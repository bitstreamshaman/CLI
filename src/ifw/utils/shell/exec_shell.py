#!/usr/bin/env python3
import os
import pty
import select
import signal
import subprocess
import sys
import termios
import tty
import threading
import time
from typing import Optional, Callable

class ShellExecutor:
    def __init__(self):
        # State persistence
        self.current_dir = os.getcwd()
        self.env_vars = os.environ.copy()
        self.shell_history = []
        
        # PTY management
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.process: Optional[subprocess.Popen] = None
        self.original_settings = None
        
        # Output capture
        self.output_buffer = []
        self.capture_output = True
        self.output_callback: Optional[Callable[[str], None]] = None
        
        # Threading for I/O handling
        self.io_thread: Optional[threading.Thread] = None
        self.stop_io = threading.Event()
        
    def set_output_callback(self, callback: Callable[[str], None]):
        """Set callback function to receive real-time output."""
        self.output_callback = callback
    
    def execute_shell_command(self, command: str) -> str:
        """Execute shell command using PTY for full terminal emulation."""
        try:
            # Store command in history
            self.shell_history.append(command)
            
            # Handle special built-in commands that need state management
            if self._handle_builtin_command(command):
                return self._get_builtin_output(command)
            
            # Execute with PTY
            return self._execute_with_pty(command)
                
        except Exception as e:
            return f"❌ Error executing command: {str(e)}"
    
    def _execute_with_pty(self, command: str) -> str:
     """Execute command using PTY with full terminal emulation."""
     try:
         # Clear output buffer
         self.output_buffer.clear()
         self.stop_io.clear()
         
         # Save terminal settings
         if sys.stdin.isatty():
             self.original_settings = termios.tcgetattr(sys.stdin.fileno())
         
         # Create PTY pair
         self.master_fd, self.slave_fd = pty.openpty()
         
         # Get user's shell
         user_shell = os.environ.get('SHELL', '/bin/bash')
         
         # Build command that explicitly sources config files and then runs the command
         if 'bash' in user_shell:
             # For bash, source .bashrc if it exists
             wrapped_command = f"[ -f ~/.bashrc ] && source ~/.bashrc; {command}"
         elif 'zsh' in user_shell:
             # For zsh, source .zshrc if it exists
             wrapped_command = f"[ -f ~/.zshrc ] && source ~/.zshrc; {command}"
         else:
             # For other shells, just use the command as-is
             wrapped_command = command
         
         # Create the process with PTY - use interactive mode to load aliases
         self.process = subprocess.Popen(
             [user_shell, '-i', '-c', wrapped_command],
             stdin=self.slave_fd,
             stdout=self.slave_fd,
             stderr=self.slave_fd,
             cwd=self.current_dir,
             env=self.env_vars,
             preexec_fn=os.setsid if os.name != 'nt' else None
         )
         
         # Close slave end in parent process
         os.close(self.slave_fd)
         self.slave_fd = None
         
         # Set terminal to raw mode if we're in a TTY
         if sys.stdin.isatty():
             tty.setraw(sys.stdin.fileno())
         
         # Start I/O handling thread
         self.io_thread = threading.Thread(target=self._handle_pty_io, daemon=True)
         self.io_thread.start()
         
         # Wait for process completion
         exit_code = self.process.wait()
         
         # Stop I/O thread
         self.stop_io.set()
         if self.io_thread:
             self.io_thread.join(timeout=1.0)
         
         # Update directory state (try to detect if it changed)
         self._update_directory_state()
         
         # Get the captured output for conversation history
         captured_output = ''.join(self.output_buffer).strip()
         
         # Return the captured output for conversation history
         if exit_code == 0:
             return captured_output  # Return actual output instead of empty string
         else:
             error_msg = f"❌ Command exited with code {exit_code}"
             if captured_output:
                 return f"{captured_output}\n{error_msg}"
             else:
                 return error_msg
             
     except KeyboardInterrupt:
         self._cleanup_pty()
         return "🛑 Command interrupted"
     except Exception as e:
         self._cleanup_pty()
         return f"❌ Error executing command: {str(e)}"
     finally:
        self._cleanup_pty()
    
    def _handle_pty_io(self):
        """Handle bidirectional I/O between terminal and process."""
        try:
            while not self.stop_io.is_set() and self.process and self.process.poll() is None:
                # Check for available input/output with timeout
                ready_fds = []
                try:
                    if sys.stdin.isatty():
                        ready_fds, _, _ = select.select([sys.stdin, self.master_fd], [], [], 0.1)
                    else:
                        # Non-interactive mode - only read from process
                        ready_fds, _, _ = select.select([self.master_fd], [], [], 0.1)
                except (OSError, ValueError):
                    break
                
                for fd in ready_fds:
                    try:
                        if fd == sys.stdin and sys.stdin.isatty():
                            # Read from terminal and send to process
                            data = os.read(sys.stdin.fileno(), 1024)
                            if data and self.master_fd:
                                os.write(self.master_fd, data)
                        
                        elif fd == self.master_fd:
                            # Read from process and send to terminal/capture
                            data = os.read(self.master_fd, 1024)
                            if data:
                                # Decode and capture output
                                try:
                                    text = data.decode('utf-8', errors='replace')
                                    if self.capture_output:
                                        self.output_buffer.append(text)
                                    
                                    # Send to terminal if in TTY mode
                                    if sys.stdout.isatty():
                                        os.write(sys.stdout.fileno(), data)
                                        sys.stdout.flush()
                                    
                                    # Call output callback if set
                                    if self.output_callback:
                                        self.output_callback(text)
                                        
                                except UnicodeDecodeError:
                                    # Handle binary data
                                    if sys.stdout.isatty():
                                        os.write(sys.stdout.fileno(), data)
                                        sys.stdout.flush()
                            else:
                                # EOF from process
                                break
                                
                    except (OSError, ValueError):
                        # Handle broken pipe or closed file descriptor
                        break
                        
        except Exception as e:
            # Log error but don't crash
            pass
    
    def _cleanup_pty(self):
        """Clean up PTY resources and restore terminal settings."""
        try:
            # Stop I/O thread
            self.stop_io.set()
            
            # Restore terminal settings
            if self.original_settings and sys.stdin.isatty():
                try:
                    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_settings)
                except:
                    pass
            
            # Close file descriptors
            if self.master_fd:
                try:
                    os.close(self.master_fd)
                except:
                    pass
                self.master_fd = None
                
            if self.slave_fd:
                try:
                    os.close(self.slave_fd)
                except:
                    pass
                self.slave_fd = None
            
            # Clean up process
            if self.process:
                try:
                    if self.process.poll() is None:
                        # Try graceful termination first
                        os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                        time.sleep(0.1)
                        if self.process.poll() is None:
                            # Force kill if still running
                            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except:
                    pass
                self.process = None
                
        except Exception:
            pass
    
    def _update_directory_state(self):
        """Try to detect if the working directory changed during command execution."""
        try:
            # This is a best-effort attempt - PTY commands might change directory
            # We can try to detect this by running 'pwd' in a separate process
            result = subprocess.run(
                ['pwd'], 
                cwd=self.current_dir, 
                capture_output=True, 
                text=True,
                env=self.env_vars
            )
            if result.returncode == 0:
                detected_dir = result.stdout.strip()
                if detected_dir and os.path.isdir(detected_dir):
                    self.current_dir = detected_dir
        except:
            # If detection fails, keep current directory
            pass
    
    def _handle_builtin_command(self, command: str) -> bool:
        """Handle commands that need special state management."""
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return False
            
        # Only handle commands that truly need state persistence
        builtin_commands = ['cd', 'pwd', 'export', 'unset']
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
                return ""
                
        except Exception as e:
            return f"❌ Error in builtin command: {str(e)}"
    
    def _handle_cd_command(self, cmd_parts: list) -> str:
        """Handle cd command with proper state update."""
        if len(cmd_parts) == 1:
            new_dir = os.path.expanduser("~")
        else:
            target = cmd_parts[1]
            
            if target == '-':
                if hasattr(self, 'previous_dir'):
                    new_dir = self.previous_dir
                else:
                    return "❌ No previous directory"
            elif target.startswith('~'):
                new_dir = os.path.expanduser(target)
            elif os.path.isabs(target):
                new_dir = target
            else:
                new_dir = os.path.join(self.current_dir, target)
        
        try:
            resolved_path = os.path.abspath(new_dir)
            if os.path.isdir(resolved_path):
                self.previous_dir = self.current_dir
                self.current_dir = resolved_path
                return ""
            else:
                return f"❌ cd: no such file or directory: {cmd_parts[1] if len(cmd_parts) > 1 else '~'}"
        except Exception as e:
            return f"❌ cd: {str(e)}"
    
    def _handle_export_command(self, cmd_parts: list) -> str:
        """Handle export command to set environment variables."""
        if len(cmd_parts) < 2:
            return "\n".join([f"{k}={v}" for k, v in self.env_vars.items() if not k.startswith('_')])
        
        for assignment in cmd_parts[1:]:
            if '=' in assignment:
                key, value = assignment.split('=', 1)
                self.env_vars[key] = value
            else:
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
    
    def interrupt_current_command(self):
        """Interrupt currently running command."""
        try:
            if self.process and self.process.poll() is None:
                # Send SIGINT to process group
                os.killpg(os.getpgid(self.process.pid), signal.SIGINT)
                return True
        except:
            pass
        return False
    
    def get_current_directory(self) -> str:
        """Get the current working directory."""
        return self.current_dir
    
    def get_shell_history(self) -> list:
        """Get the shell command history."""
        return self.shell_history.copy()
    
    def get_last_output(self) -> str:
        """Get the captured output from the last command."""
        return ''.join(self.output_buffer)
    
    def reset_state(self):
        """Reset shell state to initial values."""
        self.current_dir = os.getcwd()
        self.env_vars = os.environ.copy()
        self.shell_history = []
        self.output_buffer = []