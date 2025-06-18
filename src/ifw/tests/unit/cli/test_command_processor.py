"""
Comprehensive unit test suite for CommandProcessor class.
Uses pure pytest without any unittest or mock imports.
"""

import pytest
from rich.console import Console
from io import StringIO

# Import the classes to test
from ifw.cli.command_processor import (
    CommandProcessor,
    CommandProcessingError,
    NoHandlerFoundError,
)


class SimpleHandler:
    """Simple handler for testing - no complex mocking."""

    def __init__(self, name: str, accepts_all=True, always_succeeds=True):
        self.name = name
        self.accepts_all = accepts_all
        self.always_succeeds = always_succeeds
        self.handled_commands = []
        self.can_handle_calls = []
        self._custom_can_handle = None
        self._custom_handle = None
        self._should_raise_on_can_handle = None
        self._should_raise_on_handle = None

    def set_custom_can_handle(self, func):
        """Set custom can_handle logic."""
        self._custom_can_handle = func

    def set_custom_handle(self, func):
        """Set custom handle logic."""
        self._custom_handle = func

    def set_can_handle_exception(self, exception):
        """Set exception to raise in can_handle."""
        self._should_raise_on_can_handle = exception

    def set_handle_exception(self, exception):
        """Set exception to raise in handle."""
        self._should_raise_on_handle = exception

    def can_handle(self, user_input: str) -> bool:
        """Determine if this handler can process the input."""
        self.can_handle_calls.append(user_input)

        if self._should_raise_on_can_handle:
            raise self._should_raise_on_can_handle

        if self._custom_can_handle:
            return self._custom_can_handle(user_input)

        return self.accepts_all

    def handle(self, user_input: str) -> bool:
        """Process the input."""
        self.handled_commands.append(user_input)

        if self._should_raise_on_handle:
            raise self._should_raise_on_handle

        if self._custom_handle:
            return self._custom_handle(user_input)

        return self.always_succeeds


# Different handler classes for testing
class HandlerTypeA(SimpleHandler):
    pass


class HandlerTypeB(SimpleHandler):
    pass


class HandlerTypeC(SimpleHandler):
    pass


class HandlerTypeD(SimpleHandler):
    pass


# Fixtures
@pytest.fixture
def console():
    """Provide a console for testing."""
    return Console()


@pytest.fixture
def string_console():
    """Provide a console that captures output."""
    string_io = StringIO()
    return Console(file=string_io, force_terminal=False)


@pytest.fixture
def basic_handler():
    """Provide a basic handler."""
    return HandlerTypeA("TestHandler")


@pytest.fixture
def processor(console, basic_handler):
    """Provide a basic processor with one handler."""
    return CommandProcessor([basic_handler], console)


class TestCommandProcessorInitialization:
    """Test CommandProcessor initialization."""

    def test_init_with_handlers_and_console(self, console):
        """Test normal initialization."""
        handler1 = HandlerTypeA("Handler1")
        handler2 = HandlerTypeB("Handler2")
        handlers = [handler1, handler2]

        processor = CommandProcessor(handlers, console)

        assert processor.handlers == handlers
        assert processor.console == console
        assert processor.commands_processed == 0
        assert processor.successful_commands == 0
        assert processor.failed_commands == 0
        assert len(processor.handler_stats) == 2
        assert "HandlerTypeA" in processor.handler_stats
        assert "HandlerTypeB" in processor.handler_stats

    def test_init_with_empty_handlers(self, console):
        """Test initialization with empty handlers list."""
        processor = CommandProcessor([], console)

        assert processor.handlers == []
        assert processor.handler_stats == {}

    def test_handler_stats_initialization(self, console):
        """Test that handler statistics are properly initialized."""
        handler = HandlerTypeA("TestHandler")

        processor = CommandProcessor([handler], console)

        expected_stats = {
            "HandlerTypeA": {  # Note: uses actual class name
                "processed": 0,
                "successful": 0,
                "failed": 0,
            }
        }
        assert processor.handler_stats == expected_stats


