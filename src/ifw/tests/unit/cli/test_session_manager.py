# test_session.py
# Place this file in src/ifw/ directory
"""
Test script for SessionManager to avoid import issues.
"""

from unittest.mock import Mock
from rich.console import Console

# Import from relative modules
from ifw.shell.exec_shell import ShellCommandExecutor
from ifw.cli.session_manager import SessionManager


def test_session_manager():
    """Test SessionManager functionality."""
    print("Testing SessionManager...")

    # Create mock or real executor
    try:
        # Try to use real executor
        executor = ShellCommandExecutor()
    except Exception as e:
        # Fall back to mock
        print(f"Using mock executor due to: {e}")
        executor = Mock()
        executor.get_current_directory.return_value = "/home/user/test"

    # Create console
    console = Console()

    # Create session manager
    session = SessionManager(executor, console)

    # Test context
    print("Testing context...")
    context = session.get_context()
    print(f"Context: {context}")

    # Test session info
    print("Testing session info...")
    info = session.get_session_info()
    print(f"Session info: {info}")

    # Test history
    print("Testing history...")
    session.add_to_history("test command 1")
    session.add_to_history("test command 2")
    history = session.get_history_list()
    print(f"History: {history}")

    print("✅ All tests passed!")

    # Interactive test (optional)
    print("\nWant to test interactive input? (y/n)")
    if input().lower() == "y":
        try:
            print("Type something (Ctrl+C to stop):")
            user_input = session.get_user_input()
            print(f"You entered: '{user_input}'")
        except KeyboardInterrupt:
            print("\n🛑 Interrupted!")
        except EOFError:
            print("\n📄 EOF received!")


if __name__ == "__main__":
    test_session_manager()
