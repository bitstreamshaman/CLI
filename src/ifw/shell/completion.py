import subprocess
import os
import shlex
import time
import threading
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple, TypeVar, Generic
from dataclasses import dataclass, field
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
import re
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from thefuzz import fuzz


T = TypeVar('T')


@dataclass
class CompletionContext:
    """Rich context information for completion providers."""
    raw_text: str
    cursor_pos: int
    tokens: List[str]
    current_token: str
    command: Optional[str]
    subcommand_chain: List[str]
    current_directory: str
    environment: Dict[str, str]
    shell_state: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_text(cls, text: str, cursor_pos: int = None, shell_executor=None):
        cursor_pos = cursor_pos or len(text)
        
        # Use proper shell parsing with error handling
        try:
            tokens = shlex.split(text[:cursor_pos])
        except ValueError:
            # Handle incomplete quotes/escapes
            try:
                tokens = shlex.split(text[:cursor_pos] + '"')
            except ValueError:
                tokens = text[:cursor_pos].split()
        
        current_token = cls._get_current_token(text, cursor_pos)
        command = tokens[0] if tokens else None
        
        # Get current directory
        current_dir = '.'
        if shell_executor and hasattr(shell_executor, 'get_current_directory'):
            try:
                current_dir = shell_executor.get_current_directory()
            except:
                pass
        
        return cls(
            raw_text=text,
            cursor_pos=cursor_pos,
            tokens=tokens,
            current_token=current_token,
            command=command,
            subcommand_chain=cls._parse_subcommands(tokens),
            current_directory=current_dir,
            environment=dict(os.environ)
        )
    
    @staticmethod
    def _get_current_token(text: str, cursor_pos: int) -> str:
        """Extract the token currently being completed."""
        before_cursor = text[:cursor_pos]
        if before_cursor.endswith(' '):
            return ''
        
        words = before_cursor.split()
        return words[-1] if words else ''
    
    @staticmethod
    def _parse_subcommands(tokens: List[str]) -> List[str]:
        """Extract subcommand chain for complex commands."""
        if not tokens:
            return []
        
        # For commands like 'git commit --message', extract ['git', 'commit']
        subcommands = [tokens[0]]
        for token in tokens[1:]:
            if not token.startswith('-'):
                subcommands.append(token)
            else:
                break
        return subcommands
    
    def is_flag_context(self) -> bool:
        return self.current_token.startswith('-')
    
    def is_file_context(self) -> bool:
        file_commands = {
            'cat', 'less', 'more', 'head', 'tail', 'grep', 'find', 'ls', 'cd',
            'cp', 'mv', 'rm', 'chmod', 'chown', 'ln', 'file', 'stat',
            'vim', 'nano', 'emacs', 'code', 'subl', 'touch', 'mkdir',
            'tar', 'gzip', 'gunzip', 'zip', 'unzip', 'open', 'hexdump'
        }
        return self.command in file_commands or self._has_file_flag()
    
    def _has_file_flag(self) -> bool:
        """Check if current context suggests file completion."""
        file_flags = {'-f', '--file', '-o', '--output', '-i', '--input'}
        return any(token in file_flags for token in self.tokens)


class TTLCache(Generic[T]):
    """Time-To-Live cache with automatic expiration."""
    
    def __init__(self, default_ttl: float = 300):
        self._cache: Dict[str, Tuple[T, float]] = {}
        self._default_ttl = default_ttl
        self._last_cleanup = time.time()
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[T]:
        with self._lock:
            self._maybe_cleanup()
            if key in self._cache:
                value, expires = self._cache[key]
                if time.time() < expires:
                    return value
                else:
                    del self._cache[key]
        return None
    
    def set(self, key: str, value: T, ttl: Optional[float] = None):
        with self._lock:
            ttl = ttl or self._default_ttl
            self._cache[key] = (value, time.time() + ttl)
    
    def _maybe_cleanup(self):
        """Periodic cleanup of expired entries."""
        now = time.time()
        if now - self._last_cleanup > 60:  # Cleanup every minute
            expired_keys = [
                key for key, (_, expires) in self._cache.items()
                if now >= expires
            ]
            for key in expired_keys:
                del self._cache[key]
            self._last_cleanup = now


class CompletionProvider(ABC):
    """Abstract base for completion providers."""
    
    @abstractmethod
    def get_completions(self, context: CompletionContext) -> List[Completion]:
        pass
    
    @property
    def priority(self) -> int:
        """Higher priority providers are consulted first."""
        return 0


