"""
Session Manager for Infraware Cloud Assistant.
Manages user interaction, prompts, and session state.
"""
import getpass
import socket
from typing import Dict
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML
from rich.console import Console

# Import from existing modules
from ..shell.completion import SmartCompleter
from ..utils.exceptions import SessionError 

class SessionManager:
    """
    Manages user session state, input prompts, and interaction features.
    
    Responsibilities:
    - Enhanced terminal prompt with context
    - Command history management
    - Smart completion
    - Key bindings
    - Session context (user, directory, etc.)
    """
    
    def __init__(self, shell_executor, console: Console):
        """
        Initialize session manager.
        
        Args:
            shell_executor: Shell executor for directory context and completion
            console: Rich console for error display
        """
        self.shell_executor = shell_executor
        self.console = console
        
        # Initialize prompt_toolkit components
        self.history = InMemoryHistory()
        self.smart_completer = SmartCompleter(shell_executor)
        self.key_bindings = self._create_key_bindings()
        
        # Cache for context to avoid repeated system calls
        self._context_cache = None
        self._context_cache_valid = True
    
    def get_user_input(self) -> str:
        """
        Get user input with enhanced prompt features.
        
        Returns:
            str: User input string
            
        Raises:
            KeyboardInterrupt: When user presses Ctrl+C
            EOFError: When user presses Ctrl+D
            SessionError: On unexpected prompt errors
        """
        try:
            # Get current context for prompt
            context = self.get_context()
            
            # Create formatted prompt with user@hostname:directory format
            prompt_text = HTML(
                f'<blue><b>|>| {context["username"]}@{context["hostname"]}:{context["cwd"]} </b></blue> '
            )
            
            # Get user input with all enhanced features
            user_input = prompt(
                prompt_text,
                completer=self.smart_completer,
                history=self.history,
                complete_style=CompleteStyle.READLINE_LIKE,
                key_bindings=self.key_bindings,
                enable_history_search=True,  # Enables Ctrl+R reverse search
                complete_while_typing=False,  # Set to True for real-time completion
            )
            
            # Invalidate context cache after command (directory might change)
            self._invalidate_context_cache()
            
            return user_input
            
        except (KeyboardInterrupt, EOFError):
            # Let these bubble up to controller for policy decisions
            raise
        except Exception as e:
            # Wrap unexpected errors in SessionError
            raise SessionError(f"Failed to get user input: {e}") from e
    
    def get_context(self) -> Dict[str, str]:
        """
        Get current user and directory context for prompt display.
        
        Returns:
            Dict with username, hostname, and current working directory
        """
        # Use cache if valid to avoid repeated system calls
        if self._context_cache_valid and self._context_cache is not None:
            return self._context_cache
        
        try:
            username = getpass.getuser()
            hostname = socket.gethostname()
            cwd = self.shell_executor.get_current_directory()
            
            context = {
                "username": username,
                "hostname": hostname,
                "cwd": cwd
            }
            
            # Cache the context
            self._context_cache = context
            self._context_cache_valid = True
            
            return context
            
        except Exception as e:
            # Fallback values if system calls fail
            self.console.print(f"[yellow]Warning: Could not get system context: {e}[/yellow]")
            fallback_context = {
                "username": "user",
                "hostname": "localhost", 
                "cwd": "~"
            }
            
            # Don't cache fallback values
            return fallback_context
    
    def _create_key_bindings(self) -> KeyBindings:
        """
        Create custom key bindings for enhanced terminal experience.
        
        Returns:
            KeyBindings object with custom shortcuts
        """
        kb = KeyBindings()
        
        # Ctrl+L to clear screen
        @kb.add('c-l')
        def clear_screen(event):
            """Clear the terminal screen."""
            event.app.renderer.clear()
        
        # Future key bindings can be added here:
        # @kb.add('c-r')  # Ctrl+R for reverse search (already built-in)
        # @kb.add('c-d')  # Ctrl+D for EOF (already built-in)
        
        return kb
    
    def add_to_history(self, command: str) -> None:
        """
        Manually add a command to session history.
        
        Args:
            command: Command string to add to history
        """
        if command and command.strip():
            self.history.append_string(command.strip())
    
    def clear_history(self) -> None:
        """Clear command history."""
        self.history = InMemoryHistory()
    
    def get_history_list(self) -> list[str]:
        """
        Get list of commands from history.
        
        Returns:
            List of command strings from history
        """
        return list(self.history.get_strings())
    
    def _invalidate_context_cache(self) -> None:
        """Invalidate context cache to force refresh on next access."""
        self._context_cache_valid = False
    
    def force_context_refresh(self) -> None:
        """
        Force immediate refresh of context cache.
        
        Useful after commands that change directory or user context.
        """
        self._invalidate_context_cache()
        self.get_context()  # This will refresh the cache
    
    def get_session_info(self) -> Dict[str, any]:
        """
        Get comprehensive session information for debugging or logging.
        
        Returns:
            Dict with session state information
        """
        context = self.get_context()
        history_count = len(self.get_history_list())
        
        return {
            "context": context,
            "history_commands": history_count,
            "completer_active": self.smart_completer is not None,
            "cache_valid": self._context_cache_valid
        }
    
    def set_completion_mode(self, real_time: bool = False) -> None:
        """
        Configure completion behavior.
        
        Args:
            real_time: If True, show completions while typing
        """
        # This would require recreating the prompt session
        # For now, store the preference for next get_user_input call
        self._real_time_completion = real_time
    