class TestCommandProcessing:
    """Test the main command processing functionality."""

    def test_successful_command_processing(self, processor, basic_handler):
        """Test successful command processing."""
        result = processor.process_command("test command")

        assert result is True
        assert processor.commands_processed == 1
        assert processor.successful_commands == 1
        assert processor.failed_commands == 0
        assert basic_handler.handled_commands == ["test command"]

    def test_failed_command_processing(self, console):
        """Test command processing that fails."""
        handler = HandlerTypeB("FailHandler", always_succeeds=False)
        processor = CommandProcessor([handler], console)

        result = processor.process_command("test command")

        assert result is False
        assert processor.commands_processed == 1
        assert processor.successful_commands == 0
        assert processor.failed_commands == 1

    def test_handler_priority_order(self, console):
        """Test that handlers are tried in order."""
        handler1 = HandlerTypeA("Handler1", accepts_all=False)
        handler2 = HandlerTypeB("Handler2", accepts_all=True)
        handler3 = HandlerTypeC("Handler3", accepts_all=True)

        processor = CommandProcessor([handler1, handler2, handler3], console)

        processor.process_command("test")

        # Only handler2 should have processed the command
        assert handler1.handled_commands == []
        assert handler2.handled_commands == ["test"]
        assert handler3.handled_commands == []

    def test_invalid_input_none(self, processor):
        """Test handling of None input."""
        result = processor.process_command(None)
        assert result is False
        assert processor.commands_processed == 0

    def test_invalid_input_non_string(self, processor):
        """Test handling of non-string input."""
        result = processor.process_command(123)
        assert result is False
        assert processor.commands_processed == 0

    def test_empty_string_input(self, processor):
        """Test handling of empty string input."""
        result = processor.process_command("")
        assert result is False
        assert processor.commands_processed == 0

    def test_whitespace_only_input(self, processor):
        """Test handling of whitespace-only input."""
        result = processor.process_command("   \t\n  ")

        assert result is True
        assert processor.commands_processed == 0


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_no_handler_found_error(self, console):
        """Test NoHandlerFoundError when no handler can process command."""
        handler = HandlerTypeA("TestHandler", accepts_all=False)
        processor = CommandProcessor([handler], console)

        with pytest.raises(NoHandlerFoundError) as exc_info:
            processor.process_command("unhandleable command")

        assert "No handler found for command" in str(exc_info.value)
        # Exception is raised before failed_commands can be incremented
        assert processor.failed_commands == 0

    def test_handler_can_handle_exception(self, console):
        """Test handling of exceptions in can_handle method."""
        handler1 = HandlerTypeA("FailingHandler")
        handler1.set_can_handle_exception(ValueError("Handler check failed"))

        handler2 = HandlerTypeB("WorkingHandler")
        processor = CommandProcessor([handler1, handler2], console)

        result = processor.process_command("test")

        # Should continue to next handler
        assert result is True
        assert handler2.handled_commands == ["test"]

    def test_handler_execution_exception(self, console):
        """Test handling of exceptions during command execution."""
        handler = HandlerTypeA("FailingHandler")
        handler.set_handle_exception(RuntimeError("Handler execution failed"))

        processor = CommandProcessor([handler], console)

        with pytest.raises(CommandProcessingError) as exc_info:
            processor.process_command("test")

        assert "Handler HandlerTypeA failed to process command" in str(exc_info.value)
        assert processor.failed_commands == 1

    def test_multiple_handlers_with_can_handle_exceptions(self, console):
        """Test that processor continues through handlers even if some raise exceptions."""
        handler1 = HandlerTypeA("Failing1")
        handler1.set_can_handle_exception(ValueError("First fails"))

        handler2 = HandlerTypeB("Failing2")
        handler2.set_can_handle_exception(RuntimeError("Second fails"))

        handler3 = HandlerTypeC("Working", accepts_all=True)

        processor = CommandProcessor([handler1, handler2, handler3], console)

        result = processor.process_command("test")

        assert result is True
        assert handler3.handled_commands == ["test"]


