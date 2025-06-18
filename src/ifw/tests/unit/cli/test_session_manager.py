"""
Comprehensive unit test suite for SessionManager class.
Uses pure pytest - tests session management, prompts, and context handling.
"""

import pytest
from rich.console import Console
from io import StringIO

# Import the classes to test
from ifw.cli.session_manager import SessionManager
from ifw.utils.exceptions import SessionError


class MockShellExecutor:
    """Mock shell executor for testing."""

    def __init__(self):
        self.current_directory = "/home/testuser"
        self.commands_executed = []

    def get_current_directory(self):
        return self.current_directory

    def set_current_directory(self, path):
        self.current_directory = path

    def execute_shell_command(self, command):
        self.commands_executed.append(command)
        return f"Output of: {command}"


class MockSmartCompleter:
    """Mock smart completer for testing."""

    def __init__(self, shell_executor=None):
        self.shell_executor = shell_executor
        self.completions = []

    def get_completions(self, document, complete_event):
        return self.completions

    def add_completion(self, completion):
        self.completions.append(completion)


class MockInMemoryHistory:
    """Mock in-memory history for testing."""

    def __init__(self):
        self.commands = []

    def append_string(self, command):
        self.commands.append(command)

    def get_strings(self):
        return self.commands.copy()


def mock_getuser():
    """Mock getpass.getuser function."""
    return "testuser"


def mock_gethostname():
    """Mock socket.gethostname function."""
    return "testhost"


def mock_prompt(prompt_text, **kwargs):
    """Mock prompt_toolkit.prompt function."""
    # Store the kwargs for verification in tests
    mock_prompt.last_call_kwargs = kwargs
    mock_prompt.last_prompt_text = prompt_text

    # Return predefined input or raise exception
    if hasattr(mock_prompt, "return_value"):
        result = mock_prompt.return_value
        # Reset for next call
        delattr(mock_prompt, "return_value")
        return result
    elif hasattr(mock_prompt, "raise_exception"):
        exception = mock_prompt.raise_exception
        # Reset for next call
        delattr(mock_prompt, "raise_exception")
        raise exception
    else:
        return "test command"


# Fixtures
@pytest.fixture
def mock_shell_executor():
    """Provide a mock shell executor."""
    return MockShellExecutor()


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
def session_manager(mock_shell_executor, console, monkeypatch):
    """Provide a SessionManager with mocked dependencies."""
    # Mock external dependencies
    monkeypatch.setattr("ifw.cli.session_manager.InMemoryHistory", MockInMemoryHistory)
    monkeypatch.setattr("ifw.cli.session_manager.SmartCompleter", MockSmartCompleter)
    monkeypatch.setattr("getpass.getuser", mock_getuser)
    monkeypatch.setattr("socket.gethostname", mock_gethostname)
    monkeypatch.setattr("ifw.cli.session_manager.prompt", mock_prompt)

    return SessionManager(mock_shell_executor, console)


class TestSessionManagerInitialization:
    """Test SessionManager initialization."""

    def test_successful_initialization(self, mock_shell_executor, console, monkeypatch):
        """Test successful SessionManager initialization."""
        # Mock dependencies
        monkeypatch.setattr(
            "ifw.cli.session_manager.InMemoryHistory", MockInMemoryHistory
        )
        monkeypatch.setattr(
            "ifw.cli.session_manager.SmartCompleter", MockSmartCompleter
        )

        manager = SessionManager(mock_shell_executor, console)

        assert manager.shell_executor == mock_shell_executor
        assert manager.console == console
        assert isinstance(manager.history, MockInMemoryHistory)
        assert isinstance(manager.smart_completer, MockSmartCompleter)
        assert manager._context_cache is None
        assert manager._context_cache_valid is True

    def test_initialization_creates_smart_completer_with_shell_executor(
        self, mock_shell_executor, console, monkeypatch
    ):
        """Test that SmartCompleter is initialized with shell executor."""
        mock_completer_class = MockSmartCompleter
        monkeypatch.setattr(
            "ifw.cli.session_manager.InMemoryHistory", MockInMemoryHistory
        )
        monkeypatch.setattr(
            "ifw.cli.session_manager.SmartCompleter", mock_completer_class
        )

        manager = SessionManager(mock_shell_executor, console)

        assert manager.smart_completer.shell_executor == mock_shell_executor


