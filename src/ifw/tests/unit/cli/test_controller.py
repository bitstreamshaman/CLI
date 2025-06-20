"""
Comprehensive unit test suite for CLIController class.
Uses pure pytest - tests controller orchestration and lifecycle management.
"""

import pytest
from rich.console import Console
from io import StringIO

# Import the classes to test
from ifw.cli.controller import (
    CLIController,
    CLIInitializationError,
    create_cli_controller,
)


class MockAgent:
    """Mock agent for testing."""

    def __init__(self):
        self.messages = []
        self.call_count = 0

    def __call__(self, user_input):
        self.call_count += 1
        return f"AI response to: {user_input}"


class MockShellExecutor:
    """Mock shell executor for testing."""

    def __init__(self):
        self.executed_commands = []
        self.interrupt_called = False
        self.should_interrupt = True

    def execute_shell_command(self, command):
        self.executed_commands.append(command)
        return f"Output of: {command}"

    def interrupt_current_command(self):
        self.interrupt_called = True
        return self.should_interrupt


class MockShellDetector:
    """Mock shell detector for testing."""

    def __init__(self):
        self.is_shell_responses = {}

    def is_shell_command(self, command):
        return self.is_shell_responses.get(command, False)

    def set_shell_command(self, command, is_shell=True):
        self.is_shell_responses[command] = is_shell


class MockSessionManager:
    """Mock session manager for testing."""

    def __init__(self, shell_executor=None, console=None):
        self.input_queue = []
        self.input_index = 0
        self.context = {"username": "testuser", "cwd": "/test"}
        self.session_info = {"commands_run": 0}
        self.shell_executor = shell_executor
        self.console = console

    def get_user_input(self):
        if self.input_index < len(self.input_queue):
            result = self.input_queue[self.input_index]
            self.input_index += 1
            return result
        raise EOFError("No more input")

    def add_input(self, user_input):
        self.input_queue.append(user_input)

    def get_context(self):
        return self.context

    def get_session_info(self):
        return self.session_info

    def force_context_refresh(self):
        pass


class MockHandler:
    """Mock handler for testing."""

    def __init__(self, name, can_handle_result=True, handle_result=True):
        self.name = name
        self.can_handle_result = can_handle_result
        self.handle_result = handle_result
        self.handled_commands = []
        self.can_handle_calls = []

    def can_handle(self, user_input):
        self.can_handle_calls.append(user_input)
        if callable(self.can_handle_result):
            return self.can_handle_result(user_input)
        return self.can_handle_result

    def handle(self, user_input):
        self.handled_commands.append(user_input)
        if callable(self.handle_result):
            return self.handle_result(user_input)
        return self.handle_result


class MockCommandProcessor:
    """Mock command processor for testing."""

    def __init__(self, handlers=None, console=None):
        self.processed_commands = []
        self.handlers = handlers or []
        self.console = console
        self.should_raise = None
        self.stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "success_rate": 100.0,
            "handler_stats": {},
        }

    def process_command(self, user_input):
        self.processed_commands.append(user_input)
        self.stats["total_commands"] += 1

        if self.should_raise:
            raise self.should_raise

        self.stats["successful_commands"] += 1
        return True

    def get_processing_stats(self):
        return self.stats.copy()

    def reset_stats(self):
        self.stats = {
            "total_commands": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "success_rate": 100.0,
            "handler_stats": {},
        }

    def add_handler(self, handler, position=None):
        if position is None:
            self.handlers.append(handler)
        else:
            self.handlers.insert(position, handler)

    def remove_handler(self, handler_class):
        for i, handler in enumerate(self.handlers):
            if isinstance(handler, handler_class):
                self.handlers.pop(i)
                return True
        return False

    def list_handlers(self):
        return [h.__class__.__name__ for h in self.handlers]


# Mock implementations that will replace real classes
def mock_session_manager_factory(shell_executor, console):
    return MockSessionManager(shell_executor, console)


def mock_command_processor_factory(handlers, console):
    return MockCommandProcessor(handlers, console)


def mock_shell_executor_factory():
    return MockShellExecutor()


def mock_shell_detector_factory():
    return MockShellDetector()


def mock_control_handler_factory(shell_executor, console):
    return MockHandler("ControlHandler")