class TestStatistics:
    """Test statistics tracking functionality."""

    def test_stats_update_on_success(self, processor, basic_handler):
        """Test statistics updates on successful command processing."""
        processor.process_command("test1")
        processor.process_command("test2")

        stats = processor.get_processing_stats()
        assert stats["total_commands"] == 2
        assert stats["successful_commands"] == 2
        assert stats["failed_commands"] == 0
        assert stats["success_rate"] == 100.0
        assert stats["handler_stats"]["HandlerTypeA"]["processed"] == 2
        assert stats["handler_stats"]["HandlerTypeA"]["successful"] == 2
        assert stats["handler_stats"]["HandlerTypeA"]["failed"] == 0

    def test_stats_update_on_failure(self, console):
        """Test statistics updates on failed command processing."""
        handler = HandlerTypeA("TestHandler", always_succeeds=False)
        processor = CommandProcessor([handler], console)

        processor.process_command("test")

        stats = processor.get_processing_stats()
        assert stats["total_commands"] == 1
        assert stats["successful_commands"] == 0
        assert stats["failed_commands"] == 1
        assert stats["success_rate"] == 0.0
        assert stats["handler_stats"]["HandlerTypeA"]["processed"] == 1
        assert stats["handler_stats"]["HandlerTypeA"]["successful"] == 0
        assert stats["handler_stats"]["HandlerTypeA"]["failed"] == 1

    def test_stats_reset(self, processor):
        """Test statistics reset functionality."""
        processor.process_command("test")
        processor.reset_stats()

        stats = processor.get_processing_stats()
        assert stats["total_commands"] == 0
        assert stats["successful_commands"] == 0
        assert stats["failed_commands"] == 0
        assert stats["handler_stats"]["HandlerTypeA"]["processed"] == 0
        assert stats["handler_stats"]["HandlerTypeA"]["successful"] == 0
        assert stats["handler_stats"]["HandlerTypeA"]["failed"] == 0

    def test_success_rate_calculation_mixed_results(self, console):
        """Test success rate calculation with mixed results."""
        handler = HandlerTypeA("TestHandler")
        processor = CommandProcessor([handler], console)

        # Process some commands
        processor.process_command("test1")
        processor.process_command("test2")
        processor.process_command("test3")

        # Manually adjust for testing specific scenario
        processor.successful_commands = 2
        processor.failed_commands = 1

        stats = processor.get_processing_stats()
        expected_rate = (2 / 3) * 100
        assert abs(stats["success_rate"] - expected_rate) < 0.1

    def test_success_rate_calculation_no_commands(self, processor):
        """Test success rate calculation with no commands processed."""
        stats = processor.get_processing_stats()
        assert stats["success_rate"] == 0.0

    def test_handler_stats_for_multiple_handlers(self, console):
        """Test statistics tracking for multiple handlers."""
        handler1 = HandlerTypeA("Handler1")
        handler1.set_custom_can_handle(lambda x: x.startswith("cmd1"))

        handler2 = HandlerTypeB("Handler2")
        handler2.set_custom_can_handle(lambda x: x.startswith("cmd2"))

        processor = CommandProcessor([handler1, handler2], console)

        processor.process_command("cmd1 test")
        processor.process_command("cmd2 test")

        stats = processor.get_processing_stats()
        assert stats["handler_stats"]["HandlerTypeA"]["processed"] == 1
        assert stats["handler_stats"]["HandlerTypeB"]["processed"] == 1


