import time
import threading
from typing import List, Dict
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from .bash_completion import bash_completions


class TTLCache:
    """Simple TTL cache for completion results."""

    def __init__(self, default_ttl: float = 60):
        self._cache: Dict[str, tuple] = {}
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            if key in self._cache:
                value, expires = self._cache[key]
                if time.time() < expires:
                    return value
                else:
                    del self._cache[key]
        return None

    def set(self, key: str, value, ttl: float = None):
        with self._lock:
            ttl = ttl or self._default_ttl
            self._cache[key] = (value, time.time() + ttl)


class SmartCompleter(Completer):
    """Enhanced completer that handles both command names and bash completion."""

    def __init__(self, shell_executor=None):
        self.shell_executor = shell_executor
        self._cache = TTLCache(default_ttl=30)
        self.control_commands = {"clear", "exit", "reset", "history"}

        # Load available commands for command name completion
        self._available_commands = set()
        self._load_available_commands()

    def _load_available_commands(self):
        """Load all available commands from PATH."""
        import os
        from pathlib import Path

        # Get commands from PATH
        path_env = os.environ.get("PATH", "")
        if path_env:
            for directory in path_env.split(os.pathsep):
                try:
                    dir_path = Path(directory)
                    if dir_path.exists() and dir_path.is_dir():
                        for item in dir_path.iterdir():
                            if item.is_file() and os.access(item, os.X_OK):
                                self._available_commands.add(item.name)
                except (PermissionError, OSError):
                    continue

        # Add common built-in commands
        builtins = {
            "cd",
            "pwd",
            "echo",
            "export",
            "source",
            "alias",
            "unalias",
            "history",
            "jobs",
            "fg",
            "bg",
            "kill",
            "wait",
            "exec",
            "eval",
            "test",
            "[",
            "printf",
            "read",
            "set",
            "unset",
            "shift",
            "exit",
            "return",
            "break",
            "continue",
            "which",
            "type",
            "command",
            "builtin",
            "declare",
            "local",
            "readonly",
            "true",
            "false",
            "ls",
            "cat",
            "grep",
            "find",
            "sed",
            "awk",
        }
        self._available_commands.update(builtins)

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor

        if not text.strip():
            return

        words = text.split()

        # Determine if we're completing the first word (command name) or arguments
        if len(words) == 1 and not text.endswith(" "):
            # Completing command name
            current_word = words[0]
            yield from self._get_command_completions(current_word)
        else:
            # Completing arguments - use bash completion
            try:
                completions = self._get_bash_completions(text)
                yield from completions
            except Exception:
                # Fallback to basic completions if bash completion fails
                pass

        # Always include control commands
        if len(words) == 1 and not text.endswith(" "):
            current_word = words[0]
            for cmd in self.control_commands:
                if cmd.startswith(current_word):
                    yield Completion(
                        cmd,
                        start_position=-len(current_word),
                        display=f"{cmd} (control)",
                    )

    def _get_command_completions(self, partial_command: str) -> List[Completion]:
        """Get completions for command names."""
        completions = []

        # Check cache first
        cache_key = f"cmd:{partial_command}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # Find matching commands
        matching_commands = [
            cmd for cmd in self._available_commands if cmd.startswith(partial_command)
        ]

        # Sort by relevance (shorter commands first, then alphabetical)
        matching_commands.sort(key=lambda x: (len(x), x))

        # Convert to Completion objects
        for cmd in matching_commands[:50]:  # Limit to 50 results
            completions.append(
                Completion(cmd, start_position=-len(partial_command), display=cmd)
            )

        # Cache results
        self._cache.set(cache_key, completions)
        return completions

    def _get_bash_completions(self, text: str) -> List[Completion]:
        """Get completions using bash_completions function."""
        # Check cache first
        cache_key = f"bash:{text}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached

        # Calculate current token being completed
        if text.endswith(" "):
            current_token = ""
            begidx = len(text)
        else:
            words = text.split()
            if words:
                current_token = words[-1]
                begidx = text.rfind(current_token)
            else:
                current_token = ""
                begidx = 0

        endidx = len(text)

        try:
            # Get current directory for bash completion context
            current_dir = "."
            if self.shell_executor and hasattr(
                self.shell_executor, "get_current_directory"
            ):
                try:
                    current_dir = self.shell_executor.get_current_directory()
                except Exception:
                    pass

            # Use bash_completions function directly
            completions_set, lprefix = bash_completions(
                prefix=current_token,
                line=text,
                begidx=begidx,
                endidx=endidx,
                env={"PWD": current_dir},  # Pass current directory context
            )

            # Convert to Completion objects
            results = []
            for comp in completions_set:
                start_pos = -lprefix if lprefix > 0 else -len(current_token)
                results.append(Completion(comp, start_position=start_pos))

            # Cache results
            self._cache.set(cache_key, results)
            return results

        except Exception:
            return []
