import subprocess
import os
import shlex
from typing import List, Optional
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

class DynamicShellCompleter(Completer):
    """Dynamic completer that uses the actual shell's completion system."""
    
    def __init__(self, shell_executor=None):
        self.shell_executor = shell_executor
        self.cache = {}  # Cache completions for performance
        
    def get_completions(self, document: Document, complete_event):
        """Get completions using various dynamic methods."""
        text = document.text_before_cursor
        
        # Don't provide completions for empty input
        if not text.strip():
            return
            
        words = shlex.split(text) if text else []
        if not words:
            return
            
        # If we're completing the first word (command name)
        if len(words) == 1 and not text.endswith(' '):
            yield from self._complete_command(words[0])
        else:
            # We're completing arguments/options
            yield from self._complete_arguments(text, words)
    
    def _get_common_commands(self):
        """Get common commands from PATH."""
        commands = self._get_commands_from_path()
        for cmd in sorted(commands)[:20]:  # Limit to top 20 for performance
            yield Completion(cmd, start_position=0)
    
    def _complete_command(self, partial_command: str):
        """Complete command names from PATH."""
        commands = self._get_commands_from_path()
        matches = [cmd for cmd in commands if cmd.startswith(partial_command)]
        
        for match in sorted(matches)[:50]:  # Limit results
            yield Completion(
                match, 
                start_position=-len(partial_command),
                display=match
            )
    
    def _complete_arguments(self, full_text: str, words: List[str]):
        """Complete arguments using various strategies."""
        command = words[0]
        
        # Strategy 1: Use bash completion if available
        completions = self._get_bash_completions(full_text)
        if completions:
            current_word = words[-1] if not full_text.endswith(' ') else ''
            for completion in completions:
                if completion.startswith(current_word):
                    yield Completion(
                        completion,
                        start_position=-len(current_word)
                    )
            return
        
        # Strategy 2: File/directory completion for many commands
        if self._command_expects_files(command):
            yield from self._complete_paths(full_text, words)
        
        # Strategy 3: Command-specific help parsing
        yield from self._complete_from_help(command, full_text, words)
    
    def _get_commands_from_path(self) -> List[str]:
        """Get all available commands from PATH."""
        if 'path_commands' in self.cache:
            return self.cache['path_commands']
        
        commands = set()
        path_dirs = os.environ.get('PATH', '').split(os.pathsep)
        
        for directory in path_dirs:
            if os.path.isdir(directory):
                try:
                    for filename in os.listdir(directory):
                        filepath = os.path.join(directory, filename)
                        if os.path.isfile(filepath) and os.access(filepath, os.X_OK):
                            commands.add(filename)
                except (PermissionError, OSError):
                    continue
        
        self.cache['path_commands'] = list(commands)
        return self.cache['path_commands']
    
    def _get_bash_completions(self, text: str) -> List[str]:
        """Use bash's programmable completion system."""
        try:
            # Use bash's completion system
            bash_script = f'''
            set +H  # Disable history expansion
            source /etc/bash_completion 2>/dev/null || true
            source ~/.bash_completion 2>/dev/null || true
            
            # Set up completion environment
            COMP_LINE="{text}"
            COMP_POINT={len(text)}
            COMP_WORDS=({text})
            COMP_CWORD=$(($(echo "{text}" | wc -w) - 1))
            
            # Try to get completions
            compgen -W "$(complete -p {shlex.split(text)[0]} 2>/dev/null | sed 's/.*-W //' | sed 's/ .*//')" -- "{text.split()[-1] if text and not text.endswith(' ') else ''}" 2>/dev/null || 
            compgen -c -- "{text.split()[-1] if text and not text.endswith(' ') else ''}" 2>/dev/null
            '''
            
            result = subprocess.run(
                ['bash', '-c', bash_script],
                capture_output=True,
                text=True,
                timeout=1  # Quick timeout to avoid hanging
            )
            
            if result.returncode == 0:
                completions = [line.strip() for line in result.stdout.splitlines() if line.strip()]
                return completions[:20]  # Limit results
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return []
    
    def _complete_paths(self, full_text: str, words: List[str]):
        """Complete file and directory paths."""
        if not words:
            return
            
        # Get the current word being completed
        current_word = words[-1] if not full_text.endswith(' ') else ''
        
        # Determine the directory to search in
        if '/' in current_word:
            directory = os.path.dirname(current_word)
            prefix = os.path.basename(current_word)
            base_dir = directory if directory else '.'
        else:
            directory = ''
            prefix = current_word
            base_dir = '.'
        
        # Get current working directory from shell executor if available
        if self.shell_executor:
            try:
                base_dir = os.path.join(self.shell_executor.get_current_directory(), base_dir)
            except:
                pass
        
        try:
            if os.path.isdir(base_dir):
                entries = os.listdir(base_dir)
                matches = [entry for entry in entries if entry.startswith(prefix)]
                
                for match in sorted(matches)[:20]:  # Limit results
                    full_path = os.path.join(directory, match) if directory else match
                    display_path = full_path
                    
                    # Add trailing slash for directories
                    actual_path = os.path.join(base_dir, match)
                    if os.path.isdir(actual_path):
                        display_path += '/'
                    
                    yield Completion(
                        display_path,
                        start_position=-len(current_word),
                        display=display_path
                    )
        except (PermissionError, OSError):
            pass
    
    def _command_expects_files(self, command: str) -> bool:
        """Check if a command typically expects file arguments."""
        file_commands = {
            'cat', 'less', 'more', 'head', 'tail', 'grep', 'find', 'ls', 'cd',
            'cp', 'mv', 'rm', 'chmod', 'chown', 'ln', 'file', 'stat',
            'vim', 'nano', 'emacs', 'code', 'subl',
            'tar', 'gzip', 'gunzip', 'zip', 'unzip',
            'git', 'docker', 'python', 'node', 'go', 'java'
        }
        return command in file_commands
    
    def _complete_from_help(self, command: str, full_text: str, words: List[str]):
        """Parse command help to get options."""
        if len(words) < 2:
            return
            
        # Cache help output
        cache_key = f"help_{command}"
        if cache_key not in self.cache:
            help_options = self._parse_command_help(command)
            self.cache[cache_key] = help_options
        
        options = self.cache[cache_key]
        current_word = words[-1] if not full_text.endswith(' ') else ''
        
        # Complete options that start with current word
        for option in options:
            if option.startswith(current_word):
                yield Completion(
                    option,
                    start_position=-len(current_word),
                    display=option
                )
    
    def _parse_command_help(self, command: str) -> List[str]:
        """Parse command help output to extract options."""
        options = []
        
        try:
            # Try different help flags
            for help_flag in ['--help', '-h', 'help']:
                try:
                    result = subprocess.run(
                        [command, help_flag],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if result.returncode == 0 or result.stderr:
                        help_text = result.stdout + result.stderr
                        options = self._extract_options_from_help(help_text)
                        if options:
                            break
                except:
                    continue
                    
        except:
            pass
        
        return options[:30]  # Limit to prevent overwhelming
    
    def _extract_options_from_help(self, help_text: str) -> List[str]:
        """Extract option flags from help text."""
        import re
        options = set()
        
        # Common patterns for options in help text
        patterns = [
            r'(-[a-zA-Z])\b',           # Short options like -h
            r'(--[a-zA-Z][a-zA-Z0-9-]*)', # Long options like --help
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, help_text)
            options.update(matches)
        
        return sorted(list(options))


class SmartCompleter(Completer):
    """Intelligent completer that combines multiple strategies."""
    
    def __init__(self, shell_executor=None):
        self.shell_completer = DynamicShellCompleter(shell_executor)
        self.control_commands = {'clear', 'exit', 'reset'}
    
    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor.strip()
        
        # Don't provide any completions for empty input
        if not text:
            return
        
        # Handle control commands only if we have some input
        if len(text.split()) == 1 and not text.endswith(' '):
            # Complete control commands first
            for cmd in self.control_commands:
                if cmd.startswith(text):
                    yield Completion(
                        cmd,
                        start_position=-len(text),
                        display=f"{cmd} (control)"
                    )
        
        # Delegate to shell completer
        yield from self.shell_completer.get_completions(document, complete_event)