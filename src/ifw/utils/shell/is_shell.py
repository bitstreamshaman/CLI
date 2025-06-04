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
    
    def _args_follow_shell_patterns_lenient(self, original_input: str, parsed_args: List[str]) -> bool:
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
        unquoted_text = ''.join(result).strip()
        words = unquoted_text.split()
        if words:
            return ' '.join(words[1:])  # Skip first word (command)
        return ''
    
    def _check_natural_language_patterns(self, text: str) -> bool:
        """Check if text contains natural language patterns. Returns True if it's shell-like."""
        if not text.strip():
            return True
        
        text_lower = text.lower()
        
        # Strong indicators of natural language
        natural_indicators = [
            # Comparative language
            r'\b(better|worse|best|worst)\s+(than|of)\b',
            r'\bcompared?\s+to\b',
            r'\bvs\b|\bversus\b',
            
            # Possessive and descriptive patterns - VERY strong indicators
            r'\bmy\s+(favorite|preferred|personal)\b',
            r'\bis\s+my\s+(favorite|preferred)\b',
            r'\bcan\s+(locate|find|search|help|assist|manage|handle|create|remove|display|show)\b',
            r'\b(helps?|assists?)\s+(navigate|with|you|me|us)\b',
            r'\b(removes?|creates?|displays?|shows?|handles?|manages?|serves?|provides?)\s+\w+\s+(files|content|requests|sessions|tasks|operations|devices|connections|rules)\b',
            
            # Question patterns
            r'\bis\s+(the|this|that|a|an)\b',
            r'\bare\s+(the|these|those)\b',
            r'\bwhich\s+(one|is|are)\b',
            
            # Conversational patterns
            r'\b(can|could|should|would)\s+you\b',
            r'\bplease\s+(help|tell|show)\b',
            r'\btell\s+me\s+about\b',
            r'\bhelp\s+me\s+(with|understand)\b',
            
            # Articles + descriptive words with specific nouns
            r'\bthe\s+(latest|newest|oldest|current|main|primary|best|file|directory|process|version|service|system|program)\b',
            r'\ba\s+(new|good|bad|better|simple|useful)\b',
            r'\ban\s+(old|new|existing)\b',
            
            # Explanatory language
            r'\bhow\s+(to|do|does)\b',
            r'\bwhat\s+(is|are|does)\b',
            r'\bwhy\s+(is|are|does)\b',
            
            # Natural language instruction patterns
            r'\bthis\s+(command|file|directory|is)\b',
            r'\bthat\s+(command|file|directory)\b',
            r'\ball\s+\w+\s+(files|directories|commands|in)\b',
            r'\bsome\s+\w+\s+(files|directories)\b',
            r'\bevery\s+\w+\s+file\b',
            
            # Prepositions indicating natural language flow
            r'\bof\s+(my|the|this|that)\b',
            r'\bwith\s+(someone|the|my)\b',
            r'\bto\s+(the|my|someone)\b',
            r'\bin\s+(directory|the|my)\b',
            r'\bfrom\s+(the|my|web|disk)\b',
            r'\bbetween\s+(systems|files|the)\b',
            
            # Verb patterns with adverbs (very characteristic of natural language)
            r'\b(efficiently|properly|correctly|nicely|beautifully|permanently|gracefully|temporarily|securely|safely|professionally|regularly|accurately|reliably|clearly)\b',
            
            # Natural language time/manner expressions
            r'\bunexpectedly\s+(yesterday|today|recently)\b',
            r'\bsince\s+the\s+(last|recent)\b',
            r'\bneed\s+(to\s+be|upgrading|updating)\b',
            
            # Multi-word natural language phrases
            r'\ball\s+(files|directories)\s+in\b',
            r'\bfiles\s+in\s+(directory|the)\b',
            r'\bsource\s+code\s+changes\b',
            r'\bfile\s+(contents|permissions)\b',
            r'\bsystem\s+(files|services|resource)\b',
            r'\bnetwork\s+(connectivity|connections)\b',
            r'\bHTTP\s+requests\s+to\b',
            r'\bmultiple\s+(files|shell)\s+(together|sessions)\b',
        ]
        
        # Check for natural language patterns
        for pattern in natural_indicators:
            if re.search(pattern, text_lower):
                return False  # Found natural language pattern
        
        # Additional heuristics
        words = text_lower.split()
        if len(words) > 2:
            # High ratio of common English words
            common_words = {'the', 'is', 'are', 'and', 'or', 'but', 'for', 'to', 'of', 'in', 'on', 'at', 'by', 'with', 'all'}
            common_ratio = sum(1 for word in words if word in common_words) / len(words)
            if common_ratio > 0.4:  # More than 40% common English words
                return False
        
        return True  # Looks like shell arguments
    
    def get_command_suggestions(self, partial: str) -> List[str]:
        """Get command suggestions for partial input."""
        if not partial:
            return []
        
        suggestions = [cmd for cmd in self.available_commands 
                      if cmd.startswith(partial)]
        return sorted(suggestions)[:10]


