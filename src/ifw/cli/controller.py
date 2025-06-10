"""
Main CLI Controller for Infraware Cloud Assistant.
Orchestrates the CLI flow and manages the main interaction loop.
"""
from typing import Optional
from rich.console import Console

# Import CLI components
from .session_manager import SessionManager
from .command_processor import CommandProcessor, CommandProcessingError, NoHandlerFoundError

# Import handlers
from .handlers.control_handler import ControlCommandHandler
from .handlers.shell_handler import ShellCommandHandler
from .handlers.ai_handler import AIRequestHandler

# Import existing components (adjust paths as needed)
from ..shell.exec_shell import ShellCommandExecutor
from ..shell.is_shell import ShellCommandDetector

# Define custom exceptions for CLI controller
class CLIError(Exception):
    """Base exception for CLI controller errors."""
    pass

class CLIInitializationError(CLIError):
    """Error during CLI initialization."""
    pass


class CLIController:
    """
    Main CLI Controller for Infraware Cloud Assistant.
    
    Orchestrates the entire CLI application by coordinating:
    - Session management (user input, prompts)
    - Command processing (routing to handlers)
    - Error handling and recovery
    - Application lifecycle management
    """
    
    def __init__(self, agent=None, console: Optional[Console] = None, debug_mode: bool = False):
        """
        Initialize CLI Controller.
        
        Args:
            agent: The orchestrator agent for AI requests
            console: Rich console instance (created if None)
            debug_mode: Enable debug mode for detailed error output
        """
        self.agent = agent
        self.console = console or Console()
        self.debug_mode = debug_mode
        
        # Initialize core components
        try:
            self._initialize_components()
            self._initialize_handlers()
            self._initialize_processors()
        except Exception as e:
            raise CLIInitializationError(f"Failed to initialize CLI: {e}") from e
        
        # Runtime state
        self.running = False
        self.exit_requested = False
    
    def _initialize_components(self):
        """Initialize core shell and detection components."""
        try:
            # Initialize shell components
            self.shell_executor = ShellCommandExecutor()
            self.shell_detector = ShellCommandDetector()
            
            # Initialize session manager
            self.session_manager = SessionManager(self.shell_executor, self.console)
            
        except Exception as e:
            raise CLIInitializationError(f"Failed to initialize core components: {e}") from e
    
    def _initialize_handlers(self):
        """Initialize command handlers with proper dependencies."""
        try:
            # Create handlers in priority order
            self.control_handler = ControlCommandHandler(self.shell_executor, self.console)
            self.shell_handler = ShellCommandHandler(self.agent, self.shell_executor, self.shell_detector, self.console)
            self.ai_handler = AIRequestHandler(self.agent, self.shell_executor, self.console)
            
            # Store handlers list for easy access
            self.handlers = [self.control_handler, self.shell_handler, self.ai_handler]
            
        except Exception as e:
            raise CLIInitializationError(f"Failed to initialize handlers: {e}") from e
    
    def _initialize_processors(self):
        """Initialize command processor with handlers."""
        try:
            self.command_processor = CommandProcessor(self.handlers, self.console)
        except Exception as e:
            raise CLIInitializationError(f"Failed to initialize command processor: {e}") from e
    
    def run(self):
        """
        Main CLI application loop.
        
        Handles user input, command processing, and application lifecycle.
        """
        self.running = True
        self.exit_requested = False
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self._handle_keyboard_interrupt()
        except EOFError:
            self._handle_eof()
        except Exception as e:
            self._handle_unexpected_error(e)
        finally:
            self._cleanup()
    
    def _main_loop(self):
        """Main interaction loop."""
        while self.running and not self.exit_requested:
            try:
                # Get user input
                user_input = self.session_manager.get_user_input()
                
                # Skip completely empty input
                if not user_input.strip():
                    continue
                
                # Process the command
                self._process_command(user_input)
                
            except KeyboardInterrupt:
                # Handle Ctrl+C during command processing
                self._handle_command_interrupt()
                continue
                
            except EOFError:
                # Handle Ctrl+D during input
                self._handle_eof()
                break
                
            except Exception as e:
                # Handle unexpected errors during command processing
                self._handle_command_error(e)
                continue
    
    def _process_command(self, user_input: str):
        """
        Process a single command.
        
        Args:
            user_input: The command to process
        """
        try:
            # Process command through command processor
            success = self.command_processor.process_command(user_input)
            
            # Handle unsuccessful command execution
            if not success:
                self.console.print("[yellow]⚠️  Command execution was not successful[/yellow]")
                
        except CommandProcessingError as e:
            # Handle command processing errors
            self.console.print(f"[red]❌ Command processing error: {e}[/red]")
            if self.debug_mode:
                self.console.print_exception()
                
        except NoHandlerFoundError as e:
            # This should rarely happen since AI handler is fallback
            self.console.print(f"[red]❌ No handler available: {e}[/red]")
            if self.debug_mode:
                self.console.print_exception()
                
        except Exception as e:
            # Handle any other unexpected errors
            self.console.print(f"[red]❌ Unexpected error processing command: {e}[/red]")
            if self.debug_mode:
                self.console.print_exception()
    
    def _handle_keyboard_interrupt(self):
        """Handle main loop Ctrl+C interruption."""
        # Try to interrupt current shell command first
        if self.shell_executor.interrupt_current_command():
            self.console.print("\n🛑 Command interrupted")
        else:
            self.console.print("\n🛑 Use 'exit' to quit")
        
        # Don't exit, continue running
    
    def _handle_command_interrupt(self):
        """Handle Ctrl+C during command processing."""
        # Try to interrupt current shell command
        if self.shell_executor.interrupt_current_command():
            self.console.print("\n🛑 Command interrupted")
        else:
            self.console.print("\n🛑 Operation interrupted")
    
    def _handle_eof(self):
        """Handle Ctrl+D (EOF) input."""
        self.console.print("\n👋 Thanks for using [bold #2B1BD1]Infraware CLI[/bold #2B1BD1]! Goodbye!")
        self.exit_requested = True
    
    def _handle_unexpected_error(self, error: Exception):
        """Handle unexpected errors in main loop."""
        self.console.print(f"[red]❌ Fatal error in CLI: {error}[/red]")
        if self.debug_mode:
            self.console.print(f"[red]Error details: {repr(error)}[/red]")
        self.exit_requested = True  # Just exit
    
    def _cleanup(self):
        """Cleanup resources before exit."""
        self.running = False
        # Any additional cleanup can be added here
    
    def stop(self):
        """Stop the CLI application gracefully."""
        self.exit_requested = True
        self.running = False
    
    def get_statistics(self) -> dict:
        """
        Get comprehensive CLI statistics.
        
        Returns:
            Dictionary with CLI and command processing statistics
        """
        processor_stats = self.command_processor.get_processing_stats()
        session_info = self.session_manager.get_session_info()
        
        return {
            'cli_status': {
                'running': self.running,
                'exit_requested': self.exit_requested,
                'debug_mode': self.debug_mode
            },
            'session': session_info,
            'command_processing': processor_stats,
            'handlers': self.command_processor.list_handlers()
        }
    
    def reset_statistics(self):
        """Reset all statistics."""
        self.command_processor.reset_stats()
        # Session manager doesn't have resettable stats currently
    
    def add_handler(self, handler, position: Optional[int] = None):
        """
        Add a new command handler.
        
        Args:
            handler: Handler instance to add
            position: Position to insert (None = append)
        """
        self.command_processor.add_handler(handler, position)
        self.handlers = self.command_processor.handlers  # Update local reference
    
    def remove_handler(self, handler_class):
        """
        Remove a command handler by class.
        
        Args:
            handler_class: Class of handler to remove
            
        Returns:
            bool: True if handler was removed
        """
        removed = self.command_processor.remove_handler(handler_class)
        if removed:
            self.handlers = self.command_processor.handlers  # Update local reference
        return removed
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug mode."""
        self.debug_mode = enabled
    
    def get_session_context(self) -> dict:
        """Get current session context."""
        return self.session_manager.get_context()
    
    def force_context_refresh(self):
        """Force refresh of session context (useful after directory changes)."""
        self.session_manager.force_context_refresh()
    
    def __str__(self) -> str:
        """String representation for debugging."""
        context = self.get_session_context()
        return f"CLIController(running={self.running}, user={context.get('username', 'unknown')})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        stats = self.get_statistics()
        return (f"CLIController(running={self.running}, "
                f"handlers={len(self.handlers)}, "
                f"commands_processed={stats['command_processing']['total_commands']})")


# Factory function for easy CLI creation
def create_cli_controller(agent=None, console: Optional[Console] = None, debug_mode: bool = False) -> CLIController:
    """
    Factory function to create a CLI controller with all dependencies.
    
    Args:
        agent: The orchestrator agent for AI requests
        console: Rich console instance (optional)
        debug_mode: Enable debug mode
        
    Returns:
        Configured CLIController instance
    """
    try:
        return CLIController(agent=agent, console=console, debug_mode=debug_mode)
    except CLIInitializationError as e:
        if console:
            console.print(f"[red]❌ Failed to create CLI controller: {e}[/red]")
        else:
            print(f"❌ Failed to create CLI controller: {e}")
        raise