class TestSessionManagerUserInput:
    """Test user input functionality."""

    def test_get_user_input_success(self, session_manager, monkeypatch):
        """Test successful user input."""
        # Set up mock prompt to return specific input
        mock_prompt.return_value = "test command"

        result = session_manager.get_user_input()

        assert result == "test command"
        assert not session_manager._context_cache_valid  # Cache should be invalidated

    def test_get_user_input_with_formatted_prompt(self, session_manager, monkeypatch):
        """Test that prompt is formatted correctly."""
        mock_prompt.return_value = "test"

        session_manager.get_user_input()

        # Check that prompt was called with correct parameters
        assert hasattr(mock_prompt, "last_call_kwargs")
        kwargs = mock_prompt.last_call_kwargs

        assert "completer" in kwargs
        assert "history" in kwargs
        assert "complete_style" in kwargs
        assert "enable_history_search" in kwargs
        assert "complete_while_typing" in kwargs
        assert kwargs["enable_history_search"] is True
        assert kwargs["complete_while_typing"] is False

    def test_get_user_input_keyboard_interrupt(self, session_manager):
        """Test that KeyboardInterrupt is properly propagated."""
        mock_prompt.raise_exception = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            session_manager.get_user_input()

    def test_get_user_input_eof_error(self, session_manager):
        """Test that EOFError is properly propagated."""
        mock_prompt.raise_exception = EOFError()

        with pytest.raises(EOFError):
            session_manager.get_user_input()

    def test_get_user_input_unexpected_error(self, session_manager):
        """Test that unexpected errors are wrapped in SessionError."""
        mock_prompt.raise_exception = RuntimeError("Unexpected error")

        with pytest.raises(SessionError) as exc_info:
            session_manager.get_user_input()

        assert "Failed to get user input" in str(exc_info.value)
        assert "Unexpected error" in str(exc_info.value)


class TestSessionManagerContext:
    """Test context management functionality."""

    def test_get_context_success(self, session_manager):
        """Test successful context retrieval."""
        context = session_manager.get_context()

        expected_context = {
            "username": "testuser",
            "hostname": "testhost",
            "cwd": "/home/testuser",
        }
        assert context == expected_context
        assert session_manager._context_cache == expected_context
        assert session_manager._context_cache_valid is True

    def test_get_context_uses_cache(self, session_manager, monkeypatch):
        """Test that context uses cache when valid."""
        # First call to populate cache
        context1 = session_manager.get_context()

        # Mock functions to return different values
        monkeypatch.setattr("getpass.getuser", lambda: "different_user")
        monkeypatch.setattr("socket.gethostname", lambda: "different_host")
        session_manager.shell_executor.set_current_directory("/different/path")

        # Second call should use cache
        context2 = session_manager.get_context()

        assert context1 == context2  # Should be the same due to cache
        assert context2["username"] == "testuser"  # Original cached value

    def test_get_context_after_cache_invalidation(self, session_manager, monkeypatch):
        """Test context refresh after cache invalidation."""
        # First call to populate cache
        context1 = session_manager.get_context()

        # Invalidate cache
        session_manager._invalidate_context_cache()

        # Mock functions to return different values
        monkeypatch.setattr("getpass.getuser", lambda: "new_user")
        monkeypatch.setattr("socket.gethostname", lambda: "new_host")
        session_manager.shell_executor.set_current_directory("/new/path")

        # Second call should get fresh values
        context2 = session_manager.get_context()

        assert context1 != context2
        assert context2["username"] == "new_user"
        assert context2["hostname"] == "new_host"
        assert context2["cwd"] == "/new/path"

    def test_get_context_with_system_error(
        self, session_manager, monkeypatch, string_console
    ):
        """Test context fallback when system calls fail."""
        session_manager.console = string_console

        # Mock functions to raise errors
        monkeypatch.setattr(
            "getpass.getuser", lambda: exec('raise OSError("User error")')
        )

        context = session_manager.get_context()

        # Should return fallback values
        expected_fallback = {"username": "user", "hostname": "localhost", "cwd": "~"}
        assert context == expected_fallback

        # Should not cache fallback values
        assert session_manager._context_cache != expected_fallback

    def test_force_context_refresh(self, session_manager, monkeypatch):
        """Test force context refresh functionality."""
        # First call to populate cache
        context1 = session_manager.get_context()
        assert session_manager._context_cache_valid is True

        # Change underlying values
        monkeypatch.setattr("getpass.getuser", lambda: "refreshed_user")
        session_manager.shell_executor.set_current_directory("/refreshed/path")

        # Force refresh
        session_manager.force_context_refresh()

        # Cache should be refreshed with new values
        assert session_manager._context_cache_valid is True
        context2 = session_manager.get_context()

        assert context2["username"] == "refreshed_user"
        assert context2["cwd"] == "/refreshed/path"
        assert context1 != context2


