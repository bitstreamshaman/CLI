#!/usr/bin/env python3

import os
import shlex
import subprocess
from pathlib import Path
from typing import Set, List
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
            user_shell = os.environ.get('SHELL', '/bin/bash')
            result = subprocess.run(
                [user_shell, '-i', '-c', 'alias'], 
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True, 
                timeout=3
            )
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip() and '=' in line:
                        alias_match = re.match(r'alias\s+([^=]+)=', line)
                        if alias_match:
                            alias_name = alias_match.group(1).strip()
                            self.available_commands.add(alias_name)
        except:
            pass
    
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
            tokens = shlex.split(user_input)
            if not tokens:
                return False
            
            command = tokens[0]
            args = tokens[1:] if len(tokens) > 1 else []
            
            # 1. Must be a valid command
            if not self._is_valid_command(command):
                return False
            
            # 2. Arguments must follow shell patterns (not natural language)
            return self._args_follow_shell_patterns(args)
            
        except ValueError:
            # Invalid shell syntax = not a command
            return False
    
    def _is_obvious_natural_language(self, text: str) -> bool:
        """Quick check for obvious natural language patterns."""
        text_lower = text.lower().strip()
        
        # Questions are almost always natural language
        if text_lower.endswith('?'):
            return True
        
        # Starts with question words
        if text_lower.startswith(('what ', 'how ', 'why ', 'when ', 'where ', 'who ')):
            return True
        
        # Common conversational starters
        if text_lower.startswith(('tell me', 'can you', 'please ', 'i want', 'i need')):
            return True
        
        return False
    
    def _is_valid_command(self, command: str) -> bool:
        """Check if the first token is a valid command."""
        # Built-in shell commands and operators
        builtins = {
            "cd", "pwd", "echo", "export", "source", "alias", "unalias",
            "history", "jobs", "fg", "bg", "kill", "wait", "exec",
            "eval", "test", "[", "printf", "read", "set", "unset",
            "shift", "exit", "return", "break", "continue", "which",
            "type", "command", "builtin", "declare", "local", "readonly",
            "true", "false"
        }
        
        # Check builtins first
        if command in builtins:
            return True
        
        # Check if it's in our loaded commands
        if command in self.available_commands:
            return True
        
        # Check paths
        if command.startswith('./') or command.startswith('/') or '/' in command:
            return True
        
        # Runtime check for commands we might have missed
        return self._command_exists_runtime(command)
    
    def _command_exists_runtime(self, command: str) -> bool:
        """Check if command exists at runtime."""
        try:
            result = subprocess.run(
                ['which', command], 
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            if result.returncode == 0:
                self.available_commands.add(command)  # Cache it
                return True
        except:
            pass
        return False
    
    def _args_follow_shell_patterns(self, args: List[str]) -> bool:
        """
        Check if arguments follow shell command patterns rather than natural language.
        
        Shell arguments typically:
        - Are flags (-x, --flag)
        - Are file/directory paths
        - Are short values or quoted strings
        - Don't form grammatical sentences
        """
        if not args:
            return True  # No args is fine
        
        # Join all args to analyze as a whole
        combined_args = " ".join(args)
        text_lower = combined_args.lower()
        
        # Strong indicators of natural language in arguments
        natural_indicators = [
            # Comparative language
            r'\b(better|worse|best|worst)\s+(than|of)\b',
            r'\bcompared?\s+to\b',
            r'\bvs\b|\bversus\b',
            
            # Question patterns in args
            r'\bis\s+(the|this|that|a|an)\b',
            r'\bare\s+(the|these|those)\b',
            r'\bwhich\s+(one|is|are)\b',
            
            # Conversational patterns
            r'\b(can|could|should|would)\s+you\b',
            r'\bplease\s+(help|tell|show)\b',
            r'\btell\s+me\s+about\b',
            r'\bhelp\s+me\s+(with|understand)\b',
            
            # Articles + descriptive words (very rare in shell commands)
            r'\bthe\s+(latest|newest|oldest|current|main|primary|best|file|directory|process|version|service|system)\b',
            r'\ba\s+(new|good|bad|better|simple|useful)\b',
            r'\ban\s+(old|new|existing)\b',
            
            # Explanatory language
            r'\bhow\s+(to|do|does)\b',
            r'\bwhat\s+(is|are|does)\b',
            r'\bwhy\s+(is|are|does)\b',
            
            # Natural language instruction patterns
            r'\bthis\s+(command|file|directory)\b',
            r'\bthat\s+(command|file|directory)\b',
            r'\ball\s+\w+\s+(files|directories|commands)\b',
            r'\bsome\s+\w+\s+(files|directories)\b',
            r'\bevery\s+\w+\s+file\b',
            
            # Possessive and descriptive patterns
            r'\bmy\s+(project|files|system|directory)\b',
            r'\byour\s+(files|system|project)\b',
            r'\bof\s+(my|the|this|that)\b',
            r'\bwith\s+(someone|the|my)\b',
            r'\bto\s+(the|my|someone)\b',
            
            # Verb patterns that indicate natural language
            r'\b(can|will|should|might|must)\s+(search|find|run|work|help)\b',
            r'\bis\s+(running|working|installed|available|useful)\b',
            r'\bare\s+(running|working|available)\b',
            
            # Context words that appear in natural language descriptions
            r'\b(contents|special|running|installed|available|useful)\b',
        ]
        
        # Check for natural language patterns
        for pattern in natural_indicators:
            if re.search(pattern, text_lower):
                return False
        
        # Additional heuristics
        
        # Very long single arguments (unless they're file paths)
        for arg in args:
            if len(arg) > 40 and not ('/' in arg or '.' in arg or arg.startswith('-')):
                return False
        
        # Many very short words often indicate natural language
        short_words = [arg for arg in args if len(arg) <= 3 and not arg.startswith('-')]
        if len(short_words) > 3:
            return False
        
        # High ratio of common English words
        common_words = {'the', 'is', 'are', 'and', 'or', 'but', 'for', 'to', 'of', 'in', 'on', 'at', 'by', 'with'}
        word_tokens = combined_args.lower().split()
        if len(word_tokens) > 2:
            common_ratio = sum(1 for word in word_tokens if word in common_words) / len(word_tokens)
            if common_ratio > 0.4:  # More than 40% common English words
                return False
        
        return True
    
    def get_command_suggestions(self, partial: str) -> List[str]:
        """Get command suggestions for partial input."""
        if not partial:
            return []
        
        suggestions = [cmd for cmd in self.available_commands 
                      if cmd.startswith(partial)]
        return sorted(suggestions)[:10]


def main():
    detector = ShellCommandDetector()
    
    # Test cases organized by category with expected results
    test_cases = [
        # Valid shell commands - should all be True
        ("VALID COMMANDS", True, [
            "ls -la",
            "echo 'Hello World'", 
            "cd /usr/local/bin",
            "pwd",
            "rm -rf /tmp/test",
            "git commit -m 'Initial commit'",
            "python3 script.py",
            "docker ps -a",
            "kubectl get pods",
            "aws s3 ls",
            "which python",
            "test -f /etc/passwd",
            "find . -name '*.py'",
            "grep pattern file",
            "git help",
            "ls --help",
            "diff file1 file2",
            "cat /etc/passwd",
            "chmod +x script.sh",
            "sudo systemctl restart nginx",
            "ps aux | grep python",
            "curl -X POST https://api.example.com",
            "ssh user@server",
            "date +%Y-%m-%d",
            "man grep",
            "info bash", 
            "apropos search",
            "whatis ls",
            "type python",
            "command -v git",
            "grep 'what' file.txt",
            "echo 'how are you'",
            "find . -name 'why*'",
        ]),
        
        # Natural language - should all be False  
        ("NATURAL LANGUAGE", False, [
            "this is not a shell command",
            "what is the weather today?",
            "tell me a joke", 
            "which is better, GCP or AWS?",
            "test this command",
            "find all python files",
            "what does this command do?",
            "how do I use grep?",
            "help me with git",
            "show me the best practices",
            "explain the difference between",
        ]),
        
        # Tricky cases - natural language using command words (should be False)
        ("NATURAL LANGUAGE WITH COMMAND WORDS", False, [
            "copy all files to the backup directory",
            "delete that old file", 
            "install the latest version",
            "git status of my project",
            "ls all files in directory",
            "cd to the home directory",
            "rm all temporary files",
            "cp this file to that location",
            "cat the file contents",
            "echo is a useful command",
            "grep can search through files", 
            "head of the department",
            "tail of the list",
            "kill the running process",
            "date with someone special",
            "top of the mountain",
        ]),
        
        # Conversational patterns (should be False)
        ("CONVERSATIONAL", False, [
            "please run ls command",
            "can you execute pwd",
            "could you help me with find", 
            "is git installed?",
            "does python work?",
            "why is the server down?",
            "where is the config file?", 
            "how big is the directory?",
            "go to the directory",
            "open the document",
            "start the service",
            "exit the program",
        ]),
    ]
    
    print("=" * 80)
    print("SHELL COMMAND DETECTOR TEST RESULTS")
    print("=" * 80)
    
    total_tests = 0
    total_errors = 0
    
    for category, expected, test_inputs in test_cases:
        print(f"\n📁 {category} (Expected: {expected})")
        print("-" * 60)
        
        category_errors = 0
        for test_input in test_inputs:
            result = detector.is_shell_command(test_input)
            total_tests += 1
            
            if result != expected:
                status = "❌ WRONG"
                category_errors += 1
                total_errors += 1
            else:
                status = "✅ OK"
            
            print(f"{status:8} | '{test_input}' -> {result}")
        
        # Category summary
        accuracy = ((len(test_inputs) - category_errors) / len(test_inputs)) * 100
        print(f"\n📊 Category Accuracy: {accuracy:.1f}% ({len(test_inputs) - category_errors}/{len(test_inputs)})")
    
    # Overall summary
    print("\n" + "=" * 80)
    overall_accuracy = ((total_tests - total_errors) / total_tests) * 100
    print(f"🎯 OVERALL ACCURACY: {overall_accuracy:.1f}% ({total_tests - total_errors}/{total_tests})")
    print(f"❌ Total Errors: {total_errors}")
    print("=" * 80)

#if __name__ == "__main__":
#    main()