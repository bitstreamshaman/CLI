"""
Command Processor for Infraware Cloud Assistant.
Routes user commands to appropriate handlers.
"""
# Import handler base class
from .handlers.base_handler import BaseHandler
from typing import List, Optional
from rich.console import Console

# Define custom exceptions
class CommandProcessingError(Exception):
    """Error during command processing."""

    pass


class NoHandlerFoundError(CommandProcessingError):
    """No handler could process the command."""

    pass


class CommandProcessor:
    """
    Command processor that routes user input to appropriate handlers.

    Responsibilities:
    - Route commands to the first handler that can process them
    - Handle command processing errors
    - Track command processing statistics
    - Provide debugging information
    """

    def __init__(self, handlers: List[BaseHandler], console: Console):
        """
        Initialize command processor.

        Args:
            handlers: List of command handlers in priority order
            console: Rich console for error output
        """
        self.handlers = handlers
        self.console = console

        # Statistics tracking
        self.commands_processed = 0
        self.successful_commands = 0
        self.failed_commands = 0
        self.handler_stats = {}

        # Initialize handler statistics
        for handler in handlers:
            handler_name = handler.__class__.__name__
            self.handler_stats[handler_name] = {
                "processed": 0,
                "successful": 0,
                "failed": 0,
            }

    def process_command(self, user_input: str) -> bool:
        """
        Process a user command by routing it to the appropriate handler.

        Args:
            user_input: The command string to process

        Returns:
            bool: True if command was processed successfully, False otherwise

        Raises:
            NoHandlerFoundError: If no handler can process the command
            CommandProcessingError: If command processing fails unexpectedly
        """
        # Validate input
        if not user_input or not isinstance(user_input, str):
            self.console.print("[red]❌ Invalid command input[/red]")
            self._update_stats(None, False)
            return False

        # Skip completely empty input
        if not user_input.strip():
            return True

        self.commands_processed += 1

        # Find appropriate handler
        selected_handler = None
        handler_name = None

        try:
            # Try each handler in order until one can handle the command
            for handler in self.handlers:
                try:
                    if handler.can_handle(user_input):
                        selected_handler = handler
                        handler_name = handler.__class__.__name__
                        break
                except Exception as e:
                    # Log handler selection error but continue
                    self.console.print(
                        f"[yellow]⚠️  Error checking handler {handler.__class__.__name__}: {e}[/yellow]"
                    )
                    continue

            # If no handler found, this shouldn't happen if AI handler is fallback
            if selected_handler is None:
                error_msg = f"No handler found for command: '{user_input[:50]}...'"
                self.console.print(f"[red]❌ {error_msg}[/red]")
                self._update_stats(None, False)
                raise NoHandlerFoundError(error_msg)

            # Execute the command with the selected handler
            try:
                success = selected_handler.handle(user_input)
                self._update_stats(handler_name, success)

                if success:
                    self.successful_commands += 1
                else:
                    self.failed_commands += 1

                return success

            except Exception as e:
                # Handle command execution error
                error_msg = f"Handler {handler_name} failed to process command: {e}"
                self.console.print(f"[red]❌ {error_msg}[/red]")
                self._update_stats(handler_name, False)
                self.failed_commands += 1

                # Re-raise as CommandProcessingError for caller to handle
                raise CommandProcessingError(error_msg) from e

        except (NoHandlerFoundError, CommandProcessingError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            # Handle unexpected errors
            error_msg = f"Unexpected error processing command: {e}"
            self.console.print(f"[red]❌ {error_msg}[/red]")
            self._update_stats(None, False)
            self.failed_commands += 1
            raise CommandProcessingError(error_msg) from e

    def _update_stats(self, handler_name: Optional[str], success: bool) -> None:
        """Update handler statistics."""
        if handler_name and handler_name in self.handler_stats:
            self.handler_stats[handler_name]["processed"] += 1
            if success:
                self.handler_stats[handler_name]["successful"] += 1
            else:
                self.handler_stats[handler_name]["failed"] += 1

    def get_handler_for_input(self, user_input: str) -> Optional[BaseHandler]:
        """
        Get the handler that would process the given input (for debugging).

        Args:
            user_input: Command to check

        Returns:
            Handler that would process the command, or None
        """
        for handler in self.handlers:
            try:
                if handler.can_handle(user_input):
                    return handler
            except Exception:
                continue
        return None

    def get_processing_stats(self) -> dict:
        """
        Get command processing statistics.

        Returns:
            Dict with processing statistics
        """
        return {
            "total_commands": self.commands_processed,
            "successful_commands": self.successful_commands,
            "failed_commands": self.failed_commands,
            "success_rate": (self.successful_commands / max(1, self.commands_processed))
            * 100,
            "handler_stats": self.handler_stats.copy(),
        }

    def reset_stats(self) -> None:
        """Reset all processing statistics."""
        self.commands_processed = 0
        self.successful_commands = 0
        self.failed_commands = 0
        for handler_name in self.handler_stats:
            self.handler_stats[handler_name] = {
                "processed": 0,
                "successful": 0,
                "failed": 0,
            }

    def add_handler(self, handler: BaseHandler, position: Optional[int] = None) -> None:
        """
        Add a new handler to the processor.

        Args:
            handler: Handler to add
            position: Position to insert (None = append at end)
        """
        if position is None:
            self.handlers.append(handler)
        else:
            self.handlers.insert(position, handler)

        # Initialize stats for new handler
        handler_name = handler.__class__.__name__
        self.handler_stats[handler_name] = {
            "processed": 0,
            "successful": 0,
            "failed": 0,
        }

    def remove_handler(self, handler_class) -> bool:
        """
        Remove a handler by class type.

        Args:
            handler_class: Class of handler to remove

        Returns:
            True if handler was found and removed
        """
        for i, handler in enumerate(self.handlers):
            if isinstance(handler, handler_class):
                removed_handler = self.handlers.pop(i)
                # Clean up stats
                handler_name = removed_handler.__class__.__name__
                if handler_name in self.handler_stats:
                    del self.handler_stats[handler_name]
                return True
        return False

    def list_handlers(self) -> List[str]:
        """
        Get list of handler names in processing order.

        Returns:
            List of handler class names
        """
        return [handler.__class__.__name__ for handler in self.handlers]

    def test_routing(self, test_commands: List[str]) -> dict:
        """
        Test command routing without executing commands (for debugging).

        Args:
            test_commands: List of commands to test routing for

        Returns:
            Dict mapping commands to handler names
        """
        routing_results = {}
        for command in test_commands:
            handler = self.get_handler_for_input(command)
            handler_name = handler.__class__.__name__ if handler else "No Handler"
            routing_results[command] = handler_name
        return routing_results

    def __str__(self) -> str:
        """String representation for debugging."""
        handler_names = self.list_handlers()
        return f"CommandProcessor(handlers={handler_names}, processed={self.commands_processed})"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"CommandProcessor(handlers={len(self.handlers)}, "
            f"processed={self.commands_processed}, "
            f"success_rate={self.successful_commands / max(1, self.commands_processed) * 100:.1f}%)"
        )