class NativeShellProvider(CompletionProvider):
    """Uses native shell completion via subprocess."""
    
    def __init__(self):
        self._cache = TTLCache[List[str]](default_ttl=60)
    
    @property
    def priority(self) -> int:
        return 95  # Lower priority than path completion for file contexts
    
    def get_completions(self, context: CompletionContext) -> List[Completion]:
        if not context.command:
            return []
        
        # Check cache first
        cache_key = f"native:{context.raw_text}"
        cached = self._cache.get(cache_key)
        if cached:
            return [
                Completion(comp, start_position=-len(context.current_token))
                for comp in cached
                if comp.startswith(context.current_token)
            ]
        
        # Get completions from shell
        try:
            completions = self._get_bash_completions(context.raw_text)
            self._cache.set(cache_key, completions)
            
            return [
                Completion(comp, start_position=-len(context.current_token))
                for comp in completions
                if comp.startswith(context.current_token)
            ]
        except Exception:
            return []
    
    def _get_bash_completions(self, text: str) -> List[str]:
        """Get completions using bash's completion system."""
        try:
            words = text.split()
            if not words:
                return []
            
            command = words[0]
            current_word = words[-1] if text and not text.endswith(' ') else ''
            
            # For the first word, complete commands only
            if len(words) == 1 and not text.endswith(' '):
                bash_script = f'''
                compgen -c -- {shlex.quote(current_word)} 2>/dev/null | grep -v '^[{{}}!]' | head -20
                '''
            else:
                # For arguments, try programmable completion first, then file completion
                escaped_text = shlex.quote(text)
                escaped_word = shlex.quote(current_word)
                
                bash_script = f'''
                set +H
                source /etc/bash_completion 2>/dev/null || true
                source ~/.bash_completion 2>/dev/null || true
                
                # Set up completion variables
                COMP_LINE={escaped_text}
                COMP_POINT={len(text)}
                COMP_WORDS=({text})
                COMP_CWORD=$(($(echo {escaped_text} | wc -w) - 1))
                
                # Try programmable completion first
                _completion_func=$(complete -p {shlex.quote(command)} 2>/dev/null | sed 's/.*-F //' | awk '{{print $1}}')
                if [ -n "$_completion_func" ] && type "$_completion_func" >/dev/null 2>&1; then
                    $_completion_func {shlex.quote(command)} {escaped_word} {shlex.quote(words[-2] if len(words) > 1 else '')}
                    printf "%s\\n" "${{COMPREPLY[@]}}"
                else
                    # Fallback to file completion
                    compgen -f -- {escaped_word} 2>/dev/null
                fi | head -20
                '''
            
            result = subprocess.run(
                ['bash', '-c', bash_script],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            if result.returncode == 0:
                completions = [
                    line.strip() for line in result.stdout.splitlines() 
                    if line.strip() and not line.strip().startswith('{') and not line.strip() in ['!', 'if', 'for', 'while', 'case', 'function']
                ]
                return completions[:20]
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return []


class PathCompletionProvider(CompletionProvider):
    """Provides file and directory path completions."""
    
    def __init__(self):
        self._cache = TTLCache[List[Completion]](default_ttl=30)  # Short TTL for file changes
    
    @property
    def priority(self) -> int:
        return 100  # Highest priority for file contexts to ensure directory indicators
    
    def get_completions(self, context: CompletionContext) -> List[Completion]:
        # Always provide path completions if there's a '/' or if it's a file context
        if not context.is_file_context() and not ('/' in context.current_token) and context.current_token:
            return []
        
        return self._get_path_completions(context)
    
    def _get_path_completions(self, context: CompletionContext) -> List[Completion]:
        current_word = context.current_token
        
        # Determine search directory and prefix
        if '/' in current_word:
            directory = os.path.dirname(current_word)
            prefix = os.path.basename(current_word)
            if directory.startswith('/'):
                base_dir = directory
            else:
                base_dir = os.path.join(context.current_directory, directory)
        else:
            directory = ''
            prefix = current_word
            base_dir = context.current_directory
        
        # Expand user directory
        base_dir = os.path.expanduser(base_dir)
        
        # Cache key includes directory and prefix
        cache_key = f"path:{base_dir}:{prefix}"
        cached = self._cache.get(cache_key)
        if cached:
            return cached
        
        completions = []
        try:
            if os.path.isdir(base_dir):
                entries = os.listdir(base_dir)
                matches = [entry for entry in entries if entry.startswith(prefix)]
                
                for match in sorted(matches)[:30]:  # Limit results
                    full_path = os.path.join(directory, match) if directory else match
                    actual_path = os.path.join(base_dir, match)
                    
                    # Add trailing slash for directories
                    display_path = full_path
                    if os.path.isdir(actual_path):
                        display_path += '/'
                    
                    completion = Completion(
                        display_path,
                        start_position=-len(current_word),
                        display=display_path
                    )
                    completions.append(completion)
        
        except (PermissionError, OSError):
            pass
        
        self._cache.set(cache_key, completions)
        return completions


class CommandProvider(CompletionProvider):
    """Provides command name completions from PATH."""
    
    def __init__(self):
        self._cache = TTLCache[List[str]](default_ttl=3600)  # Commands change rarely
    
    @property
    def priority(self) -> int:
        return 60
    
    def get_completions(self, context: CompletionContext) -> List[Completion]:
        # Only complete command names
        if len(context.tokens) > 1 or context.raw_text.endswith(' '):
            return []
        
        current_word = context.current_token
        if not current_word:
            return []
        
        # Get commands from cache or PATH
        commands = self._cache.get('path_commands')
        if commands is None:
            commands = self._get_commands_from_path()
            self._cache.set('path_commands', commands)
        
        # Filter and create completions
        matches = [cmd for cmd in commands if cmd.startswith(current_word)]
        return [
            Completion(match, start_position=-len(current_word))
            for match in sorted(matches)[:50]
        ]
    
    def _get_commands_from_path(self) -> List[str]:
        """Get all executable commands from PATH."""
        commands = set()
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        
        for directory in path_dirs:
            if os.path.isdir(directory):
                try:
                    for filename in os.listdir(directory):
                        filepath = os.path.join(directory, filename)
                        if (os.path.isfile(filepath) and 
                            os.access(filepath, os.X_OK) and
                            not filename.startswith('.')):
                            commands.add(filename)
                except (PermissionError, OSError):
                    continue
        
        return list(commands)


class HelpBasedProvider(CompletionProvider):
    """Provides completions based on command help output."""
    
    def __init__(self):
        self._cache = TTLCache[List[str]](default_ttl=86400)  # Help is very stable
    
    @property
    def priority(self) -> int:
        return 40
    
    def get_completions(self, context: CompletionContext) -> List[Completion]:
        if not context.command or len(context.tokens) < 2:
            return []
        
        # Only complete flags/options
        if not context.current_token.startswith('-'):
            return []
        
        cache_key = f"help:{context.command}"
        options = self._cache.get(cache_key)
        
        if options is None:
            try:
                options = self._parse_command_help(context.command)
                self._cache.set(cache_key, options)
            except Exception:
                return []
        
        # Filter options that match current token
        matches = [opt for opt in options if opt.startswith(context.current_token)]
        return [
            Completion(match, start_position=-len(context.current_token))
            for match in matches[:20]
        ]
    
    def _parse_command_help(self, command: str) -> List[str]:
        """Extract options from command help."""
        options = set()
        
        for help_flag in ['--help', '-h']:
            try:
                result = subprocess.run(
                    [command, help_flag],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0 or result.stderr:
                    help_text = result.stdout + result.stderr
                    options.update(self._extract_options_from_help(help_text))
                    if options:
                        break
            except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                continue
        
        return sorted(list(options))
    
    def _extract_options_from_help(self, help_text: str) -> set:
        """Extract option flags from help text using regex."""
        options = set()
        
        # Patterns for different option formats
        patterns = [
            r'^\s*(-[a-zA-Z])\b',                    # Short options like -h
            r'^\s*(--[a-zA-Z][a-zA-Z0-9-]*)',       # Long options like --help
            r'\s(-[a-zA-Z])\s',                     # Inline short options
            r'\s(--[a-zA-Z][a-zA-Z0-9-]*)\s',      # Inline long options
        ]
        
        for line in help_text.split('\n'):
            for pattern in patterns:
                matches = re.findall(pattern, line)
                options.update(matches)
        
        # Filter out common false positives
        return {opt for opt in options if len(opt) > 1 and not opt.endswith('--')}


class CompletionRanker:
    """Ranks and scores completions for better user experience."""
    
    def rank_completions(self, completions: List[Completion], context: CompletionContext) -> List[Completion]:
        if not completions:
            return completions
        
        scored = []
        for comp in completions:
            score = self._calculate_score(comp, context)
            scored.append((score, comp))
        
        # Sort by score (descending) and return completions
        scored.sort(key=lambda x: x[0], reverse=True)
        return [comp for _, comp in scored]
    
    def _calculate_score(self, completion: Completion, context: CompletionContext) -> float:
        score = 0.0
        comp_text = completion.text
        current = context.current_token
        
        # Exact prefix match gets highest score
        if comp_text.startswith(current):
            score += 100
        
        # Fuzzy matching for partial matches
        if current:
            try:
                fuzzy_score = fuzz.ratio(comp_text.lower(), current.lower())
                score += fuzzy_score * 0.5
            except:
                # Fallback if fuzz fails
                pass
        
        # Shorter completions are generally preferred
        score += max(0, 50 - len(comp_text))
        
        # Boost common commands
        common_commands = {'ls', 'cd', 'git', 'docker', 'python', 'npm', 'cat', 'grep'}
        if comp_text in common_commands:
            score += 20
        
        return score


class DynamicShellCompleter(Completer):
    """Modern shell completer with multiple providers."""
    
    def __init__(self, shell_executor=None):
        self.shell_executor = shell_executor
        self.providers = [
            NativeShellProvider(),
            PathCompletionProvider(),
            CommandProvider(),
            HelpBasedProvider(),
        ]
        self.ranker = CompletionRanker()
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        # Sort providers by priority
        self.providers.sort(key=lambda p: p.priority, reverse=True)
    
    def get_completions(self, document: Document, complete_event):
        """Main completion method."""
        text = document.text_before_cursor
        
        if not text.strip():
            return
        
        try:
            completions = self._get_completions_sync(text)
            yield from completions
        except Exception:
            # Fallback to basic completion on error
            yield from self._fallback_completions(text)
    
    def _get_completions_sync(self, text: str) -> List[Completion]:
        """Synchronous completion logic with threading for I/O."""
        context = CompletionContext.from_text(text, shell_executor=self.shell_executor)
        
        all_completions = []
        
        # Use threading for providers to allow concurrent execution with timeout
        futures = []
        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            for provider in self.providers:
                future = executor.submit(self._safe_get_completions, provider, context)
                futures.append((provider, future))
            
            # Collect results with timeout, prioritizing high-priority providers
            for provider, future in futures:
                try:
                    completions = future.result(timeout=0.5)
                    if completions:
                        all_completions.extend(completions)
                        
                        # For file contexts, if PathCompletionProvider returns results, prefer those
                        if (context.is_file_context() and 
                            provider.__class__.__name__ == 'PathCompletionProvider' and 
                            completions):
                            # Cancel remaining futures and use path completions
                            for _, remaining_future in futures:
                                remaining_future.cancel()
                            break
                        
                        # If high-priority provider returns results for non-file contexts
                        if provider.priority > 95 and not context.is_file_context():
                            break
                        
                except Exception:
                    continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_completions = []
        for comp in all_completions:
            if comp.text not in seen:
                seen.add(comp.text)
                unique_completions.append(comp)
        
        # Rank and return top completions
        ranked = self.ranker.rank_completions(unique_completions, context)
        return ranked[:50]  # Limit to prevent UI overload
    
    def _safe_get_completions(self, provider: CompletionProvider, context: CompletionContext) -> List[Completion]:
        """Safely get completions from a provider."""
        try:
            return provider.get_completions(context)
        except Exception:
            return []
    
    def _fallback_completions(self, text: str):
        """Simple fallback completions if main logic fails."""
        words = text.split()
        if len(words) == 1 and not text.endswith(' '):
            # Basic command completion
            current = words[0]
            common_commands = ['ls', 'cd', 'git', 'docker', 'python', 'cat', 'grep', 'find']
            for cmd in common_commands:
                if cmd.startswith(current):
                    yield Completion(cmd, start_position=-len(current))


class SmartCompleter(Completer):
    """Backward-compatible smart completer interface."""
    
    def __init__(self, shell_executor=None):
        self.shell_completer = DynamicShellCompleter(shell_executor)
        self.control_commands = {'clear', 'exit', 'reset', 'history'}
    
    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor.strip()
        
        if not text:
            return
        
        # Handle control commands
        if len(text.split()) == 1 and not text.endswith(' '):
            for cmd in self.control_commands:
                if cmd.startswith(text):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display=f"{cmd} (control)"
                    )
        
        # Delegate to main completer
        yield from self.shell_completer.get_completions(document, complete_event)