class TestHandlerManagement:
    """Test handler management functionality."""

    def test_add_handler_at_end(self, console):
        """Test adding handler at the end of the list."""
        handler1 = HandlerTypeA("Handler1")
        handler2 = HandlerTypeB("Handler2")
        processor = CommandProcessor([handler1], console)

        processor.add_handler(handler2)

        assert len(processor.handlers) == 2
        assert processor.handlers[1] == handler2
        assert "HandlerTypeA" in processor.handler_stats
        assert "HandlerTypeB" in processor.handler_stats

    def test_add_handler_at_position(self, console):
        """Test adding handler at specific position."""
        handler1 = HandlerTypeA("Handler1")
        handler2 = HandlerTypeB("Handler2")
        handler3 = HandlerTypeC("Handler3")
        processor = CommandProcessor([handler1, handler3], console)

        processor.add_handler(handler2, position=1)

        assert len(processor.handlers) == 3
        assert processor.handlers[1] == handler2
        assert processor.handlers[2] == handler3

    def test_remove_handler_success(self, console):
        """Test removing handler by class type."""
        handler1 = HandlerTypeA("HandlerA")
        handler2 = HandlerTypeB("HandlerB")
        processor = CommandProcessor([handler1, handler2], console)

        # Remove by class type
        result = processor.remove_handler(HandlerTypeA)

        assert result is True
        assert len(processor.handlers) == 1
        assert processor.handlers[0] == handler2
        assert "HandlerTypeA" not in processor.handler_stats
        assert "HandlerTypeB" in processor.handler_stats

    def test_remove_nonexistent_handler(self, console):
        """Test removing handler that doesn't exist."""
        handler = HandlerTypeA("Handler1")
        processor = CommandProcessor([handler], console)

        class NonExistentHandler:
            pass

        result = processor.remove_handler(NonExistentHandler)

        assert result is False
        assert len(processor.handlers) == 1

    def test_list_handlers(self, console):
        """Test listing handler names."""
        handler1 = HandlerTypeA("Handler1")
        handler2 = HandlerTypeB("Handler2")
        processor = CommandProcessor([handler1, handler2], console)

        handler_names = processor.list_handlers()

        assert handler_names == ["HandlerTypeA", "HandlerTypeB"]

    def test_list_handlers_empty(self, console):
        """Test listing handlers when none exist."""
        processor = CommandProcessor([], console)

        handler_names = processor.list_handlers()

        assert handler_names == []


class TestDebuggingFeatures:
    """Test debugging and utility features."""

    def test_get_handler_for_input_found(self, console):
        """Test getting handler for specific input."""
        handler1 = HandlerTypeA("Handler1")
        handler1.set_custom_can_handle(lambda x: x.startswith("hello"))

        handler2 = HandlerTypeB("Handler2")
        handler2.set_custom_can_handle(lambda x: x.startswith("goodbye"))

        processor = CommandProcessor([handler1, handler2], console)

        result_handler = processor.get_handler_for_input("hello world")
        assert result_handler == handler1

        result_handler = processor.get_handler_for_input("goodbye world")
        assert result_handler == handler2

    def test_get_handler_for_input_not_found(self, console):
        """Test getting handler when no handler can handle input."""
        handler = HandlerTypeA("Handler", accepts_all=False)
        processor = CommandProcessor([handler], console)

        result_handler = processor.get_handler_for_input("unknown command")
        assert result_handler is None

    def test_get_handler_for_input_with_exception(self, console):
        """Test get_handler_for_input when handler raises exception."""
        handler = HandlerTypeA("FailingHandler")
        handler.set_can_handle_exception(ValueError("test error"))

        processor = CommandProcessor([handler], console)

        result = processor.get_handler_for_input("test")

        assert result is None

    def test_test_routing(self, console):
        """Test command routing testing functionality."""
        handler1 = HandlerTypeA("Handler1")
        handler1.set_custom_can_handle(lambda x: x.startswith("cmd1"))

        handler2 = HandlerTypeB("Handler2")
        handler2.set_custom_can_handle(lambda x: x.startswith("cmd2"))

        processor = CommandProcessor([handler1, handler2], console)

        test_commands = ["cmd1 test", "cmd2 test", "unknown command"]
        routing_results = processor.test_routing(test_commands)

        expected = {
            "cmd1 test": "HandlerTypeA",
            "cmd2 test": "HandlerTypeB",
            "unknown command": "No Handler",
        }
        assert routing_results == expected

    def test_test_routing_with_exceptions(self, console):
        """Test routing test with handlers that raise exceptions."""
        handler = HandlerTypeA("FailingHandler")
        handler.set_can_handle_exception(RuntimeError("test"))

        processor = CommandProcessor([handler], console)

        routing_results = processor.test_routing(["test command"])

        assert routing_results["test command"] == "No Handler"

    def test_string_representation(self, processor):
        """Test __str__ method."""
        str_repr = str(processor)
        assert "CommandProcessor" in str_repr
        assert "HandlerTypeA" in str_repr
        assert "processed=0" in str_repr

    def test_detailed_representation(self, processor):
        """Test __repr__ method."""
        repr_str = repr(processor)
        assert "CommandProcessor" in repr_str
        assert "handlers=1" in repr_str
        assert "processed=0" in repr_str
        assert "success_rate=" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
