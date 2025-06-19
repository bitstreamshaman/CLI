#!/usr/bin/env python3

import os
import shlex
import subprocess
from pathlib import Path
from typing import List
import re


class ShellCommandDetector:
    def __init__(self):
        self.available_commands = set()
        self.load_commands()

    def load_commands(self) -> None:
        """Load all available shell commands."""
        # Get commands from PATH
        path_env = os.environ.get("PATH", "")
        if path_env:
            for directory in path_env.split(os.pathsep):
                self._load_commands_from_directory(directory)

        # Load aliases
        self._load_user_aliases()

    def _load_commands_from_directory(self, directory: str) -> None:
        """Load commands from a specific directory."""
        try:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                return

            for item in dir_path.iterdir():
                if item.is_file() and os.access(item, os.X_OK):
                    self.available_commands.add(item.name)

        except (PermissionError, OSError):
            pass

    def _load_user_aliases(self) -> None:
        """Load user-defined aliases."""
        try:
            user_shell = os.environ.get("SHELL", "/bin/bash")
            result = subprocess.run(
                [user_shell, "-i", "-c", "alias"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=3,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.strip() and "=" in line:
                        alias_match = re.match(r"alias\s+([^=]+)=", line)
                        if alias_match:
                            alias_name = alias_match.group(1).strip()
                            self.available_commands.add(alias_name)
        except Exception:
            pass

    def _is_obvious_natural_language(self, text: str) -> bool:
        """Quick check for obvious natural language patterns."""
        text_lower = text.lower().strip()

        # Questions are almost always natural language
        if text_lower.endswith("?"):
            return True

        # Starts with question words
        if text_lower.startswith(("what ", "how ", "why ", "when ", "where ", "who ")):
            return True

        # Common conversational starters
        if text_lower.startswith(("tell me", "can you", "please ", "i want", "i need")):
            return True

        return False

    def _is_valid_command(self, command: str) -> bool:
        """Check if the first token is a valid command."""
        # Built-in shell commands and operators
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
        }

        # Check builtins first
        if command in builtins:
            return True

        # Check if it's in our loaded commands
        if command in self.available_commands:
            return True

        # Check paths
        if command.startswith("./") or command.startswith("/") or "/" in command:
            return True

        # Runtime check for commands we might have missed
        return self._command_exists_runtime(command)

    def _command_exists_runtime(self, command: str) -> bool:
        """Check if command exists at runtime."""
        try:
            result = subprocess.run(
                ["which", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=2,
            )
            if result.returncode == 0:
                self.available_commands.add(command)  # Cache it
                return True
        except Exception:
            pass
        return False

    def is_shell_command(self, user_input: str) -> bool:
        """
        Determine if input is a shell command using linguistic analysis.

        Core principle: Shell commands follow specific structural patterns
        that are fundamentally different from natural language.
        """
        if not user_input.strip():
            return False

        # Quick pre-checks for obvious cases
        if self._is_obvious_natural_language(user_input):
            return False

        try:
            # Check if it's valid shell syntax first
            tokens = shlex.split(user_input)
            if not tokens:
                return False

            command = tokens[0]
            args = tokens[1:] if len(tokens) > 1 else []

            # 1. Must be a valid command
            if not self._is_valid_command(command):
                return False

            # 2. For quoted arguments, be more lenient - they can contain any text
            # But for unquoted args, they must follow shell patterns
            return self._args_follow_shell_patterns_lenient(user_input, args)

        except ValueError:
            # Invalid shell syntax = not a command
            return False

    def _args_follow_shell_patterns_lenient(
        self, original_input: str, parsed_args: List[str]
    ) -> bool:
        """
        More lenient argument checking that considers quoted vs unquoted content.
        """
        if not parsed_args:
            return True

        # If the original input contains quotes, be more lenient
        # because quoted content can be anything
        has_quotes = "'" in original_input or '"' in original_input

        if has_quotes:
            # For inputs with quotes, only check unquoted portions
            # Extract unquoted parts by looking at the original input
            unquoted_parts = self._extract_unquoted_parts(original_input)
            if not unquoted_parts.strip():
                return True  # All content was quoted

            # Only analyze the unquoted parts
            return self._check_natural_language_patterns(unquoted_parts)
        else:
            # No quotes, analyze all arguments normally
            combined_args = " ".join(parsed_args)
            return self._check_natural_language_patterns(combined_args)

    def _extract_unquoted_parts(self, text: str) -> str:
        """Extract only the unquoted parts of the text for analysis."""
        result = []
        in_quote = False
        quote_char = None

        for char in text:
            if not in_quote and char in ["'", '"']:
                in_quote = True
                quote_char = char
            elif in_quote and char == quote_char:
                in_quote = False
                quote_char = None
            elif not in_quote:
                result.append(char)

        # Remove the command part (first word)
        unquoted_text = "".join(result).strip()
        words = unquoted_text.split()
        if words:
            return " ".join(words[1:])  # Skip first word (command)
        return ""

    def _check_natural_language_patterns(self, text: str) -> bool:
        """Check if text contains natural language patterns. Returns True if it's shell-like."""
        if not text.strip():
            return True

        text_lower = text.lower()

        # Strong indicators of natural language
        natural_indicators = [
            # Comparative language
            r"\b(better|worse|best|worst)\s+(than|of)\b",
            r"\bcompared?\s+to\b",
            r"\bvs\b|\bversus\b",
            # Possessive and descriptive patterns - VERY strong indicators
            r"\bmy\s+(favorite|preferred|personal)\b",
            r"\bis\s+my\s+(favorite|preferred)\b",
            r"\bcan\s+(locate|find|search|help|assist|manage|handle|create|remove|display|show)\b",
            r"\b(helps?|assists?)\s+(navigate|with|you|me|us)\b",
            r"\b(removes?|creates?|displays?|shows?|handles?|manages?|serves?|provides?)\s+\w+\s+(files|content|requests|sessions|tasks|operations|devices|connections|rules)\b",
            # Question patterns
            r"\bis\s+(the|this|that|a|an)\b",
            r"\bare\s+(the|these|those)\b",
            r"\bwhich\s+(one|is|are)\b",
            # Conversational patterns
            r"\b(can|could|should|would)\s+you\b",
            r"\bplease\s+(help|tell|show)\b",
            r"\btell\s+me\s+about\b",
            r"\bhelp\s+me\s+(with|understand)\b",
            # Articles + descriptive words with specific nouns
            r"\bthe\s+(latest|newest|oldest|current|main|primary|best|file|directory|process|version|service|system|program)\b",
            r"\ba\s+(new|good|bad|better|simple|useful)\b",
            r"\ban\s+(old|new|existing)\b",
            # Explanatory language
            r"\bhow\s+(to|do|does)\b",
            r"\bwhat\s+(is|are|does)\b",
            r"\bwhy\s+(is|are|does)\b",
            # Natural language instruction patterns
            r"\bthis\s+(command|file|directory|is)\b",
            r"\bthat\s+(command|file|directory)\b",
            r"\ball\s+\w+\s+(files|directories|commands|in)\b",
            r"\bsome\s+\w+\s+(files|directories)\b",
            r"\bevery\s+\w+\s+file\b",
            # Prepositions indicating natural language flow
            r"\bof\s+(my|the|this|that)\b",
            r"\bwith\s+(someone|the|my)\b",
            r"\bto\s+(the|my|someone)\b",
            r"\bin\s+(directory|the|my)\b",
            r"\bfrom\s+(the|my|web|disk)\b",
            r"\bbetween\s+(systems|files|the)\b",
            # Verb patterns with adverbs (very characteristic of natural language)
            r"\b(efficiently|properly|correctly|nicely|beautifully|permanently|gracefully|temporarily|securely|safely|professionally|regularly|accurately|reliably|clearly)\b",
            # Natural language time/manner expressions
            r"\bunexpectedly\s+(yesterday|today|recently)\b",
            r"\bsince\s+the\s+(last|recent)\b",
            r"\bneed\s+(to\s+be|upgrading|updating)\b",
            # Multi-word natural language phrases
            r"\ball\s+(files|directories)\s+in\b",
            r"\bfiles\s+in\s+(directory|the)\b",
            r"\bsource\s+code\s+changes\b",
            r"\bfile\s+(contents|permissions)\b",
            r"\bsystem\s+(files|services|resource)\b",
            r"\bnetwork\s+(connectivity|connections)\b",
            r"\bHTTP\s+requests\s+to\b",
            r"\bmultiple\s+(files|shell)\s+(together|sessions)\b",
        ]

        # Check for natural language patterns
        for pattern in natural_indicators:
            if re.search(pattern, text_lower):
                return False  # Found natural language pattern

        # Additional heuristics
        words = text_lower.split()
        if len(words) > 2:
            # High ratio of common English words
            common_words = {
                "the",
                "is",
                "are",
                "and",
                "or",
                "but",
                "for",
                "to",
                "of",
                "in",
                "on",
                "at",
                "by",
                "with",
                "all",
            }
            common_ratio = sum(1 for word in words if word in common_words) / len(words)
            if common_ratio > 0.4:  # More than 40% common English words
                return False

        return True  # Looks like shell arguments

    def get_command_suggestions(self, partial: str) -> List[str]:
        """Get command suggestions for partial input."""
        if not partial:
            return []

        suggestions = [
            cmd for cmd in self.available_commands if cmd.startswith(partial)
        ]
        return sorted(suggestions)[:10]