class TestSessionManagerHistory:
    """Test history management functionality."""

    def test_get_history_list_empty(self, session_manager):
        """Test getting history when empty."""
        history = session_manager.get_history_list()
        assert history == []

    def test_get_history_list_with_commands(self, session_manager):
        """Test getting history with commands."""
        # Add some commands to history
        session_manager.history.append_string("command1")
        session_manager.history.append_string("command2")
        session_manager.history.append_string("command3")

        history = session_manager.get_history_list()
        assert history == ["command1", "command2", "command3"]

    def test_history_persistence_across_calls(self, session_manager):
        """Test that history persists across multiple calls."""
        session_manager.history.append_string("persistent_command")

        history1 = session_manager.get_history_list()
        history2 = session_manager.get_history_list()

        assert history1 == history2
        assert "persistent_command" in history1


class TestSessionManagerCacheManagement:
    """Test cache management functionality."""

    def test_invalidate_context_cache(self, session_manager):
        """Test context cache invalidation."""
        # Populate cache first
        session_manager.get_context()
        assert session_manager._context_cache_valid is True

        # Invalidate cache
        session_manager._invalidate_context_cache()
        assert session_manager._context_cache_valid is False

    def test_cache_invalidation_after_user_input(self, session_manager):
        """Test that cache is invalidated after user input."""
        # Populate cache
        session_manager.get_context()
        assert session_manager._context_cache_valid is True

        # Get user input (should invalidate cache)
        mock_prompt.return_value = "test"
        session_manager.get_user_input()

        assert session_manager._context_cache_valid is False


class TestSessionManagerSessionInfo:
    """Test session information functionality."""

    def test_get_session_info(self, session_manager):
        """Test getting comprehensive session information."""
        # Add some history
        session_manager.history.append_string("test1")
        session_manager.history.append_string("test2")

        session_info = session_manager.get_session_info()

        assert "context" in session_info
        assert "history_commands" in session_info
        assert "completer_active" in session_info
        assert "cache_valid" in session_info

        # Check specific values
        assert session_info["history_commands"] == 2
        assert session_info["completer_active"] is True
        assert session_info["cache_valid"] is True

        # Check context structure
        context = session_info["context"]
        assert "username" in context
        assert "hostname" in context
        assert "cwd" in context

    def test_get_session_info_with_invalid_cache(self, session_manager):
        """Test session info when cache is invalid."""
        session_manager._invalidate_context_cache()

        session_info = session_manager.get_session_info()

        # Cache should be valid after get_session_info call (it calls get_context)
        assert session_info["cache_valid"] is True

    def test_get_session_info_without_completer(self, session_manager):
        """Test session info when completer is None."""
        session_manager.smart_completer = None

        session_info = session_manager.get_session_info()

        assert session_info["completer_active"] is False


class TestSessionManagerCompletionMode:
    """Test completion mode functionality."""

    def test_set_completion_mode_real_time_true(self, session_manager):
        """Test setting completion mode to real-time."""
        session_manager.set_completion_mode(real_time=True)

        # Check that preference is stored
        assert hasattr(session_manager, "_real_time_completion")
        assert session_manager._real_time_completion is True

    def test_set_completion_mode_real_time_false(self, session_manager):
        """Test setting completion mode to non-real-time."""
        session_manager.set_completion_mode(real_time=False)

        # Check that preference is stored
        assert hasattr(session_manager, "_real_time_completion")
        assert session_manager._real_time_completion is False

    def test_set_completion_mode_default(self, session_manager):
        """Test setting completion mode with default parameter."""
        session_manager.set_completion_mode()

        # Default should be False
        assert hasattr(session_manager, "_real_time_completion")
        assert session_manager._real_time_completion is False