def mock_shell_handler_factory(agent, shell_executor, shell_detector, console):
    return MockHandler("ShellHandler")


def mock_ai_handler_factory(agent, shell_executor, console):
    return MockHandler("AIHandler")


# Fixtures
@pytest.fixture
def mock_agent():
    """Provide a mock agent."""
    return MockAgent()


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
def mock_cli_controller(monkeypatch):
    """Provide a CLIController with all dependencies mocked."""
    # Create mock agent
    mock_agent = MockAgent()
    console = Console()

    # Mock all the imports
    monkeypatch.setattr(
        "ifw.cli.controller.SessionManager", mock_session_manager_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.ShellCommandExecutor", mock_shell_executor_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
    )
    monkeypatch.setattr("ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory)

    return CLIController(agent=mock_agent, console=console)


def create_mock_cli_controller(monkeypatch, mock_agent=None, console=None):
    """Helper function to create a mock CLI controller."""
    if mock_agent is None:
        mock_agent = MockAgent()
    if console is None:
        console = Console()

    # Mock all the imports
    monkeypatch.setattr(
        "ifw.cli.controller.SessionManager", mock_session_manager_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.ShellCommandExecutor", mock_shell_executor_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
    )
    monkeypatch.setattr(
        "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
    )
    monkeypatch.setattr("ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory)

    return CLIController(agent=mock_agent, console=console)


class TestCLIControllerInitialization:
    """Test CLIController initialization."""

    def test_successful_initialization(self, mock_agent, console, monkeypatch):
        """Test successful CLIController initialization."""
        # Mock all dependencies
        monkeypatch.setattr(
            "ifw.cli.controller.SessionManager", mock_session_manager_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandExecutor", mock_shell_executor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory
        )

        controller = CLIController(agent=mock_agent, console=console, debug_mode=True)

        assert controller.agent == mock_agent
        assert controller.console == console
        assert controller.debug_mode is True
        assert controller.running is False
        assert controller.exit_requested is False
        assert len(controller.handlers) == 3

    def test_initialization_with_defaults(self, mock_agent, monkeypatch):
        """Test initialization with default parameters."""
        # Mock all dependencies
        monkeypatch.setattr(
            "ifw.cli.controller.SessionManager", mock_session_manager_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandExecutor", mock_shell_executor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory
        )

        controller = CLIController(agent=mock_agent)

        assert controller.agent == mock_agent
        assert isinstance(controller.console, Console)
        assert controller.debug_mode is False

    def test_initialization_failure_in_components(
        self, mock_agent, console, monkeypatch
    ):
        """Test initialization failure during component setup."""

        def failing_shell_executor():
            raise Exception("Executor initialization failed")

        # Mock other dependencies normally, but make shell executor fail
        monkeypatch.setattr(
            "ifw.cli.controller.SessionManager", mock_session_manager_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandExecutor", failing_shell_executor
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory
        )

        with pytest.raises(CLIInitializationError) as exc_info:
            CLIController(agent=mock_agent, console=console)

        assert "Failed to initialize CLI" in str(exc_info.value)
        assert "Executor initialization failed" in str(exc_info.value)

    def test_initialization_failure_in_handlers(self, mock_agent, console, monkeypatch):
        """Test initialization failure during handler setup."""

        def failing_control_handler(shell_executor, console):
            raise Exception("Control handler initialization failed")

        # Mock dependencies normally, but make control handler fail
        monkeypatch.setattr(
            "ifw.cli.controller.SessionManager", mock_session_manager_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandExecutor", mock_shell_executor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ControlCommandHandler", failing_control_handler
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory
        )

        with pytest.raises(CLIInitializationError) as exc_info:
            CLIController(agent=mock_agent, console=console)

        assert "Failed to initialize handlers" in str(exc_info.value)

    def test_initialization_failure_in_processors(
        self, mock_agent, console, monkeypatch
    ):
        """Test initialization failure during processor setup."""

        def failing_command_processor(handlers, console):
            raise Exception("Processor initialization failed")

        # Mock dependencies normally, but make command processor fail
        monkeypatch.setattr(
            "ifw.cli.controller.SessionManager", mock_session_manager_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.CommandProcessor", failing_command_processor
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandExecutor", mock_shell_executor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory
        )

        with pytest.raises(CLIInitializationError) as exc_info:
            CLIController(agent=mock_agent, console=console)

        assert "Failed to initialize command processor" in str(exc_info.value)


class TestCLIControllerRunMethod:
    """Test CLIController run method and main loop."""

    def test_run_with_single_command(self, monkeypatch):
        """Test running CLI with a single command."""
        controller = create_mock_cli_controller(monkeypatch)

        # Add input to session manager
        controller.session_manager.add_input("test command")

        # Run the CLI
        controller.run()

        # Verify command was processed
        assert len(controller.command_processor.processed_commands) == 1
        assert controller.command_processor.processed_commands[0] == "test command"
        assert not controller.running

    def test_run_with_multiple_commands(self, monkeypatch):
        """Test running CLI with multiple commands."""
        controller = create_mock_cli_controller(monkeypatch)

        # Add multiple inputs
        controller.session_manager.add_input("command1")
        controller.session_manager.add_input("command2")
        controller.session_manager.add_input("command3")

        controller.run()

        # Verify all commands were processed
        assert len(controller.command_processor.processed_commands) == 3
        assert controller.command_processor.processed_commands == [
            "command1",
            "command2",
            "command3",
        ]

    def test_run_with_empty_input_skipped(self, monkeypatch):
        """Test that empty input is skipped."""
        controller = create_mock_cli_controller(monkeypatch)

        # Add empty and whitespace inputs
        controller.session_manager.add_input("")
        controller.session_manager.add_input("   ")
        controller.session_manager.add_input("real command")

        controller.run()

        # Only the real command should be processed
        assert len(controller.command_processor.processed_commands) == 1
        assert controller.command_processor.processed_commands[0] == "real command"

    def test_run_handles_eof_gracefully(self, monkeypatch):
        """Test that EOFError (Ctrl+D) is handled gracefully."""
        controller = create_mock_cli_controller(monkeypatch)

        # No input added, so EOFError will be raised immediately
        controller.run()

        assert controller.exit_requested
        assert not controller.running

    def test_run_handles_keyboard_interrupt(self, monkeypatch):
        """Test that KeyboardInterrupt is handled gracefully."""
        controller = create_mock_cli_controller(monkeypatch)

        # Track how many times get_user_input is called to prevent infinite loop
        call_count = 0

        def raise_keyboard_interrupt():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise KeyboardInterrupt()
            else:
                # After the first KeyboardInterrupt, raise EOFError to exit
                raise EOFError()

        # Mock session manager to raise KeyboardInterrupt then EOF
        monkeypatch.setattr(
            controller.session_manager, "get_user_input", raise_keyboard_interrupt
        )

        controller.run()

        # Should handle interrupt and then exit on EOF
        assert not controller.running
        assert call_count >= 1


class TestCLIControllerCommandProcessing:
    """Test command processing functionality."""

    def test_process_command_success(self, monkeypatch):
        """Test successful command processing."""
        controller = create_mock_cli_controller(monkeypatch)

        controller._process_command("test command")

        assert len(controller.command_processor.processed_commands) == 1
        assert controller.command_processor.processed_commands[0] == "test command"

    def test_process_command_with_command_processing_error(self, monkeypatch):
        """Test handling of CommandProcessingError."""
        from ifw.cli.command_processor import CommandProcessingError

        controller = create_mock_cli_controller(monkeypatch)

        # Make command processor raise error
        controller.command_processor.should_raise = CommandProcessingError(
            "Processing failed"
        )

        # Should not raise exception, but handle it gracefully
        controller._process_command("failing command")

        assert len(controller.command_processor.processed_commands) == 1

    def test_process_command_with_no_handler_found_error(self, monkeypatch):
        """Test handling of NoHandlerFoundError."""
        from ifw.cli.command_processor import NoHandlerFoundError

        controller = create_mock_cli_controller(monkeypatch)

        # Make command processor raise error
        controller.command_processor.should_raise = NoHandlerFoundError("No handler")

        # Should not raise exception, but handle it gracefully
        controller._process_command("unhandled command")

        assert len(controller.command_processor.processed_commands) == 1

    def test_process_command_with_unexpected_error(self, monkeypatch):
        """Test handling of unexpected errors."""
        controller = create_mock_cli_controller(monkeypatch)

        # Make command processor raise unexpected error
        controller.command_processor.should_raise = RuntimeError("Unexpected error")

        # Should not raise exception, but handle it gracefully
        controller._process_command("error command")

        assert len(controller.command_processor.processed_commands) == 1


class TestCLIControllerInterruptHandling:
    """Test interrupt and signal handling."""

    def test_handle_keyboard_interrupt_with_shell_interrupt(self, monkeypatch):
        """Test keyboard interrupt when shell command can be interrupted."""
        controller = create_mock_cli_controller(monkeypatch)
        controller.shell_executor.should_interrupt = True

        controller._handle_keyboard_interrupt()

        assert controller.shell_executor.interrupt_called
        # Should not exit, just interrupt current command
        assert not controller.exit_requested

    def test_handle_keyboard_interrupt_without_shell_interrupt(self, monkeypatch):
        """Test keyboard interrupt when no shell command to interrupt."""
        controller = create_mock_cli_controller(monkeypatch)
        controller.shell_executor.should_interrupt = False

        controller._handle_keyboard_interrupt()

        assert controller.shell_executor.interrupt_called
        assert not controller.exit_requested

    def test_handle_command_interrupt(self, monkeypatch):
        """Test handling interrupt during command processing."""
        controller = create_mock_cli_controller(monkeypatch)

        controller._handle_command_interrupt()

        assert controller.shell_executor.interrupt_called

    def test_handle_eof(self, monkeypatch):
        """Test handling EOF (Ctrl+D)."""
        controller = create_mock_cli_controller(monkeypatch)

        controller._handle_eof()

        assert controller.exit_requested

    def test_handle_unexpected_error(self, monkeypatch):
        """Test handling unexpected errors in main loop."""
        controller = create_mock_cli_controller(monkeypatch)
        test_error = RuntimeError("Unexpected error")

        controller._handle_unexpected_error(test_error)

        assert controller.exit_requested


class TestCLIControllerLifecycle:
    """Test CLI lifecycle management."""

    def test_stop_method(self, monkeypatch):
        """Test stopping the CLI gracefully."""
        controller = create_mock_cli_controller(monkeypatch)
        controller.running = True

        controller.stop()

        assert controller.exit_requested
        assert not controller.running

    def test_cleanup_method(self, monkeypatch):
        """Test cleanup functionality."""
        controller = create_mock_cli_controller(monkeypatch)
        controller.running = True

        controller._cleanup()

        assert not controller.running


class TestCLIControllerStatistics:
    """Test statistics and monitoring functionality."""

    def test_get_statistics(self, monkeypatch):
        """Test getting comprehensive statistics."""
        controller = create_mock_cli_controller(monkeypatch)

        stats = controller.get_statistics()

        assert "cli_status" in stats
        assert "session" in stats
        assert "command_processing" in stats
        assert "handlers" in stats

        # Check CLI status
        assert "running" in stats["cli_status"]
        assert "exit_requested" in stats["cli_status"]
        assert "debug_mode" in stats["cli_status"]

        # Check session info
        assert stats["session"] == {"commands_run": 0}

    def test_reset_statistics(self, monkeypatch):
        """Test resetting statistics."""
        controller = create_mock_cli_controller(monkeypatch)

        # Process a command first
        controller._process_command("test")

        # Reset statistics
        controller.reset_statistics()

        stats = controller.get_statistics()
        assert stats["command_processing"]["total_commands"] == 0


class TestCLIControllerHandlerManagement:
    """Test handler management functionality."""

    def test_add_handler(self, monkeypatch):
        """Test adding a new handler."""
        controller = create_mock_cli_controller(monkeypatch)

        new_handler = MockHandler("NewHandler")
        initial_count = len(controller.handlers)

        controller.add_handler(new_handler)

        assert len(controller.handlers) == initial_count + 1
        assert new_handler in controller.command_processor.handlers

    def test_add_handler_at_position(self, monkeypatch):
        """Test adding handler at specific position."""
        controller = create_mock_cli_controller(monkeypatch)

        new_handler = MockHandler("NewHandler")

        controller.add_handler(new_handler, position=1)

        assert controller.command_processor.handlers[1] == new_handler

    def test_remove_handler(self, monkeypatch):
        """Test removing a handler."""
        controller = create_mock_cli_controller(monkeypatch)

        initial_count = len(controller.handlers)

        # Add a handler first
        test_handler = MockHandler("TestHandler")
        controller.add_handler(test_handler)

        # Remove it
        result = controller.remove_handler(MockHandler)

        assert result is True
        assert len(controller.handlers) == initial_count

    def test_remove_nonexistent_handler(self, monkeypatch):
        """Test removing a handler that doesn't exist."""
        controller = create_mock_cli_controller(monkeypatch)

        class NonExistentHandler:
            pass

        result = controller.remove_handler(NonExistentHandler)

        assert result is False


class TestCLIControllerUtilityMethods:
    """Test utility and helper methods."""

    def test_set_debug_mode(self, monkeypatch):
        """Test setting debug mode."""
        controller = create_mock_cli_controller(monkeypatch)

        assert controller.debug_mode is False

        controller.set_debug_mode(True)
        assert controller.debug_mode is True

        controller.set_debug_mode(False)
        assert controller.debug_mode is False

    def test_get_session_context(self, monkeypatch):
        """Test getting session context."""
        controller = create_mock_cli_controller(monkeypatch)

        context = controller.get_session_context()

        assert context == {"username": "testuser", "cwd": "/test"}

    def test_force_context_refresh(self, monkeypatch):
        """Test forcing context refresh."""
        controller = create_mock_cli_controller(monkeypatch)

        # Should not raise any errors
        controller.force_context_refresh()

    def test_string_representation(self, monkeypatch):
        """Test __str__ method."""
        controller = create_mock_cli_controller(monkeypatch)

        str_repr = str(controller)

        assert "CLIController" in str_repr
        assert "running=False" in str_repr
        assert "testuser" in str_repr

    def test_detailed_representation(self, monkeypatch):
        """Test __repr__ method."""
        controller = create_mock_cli_controller(monkeypatch)

        repr_str = repr(controller)

        assert "CLIController" in repr_str
        assert "running=False" in repr_str
        assert "handlers=3" in repr_str
        assert "commands_processed=0" in repr_str


class TestCreateCLIControllerFactory:
    """Test the factory function for creating CLI controllers."""

    def test_create_cli_controller_success(self, mock_agent, console, monkeypatch):
        """Test successful CLI controller creation via factory."""
        # Mock all dependencies
        monkeypatch.setattr(
            "ifw.cli.controller.SessionManager", mock_session_manager_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandExecutor", mock_shell_executor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory
        )

        controller = create_cli_controller(
            agent=mock_agent, console=console, debug_mode=True
        )

        assert isinstance(controller, CLIController)
        assert controller.agent == mock_agent
        assert controller.console == console
        assert controller.debug_mode is True

    def test_create_cli_controller_with_defaults(self, mock_agent, monkeypatch):
        """Test factory with default parameters."""
        # Mock all dependencies
        monkeypatch.setattr(
            "ifw.cli.controller.SessionManager", mock_session_manager_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandExecutor", mock_shell_executor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory
        )

        controller = create_cli_controller(agent=mock_agent)

        assert isinstance(controller, CLIController)
        assert controller.agent == mock_agent
        assert controller.debug_mode is False

    def test_create_cli_controller_initialization_failure(
        self, mock_agent, console, monkeypatch
    ):
        """Test factory when initialization fails."""

        def failing_shell_executor():
            raise Exception("Initialization failed")

        # Mock dependencies with one failing
        monkeypatch.setattr(
            "ifw.cli.controller.SessionManager", mock_session_manager_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.CommandProcessor", mock_command_processor_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandExecutor", failing_shell_executor
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandDetector", mock_shell_detector_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ControlCommandHandler", mock_control_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.ShellCommandHandler", mock_shell_handler_factory
        )
        monkeypatch.setattr(
            "ifw.cli.controller.AIRequestHandler", mock_ai_handler_factory
        )

        with pytest.raises(CLIInitializationError):
            create_cli_controller(agent=mock_agent, console=console)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