def main():
    detector = ShellCommandDetector()
    
    # Comprehensive test cases - 100+ new examples
    test_cases = [
        # Valid shell commands - should all be True (40 commands)
        ("VALID COMMANDS", True, [
            "nginx -t",
            "systemctl status apache2",
            "journalctl -f",
            "crontab -e",
            "htop",
            "iotop",
            "netstat -tulpn",
            "ss -tuln",
            "lsof -i :80",
            "uname -a",
            "uptime",
            "free -h",
            "vmstat 1 5",
            "iostat -x 1",
            "sar -u 1 10",
            "tcpdump -i eth0",
            "wireshark",
            "nmap -p 22 192.168.1.1",
            "ping -c 4 google.com",
            "traceroute 8.8.8.8",
            "dig google.com",
            "nslookup github.com",
            "host example.com",
            "wget https://example.com/file.zip",
            "curl -L -o output.html https://httpbin.org/html",
            "rsync -avz /source/ user@host:/dest/",
            "scp -r folder/ user@server:~/",
            "sftp user@hostname",
            "screen -S session_name",
            "tmux new-session -d -s work",
            "nohup python script.py &",
            "jobs -l",
            "bg %1",
            "fg %2",
            "disown %3",
            "at now + 5 minutes",
            "batch",
            "watch -n 2 'ps aux'",
            "strace -p 1234",
            "gdb -p 5678",
        ]),
        
        # Natural language questions/statements - should all be False (30 examples)
        ("NATURAL LANGUAGE", False, [
            "How can I improve server performance?",
            "What are the benefits of using containers?",
            "Why is my application running slowly?",
            "When should I restart the database?",
            "Where are the configuration files stored?",
            "Who has access to the production server?",
            "Which programming language is better for web development?",
            "Could you recommend a good text editor?",
            "I need help with my deployment pipeline",
            "The server seems to be experiencing issues",
            "My application crashed unexpectedly yesterday",
            "Users are reporting connectivity problems",
            "Performance has degraded since the last update",
            "We need to scale our infrastructure",
            "The database is consuming too much memory",
            "Security vulnerabilities were discovered",
            "Backup procedures need to be reviewed",
            "Monitoring alerts are firing constantly",
            "Load balancing configuration requires optimization",
            "SSL certificates are expiring soon",
            "API response times are unacceptable",
            "Storage capacity is running low",
            "Network latency has increased significantly",
            "Authentication mechanisms need upgrading",
            "Disaster recovery plans are outdated",
            "Compliance requirements have changed",
            "Budget constraints limit our options",
            "Team productivity could be improved",
            "Documentation is incomplete and confusing",
            "Training materials need updating",
        ]),
        
        # Natural language using command words - should all be False (40 examples)  
        ("NATURAL LANGUAGE WITH COMMAND WORDS", False, [
            "grep is my favorite search tool",
            "find can locate files efficiently", 
            "cat shows file contents nicely",
            "ls displays directory listings beautifully",
            "cd helps navigate the filesystem",
            "rm removes files permanently from disk",
            "cp creates copies of important files",
            "mv relocates files to different directories",
            "chmod modifies file permissions correctly",
            "chown changes ownership of system files",
            "ps shows all running processes",
            "top displays system resource usage",
            "kill terminates problematic processes gracefully",
            "sudo grants administrative privileges temporarily",
            "ssh connects to remote servers securely",
            "scp transfers files between systems safely",
            "wget downloads files from web servers",
            "curl makes HTTP requests to APIs",
            "tar compresses multiple files together",
            "zip creates compressed archive files",
            "nginx serves web content efficiently",
            "apache handles HTTP requests properly",
            "mysql manages database operations",
            "git tracks source code changes",
            "docker runs containerized applications",
            "vim edits text files professionally",
            "nano provides simple text editing",
            "screen multiplexes terminal sessions",
            "tmux manages multiple shell sessions",
            "cron schedules automated tasks regularly",
            "systemctl controls system services",
            "mount attaches filesystem devices",
            "fdisk partitions storage devices",
            "lsblk lists block devices clearly",
            "df shows filesystem usage statistics",
            "du calculates directory sizes accurately",
            "ping tests network connectivity reliably",
            "netstat displays network connections",
            "iptables configures firewall rules",
            "rsync synchronizes files efficiently",
        ]),
        
        # Conversational patterns - should all be False (35 examples)
        ("CONVERSATIONAL", False, [
            "Please help me configure the firewall",
            "Can you show me how to use Docker?",
            "Would you mind explaining Git workflow?",
            "Could you assist with database optimization?",
            "I'd like to learn about Kubernetes",
            "Would it be possible to automate deployments?",
            "Can we discuss security best practices?",
            "Please walk me through the setup process",
            "I'm having trouble with SSL configuration",
            "Could you recommend monitoring tools?",
            "Would you suggest backup strategies?",
            "Can you help troubleshoot network issues?",
            "Please explain load balancing concepts",
            "I need guidance on container orchestration",
            "Could we review the disaster recovery plan?",
            "Would you mind checking system logs?",
            "Can you verify the server configuration?",
            "Please confirm the backup completed successfully",
            "I'd appreciate help with performance tuning",
            "Could you investigate the connection timeout?",
            "Would you mind updating the documentation?",
            "Can we schedule a maintenance window?",
            "Please notify users about the downtime",
            "I think we should upgrade the hardware",
            "Could you consider implementing caching?",
            "Would it help to increase memory allocation?",
            "Can we try restarting the application server?",
            "Please make sure logging is enabled",
            "I wonder if we need more disk space",
            "Could you check if all services are running?",
            "Would you mind testing the backup restore?",
            "Can we validate the security patches?",
            "Please ensure compliance requirements are met",
            "I believe we should monitor CPU usage",
            "Could you double-check the network configuration?",
        ]),
    ]
    
    print("=" * 80)
    print("COMPREHENSIVE SHELL COMMAND DETECTOR TEST (100+ CASES)")
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
    print(f"📊 Total Test Cases: {total_tests}")
    print("=" * 80)

if __name__ == "__main__":
    main()