class TestSessionManagerEdgeCases:
    """Test edge cases and error conditions."""

    def test_context_with_shell_executor_error(
        self, session_manager, monkeypatch, string_console
    ):
        """Test context handling when shell executor fails."""
        session_manager.console = string_console

        # Mock shell executor to raise error
        def failing_get_directory():
            raise RuntimeError("Shell executor failed")

        session_manager.shell_executor.get_current_directory = failing_get_directory

        context = session_manager.get_context()

        # Should return fallback values
        assert context["username"] == "user"
        assert context["hostname"] == "localhost"
        assert context["cwd"] == "~"

    def test_multiple_context_errors(
        self, session_manager, monkeypatch, string_console
    ):
        """Test context handling when multiple system calls fail."""
        session_manager.console = string_console

        # Mock all system calls to fail
        monkeypatch.setattr(
            "getpass.getuser", lambda: exec('raise OSError("User failed")')
        )
        monkeypatch.setattr(
            "socket.gethostname", lambda: exec('raise OSError("Hostname failed")')
        )
        session_manager.shell_executor.get_current_directory = lambda: exec(
            'raise OSError("Directory failed")'
        )

        context = session_manager.get_context()

        # Should return complete fallback
        expected_fallback = {"username": "user", "hostname": "localhost", "cwd": "~"}
        assert context == expected_fallback

    def test_prompt_with_empty_context(self, session_manager, monkeypatch):
        """Test prompt creation with minimal context."""

        # Mock to return minimal context
        def minimal_context():
            return {"username": "", "hostname": "", "cwd": ""}

        monkeypatch.setattr(session_manager, "get_context", minimal_context)
        mock_prompt.return_value = "test"

        result = session_manager.get_user_input()

        assert result == "test"
        # Should not raise any errors with empty context values


class TestSessionManagerIntegration:
    """Test integration scenarios."""

    def test_full_session_workflow(self, session_manager):
        """Test a complete session workflow."""
        # Initial state
        assert session_manager.get_history_list() == []

        # Get context (populates cache)
        context = session_manager.get_context()
        assert context["username"] == "testuser"
        assert session_manager._context_cache_valid is True

        # Simulate user input (invalidates cache)
        mock_prompt.return_value = "ls -la"
        user_input = session_manager.get_user_input()
        assert user_input == "ls -la"
        assert session_manager._context_cache_valid is False

        # Get session info
        session_info = session_manager.get_session_info()
        assert session_info["cache_valid"] is True  # Refreshed by get_session_info
        assert session_info["completer_active"] is True

    def test_cache_behavior_across_operations(self, session_manager, monkeypatch):
        """Test cache behavior across multiple operations."""
        # Initial context
        context1 = session_manager.get_context()
        assert session_manager._context_cache_valid is True

        # Change directory via shell executor
        session_manager.shell_executor.set_current_directory("/new/directory")

        # Context should still be cached (stale)
        context2 = session_manager.get_context()
        assert context1 == context2  # Still using cache

        # Simulate user input (invalidates cache)
        mock_prompt.return_value = "cd /new/directory"
        session_manager.get_user_input()

        # Now context should be fresh
        context3 = session_manager.get_context()
        assert context3["cwd"] == "/new/directory"
        assert context1 != context3

    def test_error_recovery(self, session_manager, monkeypatch, string_console):
        """Test error recovery in various scenarios."""
        session_manager.console = string_console

        # Test recovery from context error
        monkeypatch.setattr(
            "getpass.getuser", lambda: exec('raise OSError("Temporary error")')
        )
        context = session_manager.get_context()
        assert context["username"] == "user"  # Fallback

        # Test that subsequent operations still work
        mock_prompt.return_value = "test command"
        user_input = session_manager.get_user_input()
        assert user_input == "test command"

        # Test session info still works
        session_info = session_manager.get_session_info()
        assert "context" in session_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
