#!/usr/bin/env python3
import subprocess
import os
import signal
import time

class ShellExecutor:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.current_process = None
        # State persistence
        self.current_dir = os.getcwd()
        self.env_vars = os.environ.copy()
        self.shell_history = []
        
    def execute_shell_command(self, command: str) -> str:
        """Execute shell command with state persistence and return output."""
        try:
            # Store command in history
            self.shell_history.append(command)
            
            # Handle built-in commands that need state persistence
            if self._handle_builtin_command(command):
                return self._get_builtin_output(command)
            
            # Get user's shell and run in interactive mode to load aliases
            user_shell = os.environ.get('SHELL', '/bin/bash')
            
            # Build the full command with current directory context
            full_command = self._build_command_with_context(command)
            
            # Use -i (interactive) to load .bashrc/.zshrc with aliases
            # Use -c to execute the command
            process = subprocess.Popen(
                [user_shell, '-i', '-c', full_command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=self.current_dir,  # Set working directory
                env=self.env_vars,     # Use persistent environment
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            self.current_process = process
            
            try:
                # Wait for completion with timeout
                stdout, stderr = process.communicate(timeout=self.timeout)
                
                # Update state based on command output if needed
                self._update_state_from_command(command, stdout, stderr, process.returncode)
                
                # Format the output
                output = self._format_output(stdout, stderr, process.returncode)
                return output
                
            except subprocess.TimeoutExpired:
                # Kill the process group on timeout
                self._kill_process_group(process)
                return f"❌ Command timed out after {self.timeout} seconds"
                
        except Exception as e:
            return f"❌ Error executing command: {str(e)}"
        finally:
            self.current_process = None
    
    def _handle_builtin_command(self, command: str) -> bool:
        """Handle commands that need special state management."""
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return False
            
        builtin_commands = ['cd', 'pwd', 'export', 'unset', 'pushd', 'popd']
        return cmd_parts[0] in builtin_commands
    
    def _get_builtin_output(self, command: str) -> str:
        """Execute built-in commands with state persistence."""
        cmd_parts = command.strip().split()
        cmd = cmd_parts[0]
        
        try:
            if cmd == 'cd':
                return self._handle_cd_command(cmd_parts)
            elif cmd == 'pwd':
                return self.current_dir
            elif cmd == 'export':
                return self._handle_export_command(cmd_parts)
            elif cmd == 'unset':
                return self._handle_unset_command(cmd_parts)
            else:
                # For other builtins, fall back to subprocess but update state
                return ""
                
        except Exception as e:
            return f"❌ Error in builtin command: {str(e)}"
    
    def _handle_cd_command(self, cmd_parts: list) -> str:
        """Handle cd command with proper state update."""
        if len(cmd_parts) == 1:
            # cd with no arguments goes to home
            new_dir = os.path.expanduser("~")
        else:
            # cd with path argument
            target = cmd_parts[1]
            
            # Handle special cases
            if target == '-':
                # cd - (go to previous directory)
                if hasattr(self, 'previous_dir'):
                    new_dir = self.previous_dir
                else:
                    return "❌ No previous directory"
            elif target.startswith('~'):
                # Handle ~ expansion
                new_dir = os.path.expanduser(target)
            elif os.path.isabs(target):
                # Absolute path
                new_dir = target
            else:
                # Relative path
                new_dir = os.path.join(self.current_dir, target)
        
        # Resolve the path and check if it exists
        try:
            resolved_path = os.path.abspath(new_dir)
            if os.path.isdir(resolved_path):
                # Store previous directory for cd -
                self.previous_dir = self.current_dir
                self.current_dir = resolved_path
                return ""  # Success, no output
            else:
                return f"❌ cd: no such file or directory: {cmd_parts[1] if len(cmd_parts) > 1 else '~'}"
        except Exception as e:
            return f"❌ cd: {str(e)}"
    
    def _handle_export_command(self, cmd_parts: list) -> str:
        """Handle export command to set environment variables."""
        if len(cmd_parts) < 2:
            # Show all exported variables
            return "\n".join([f"{k}={v}" for k, v in self.env_vars.items() if not k.startswith('_')])
        
        for assignment in cmd_parts[1:]:
            if '=' in assignment:
                key, value = assignment.split('=', 1)
                self.env_vars[key] = value
            else:
                # Export existing variable
                if assignment in os.environ:
                    self.env_vars[assignment] = os.environ[assignment]
        
        return ""
    
    def _handle_unset_command(self, cmd_parts: list) -> str:
        """Handle unset command to remove environment variables."""
        if len(cmd_parts) < 2:
            return "❌ unset: not enough arguments"
        
        for var_name in cmd_parts[1:]:
            self.env_vars.pop(var_name, None)
        
        return ""
    
    def _build_command_with_context(self, command: str) -> str:
        """Build command with current directory context for non-builtin commands."""
        # For non-cd commands, we'll rely on cwd parameter in subprocess
        return command
    
    def _update_state_from_command(self, command: str, stdout: str, stderr: str, returncode: int):
        """Update internal state based on command execution."""
        # This method can be extended to handle other state changes
        # For example, if a command changes environment variables
        pass
    
    def _format_output(self, stdout: str, stderr: str, returncode: int) -> str:
        """Format command output for display."""
        output_parts = []
        
        # Add stdout if present
        if stdout.strip():
            output_parts.append(stdout.rstrip())
        
        # Filter out bash job control warnings from stderr
        if stderr.strip():
            stderr_lines = stderr.strip().split('\n')
            filtered_stderr = []
            
            for line in stderr_lines:
                # Skip common bash interactive mode warnings
                if any(warning in line for warning in [
                    "cannot set terminal process group",
                    "no job control in this shell",
                    "Inappropriate ioctl for device"
                ]):
                    continue
                filtered_stderr.append(line)
            
            # Only show stderr if there are actual errors (not just bash warnings)
            if filtered_stderr:
                stderr_formatted = "\n".join([f"⚠️  {line}" for line in filtered_stderr])
                output_parts.append(stderr_formatted)
        
        # Add return code info for non-zero exits
        if returncode != 0:
            output_parts.append(f"❌ Command exited with code {returncode}")
        
        # Join all parts or show success message for empty output
        if output_parts:
            return "\n".join(output_parts)
        elif returncode == 0:
            return ""  # Clean success, no extra message needed
        else:
            return f"❌ Command failed with exit code {returncode}"
    
    def _kill_process_group(self, process):
        """Kill process and its children."""
        try:
            if os.name != 'nt':
                # Unix: kill the process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                time.sleep(0.5)
                if process.poll() is None:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            else:
                # Windows: kill the process
                process.terminate()
                time.sleep(0.5)
                if process.poll() is None:
                    process.kill()
        except (OSError, ProcessLookupError):
            # Process already died
            pass
    
    def interrupt_current_command(self):
        """Interrupt currently running command (called on Ctrl+C)."""
        if self.current_process and self.current_process.poll() is None:
            try:
                self._kill_process_group(self.current_process)
                return True
            except Exception:
                return False
        return False
    
    def get_current_directory(self) -> str:
        """Get the current working directory."""
        return self.current_dir
    
    def get_shell_history(self) -> list:
        """Get the shell command history."""
        return self.shell_history.copy()
    
    def reset_state(self):
        """Reset shell state to initial values."""
        self.current_dir = os.getcwd()
        self.env_vars = os.environ.copy()
        self.shell_history = []

