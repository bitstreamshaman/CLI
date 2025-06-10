#!/usr/bin/env python3
"""
Unit tests for CommandProcessor using proper unittest framework and Mock.
"""
import sys
import os
import unittest
from unittest.mock import Mock
from rich.console import Console

# Add current directory to Python path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the components to test
from ifw.cli.command_processor import CommandProcessor, CommandProcessingError, NoHandlerFoundError


class TestCommandProcessor(unittest.TestCase):
    """Test suite for CommandProcessor class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.console = Console()
        self.control_handler = self._create_control_handler_mock()
        self.shell_handler = self._create_shell_handler_mock()
        self.ai_handler = self._create_ai_handler_mock()
        self.handlers = [self.control_handler, self.shell_handler, self.ai_handler]
        self.processor = CommandProcessor(self.handlers, self.console)
    
    def _create_control_handler_mock(self):
        """Create a mock control handler."""
        handler = Mock()
        # Set class name for handler identification
        handler.__class__ = Mock()
        handler.__class__.__name__ = "ControlCommandHandler"
        # Configure behavior
        handler.can_handle.side_effect = lambda x: x.lower().strip() in ["exit", "clear"]
        handler.handle.return_value = True
        return handler
    
    def _create_shell_handler_mock(self):
        """Create a mock shell handler."""
        handler = Mock()
        # Set class name for handler identification
        handler.__class__ = Mock()
        handler.__class__.__name__ = "ShellCommandHandler"
        # Configure behavior
        handler.can_handle.side_effect = lambda x: any(x.startswith(cmd) for cmd in ["ls", "cd", "pwd", "echo", "cat", "grep"])
        handler.handle.return_value = True
        return handler
    
    def _create_ai_handler_mock(self):
        """Create a mock AI handler (fallback)."""
        handler = Mock()
        # Set class name for handler identification
        handler.__class__ = Mock()
        handler.__class__.__name__ = "AIRequestHandler"
        # Configure behavior
        handler.can_handle.return_value = True  # Always handles (fallback)
        handler.handle.return_value = True
        return handler
    
    def test_processor_initialization(self):
        """Test CommandProcessor initialization."""
        self.assertEqual(len(self.processor.handlers), 3)
        self.assertEqual(self.processor.commands_processed, 0)
        self.assertEqual(self.processor.successful_commands, 0)
        self.assertEqual(self.processor.failed_commands, 0)
    
    def test_list_handlers(self):
        """Test handler listing functionality."""
        handler_names = self.processor.list_handlers()
        expected_names = ["ControlCommandHandler", "ShellCommandHandler", "AIRequestHandler"]
        self.assertEqual(handler_names, expected_names)
    
    def test_command_routing_control_commands(self):
        """Test routing of control commands."""
        test_cases = [
            ("exit", "ControlCommandHandler"),
            ("clear", "ControlCommandHandler"),
        ]
        
        for command, expected_handler in test_cases:
            with self.subTest(command=command):
                handler = self.processor.get_handler_for_input(command)
                self.assertEqual(handler.__class__.__name__, expected_handler)
    
    def test_command_routing_shell_commands(self):
        """Test routing of shell commands."""
        test_cases = [
            ("ls -la", "ShellCommandHandler"),
            ("cd /home", "ShellCommandHandler"),
            ("pwd", "ShellCommandHandler"),
            ("echo hello", "ShellCommandHandler"),
        ]
        
        for command, expected_handler in test_cases:
            with self.subTest(command=command):
                handler = self.processor.get_handler_for_input(command)
                self.assertEqual(handler.__class__.__name__, expected_handler)
    
    def test_command_routing_ai_commands(self):
        """Test routing of AI commands (fallback)."""
        test_cases = [
            ("help me with AWS", "AIRequestHandler"),
            ("what is kubernetes", "AIRequestHandler"),
            ("random input", "AIRequestHandler"),
            ("how to deploy docker", "AIRequestHandler"),
        ]
        
        for command, expected_handler in test_cases:
            with self.subTest(command=command):
                handler = self.processor.get_handler_for_input(command)
                self.assertEqual(handler.__class__.__name__, expected_handler)
    
    def test_successful_command_execution(self):
        """Test successful command execution."""
        test_commands = [
            "exit",           # Control
            "ls -la",         # Shell
            "help with cloud" # AI
        ]
        
        for command in test_commands:
            with self.subTest(command=command):
                result = self.processor.process_command(command)
                self.assertTrue(result)
        
        # Check statistics
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['total_commands'], 3)
        self.assertEqual(stats['successful_commands'], 3)
        self.assertEqual(stats['failed_commands'], 0)
        self.assertEqual(stats['success_rate'], 100.0)
    
    def test_empty_command_handling(self):
        """Test handling of empty commands."""
        # Empty string should return False and not be processed
        result = self.processor.process_command("")
        self.assertFalse(result)
        
        # Whitespace-only should return True (handled gracefully)
        result = self.processor.process_command("   ")
        self.assertTrue(result)
    
    def test_invalid_input_handling(self):
        """Test handling of invalid input."""
        test_cases = [None, 123, [], {}]
        
        for invalid_input in test_cases:
            with self.subTest(input=invalid_input):
                result = self.processor.process_command(invalid_input)
                self.assertFalse(result)
    
    def test_handler_execution_error(self):
        """Test handling of handler execution errors."""
        # Create a handler that throws an error during execution
        error_handler = Mock()
        error_handler.__class__ = Mock()
        error_handler.__class__.__name__ = "ErrorHandler"
        error_handler.can_handle.return_value = True
        error_handler.handle.side_effect = Exception("Simulated handler error")
        
        error_processor = CommandProcessor([error_handler], self.console)
        
        with self.assertRaises(CommandProcessingError) as context:
            error_processor.process_command("test error")
        
        self.assertIn("Simulated handler error", str(context.exception))
    
    def test_no_handler_found_error(self):
        """Test NoHandlerFoundError when no handler can process command."""
        # Create handlers that never match
        no_match_handler1 = Mock()
        no_match_handler1.__class__ = Mock()
        no_match_handler1.__class__.__name__ = "NoMatchHandler1"
        no_match_handler1.can_handle.return_value = False
        
        no_match_handler2 = Mock()
        no_match_handler2.__class__ = Mock()
        no_match_handler2.__class__.__name__ = "NoMatchHandler2"
        no_match_handler2.can_handle.return_value = False
        
        no_handler_processor = CommandProcessor([no_match_handler1, no_match_handler2], self.console)
        
        with self.assertRaises(NoHandlerFoundError) as context:
            no_handler_processor.process_command("unhandleable command")
        
        self.assertIn("No handler found", str(context.exception))
    
    def test_handler_selection_error_graceful_handling(self):
        """Test graceful handling when handler.can_handle() throws an exception."""
        # Create a handler that throws error during can_handle()
        broken_handler = Mock()
        broken_handler.__class__ = Mock()
        broken_handler.__class__.__name__ = "BrokenHandler"
        broken_handler.can_handle.side_effect = Exception("can_handle() error")
        
        # Create a working fallback handler
        fallback_handler = Mock()
        fallback_handler.__class__ = Mock()
        fallback_handler.__class__.__name__ = "FallbackHandler"
        fallback_handler.can_handle.return_value = True
        fallback_handler.handle.return_value = True
        
        processor = CommandProcessor([broken_handler, fallback_handler], self.console)
        
        # Should gracefully skip broken handler and use fallback
        result = processor.process_command("test command")
        self.assertTrue(result)
        
        # Verify fallback handler was called
        fallback_handler.handle.assert_called_once_with("test command")
    
    def test_handler_management_add_handler(self):
        """Test adding handlers to the processor."""
        initial_count = len(self.processor.handlers)
        
        new_handler = Mock()
        new_handler.__class__ = Mock()
        new_handler.__class__.__name__ = "NewTestHandler"
        
        self.processor.add_handler(new_handler)
        
        self.assertEqual(len(self.processor.handlers), initial_count + 1)
        self.assertIn("NewTestHandler", self.processor.list_handlers())
    
    def test_handler_management_remove_handler(self):
        """Test removing handlers from the processor."""
        # Add a handler first
        test_handler = Mock()
        test_handler.__class__ = Mock()
        test_handler.__class__.__name__ = "TestHandler"
        self.processor.add_handler(test_handler)
        
        initial_count = len(self.processor.handlers)
        
        # Remove the handler by class type
        removed = self.processor.remove_handler(type(test_handler))
        
        self.assertTrue(removed)
        self.assertEqual(len(self.processor.handlers), initial_count - 1)
        self.assertNotIn("TestHandler", self.processor.list_handlers())
    
    def test_handler_management_remove_nonexistent_handler(self):
        """Test removing a handler that doesn't exist."""
        class NonExistentHandler:
            pass
        
        removed = self.processor.remove_handler(NonExistentHandler)
        self.assertFalse(removed)
    
    def test_processing_statistics(self):
        """Test processing statistics tracking."""
        # Process some commands
        self.processor.process_command("exit")  # Success
        self.processor.process_command("ls")    # Success
        
        # Create a failing handler for failed command test
        failing_handler = Mock()
        failing_handler.__class__ = Mock()
        failing_handler.__class__.__name__ = "FailingHandler"
        failing_handler.can_handle.return_value = True
        failing_handler.handle.return_value = False  # Returns False (failure)
        
        failing_processor = CommandProcessor([failing_handler], self.console)
        failing_processor.process_command("failing command")
        
        # Check original processor stats
        stats = self.processor.get_processing_stats()
        self.assertEqual(stats['total_commands'], 2)
        self.assertEqual(stats['successful_commands'], 2)
        self.assertEqual(stats['failed_commands'], 0)
        self.assertEqual(stats['success_rate'], 100.0)
        
        # Check failing processor stats
        failing_stats = failing_processor.get_processing_stats()
        self.assertEqual(failing_stats['total_commands'], 1)
        self.assertEqual(failing_stats['successful_commands'], 0)
        self.assertEqual(failing_stats['failed_commands'], 1)
        self.assertEqual(failing_stats['success_rate'], 0.0)
    
    def test_reset_statistics(self):
        """Test statistics reset functionality."""
        # Process some commands
        self.processor.process_command("exit")
        self.processor.process_command("ls")
        
        # Verify stats exist
        stats_before = self.processor.get_processing_stats()
        self.assertEqual(stats_before['total_commands'], 2)
        
        # Reset stats
        self.processor.reset_stats()
        
        # Verify stats are reset
        stats_after = self.processor.get_processing_stats()
        self.assertEqual(stats_after['total_commands'], 0)
        self.assertEqual(stats_after['successful_commands'], 0)
        self.assertEqual(stats_after['failed_commands'], 0)
        self.assertEqual(stats_after['success_rate'], 0.0)
    
    def test_test_routing_method(self):
        """Test the test_routing method for debugging."""
        test_commands = [
            "exit",
            "ls -la", 
            "help me"
        ]
        
        routing_results = self.processor.test_routing(test_commands)
        
        expected_results = {
            "exit": "ControlCommandHandler",
            "ls -la": "ShellCommandHandler",
            "help me": "AIRequestHandler"
        }
        
        self.assertEqual(routing_results, expected_results)
    
    def test_string_representations(self):
        """Test string representation methods."""
        str_repr = str(self.processor)
        self.assertIn("CommandProcessor", str_repr)
        
        repr_str = repr(self.processor)
        self.assertIn("CommandProcessor", repr_str)
        self.assertIn("handlers=3", repr_str)


class TestCommandProcessorIntegration(unittest.TestCase):
    """Integration tests with more realistic handler behavior."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.console = Console()
        
        # Create more realistic mock handlers
        self.control_handler = Mock()
        self.control_handler.__class__ = Mock()
        self.control_handler.__class__.__name__ = "ControlCommandHandler"
        self.control_handler.can_handle.side_effect = lambda x: x.strip().lower() in ["exit", "clear"]
        self.control_handler.handle.side_effect = self._realistic_control_handler
        
        self.shell_handler = Mock()
        self.shell_handler.__class__ = Mock()
        self.shell_handler.__class__.__name__ = "ShellCommandHandler"
        self.shell_handler.can_handle.side_effect = lambda x: x.startswith(("ls", "cd", "pwd"))
        self.shell_handler.handle.side_effect = self._realistic_shell_handler
        
        self.ai_handler = Mock()
        self.ai_handler.__class__ = Mock()
        self.ai_handler.__class__.__name__ = "AIRequestHandler"
        self.ai_handler.can_handle.return_value = True
        self.ai_handler.handle.side_effect = self._realistic_ai_handler
        
        self.processor = CommandProcessor([self.control_handler, self.shell_handler, self.ai_handler], self.console)
    
    def _realistic_control_handler(self, command):
        """Realistic control handler behavior."""
        if command == "exit":
            # Don't actually exit in test
            return True
        elif command == "clear":
            return True
        return False
    
    def _realistic_shell_handler(self, command):
        """Realistic shell handler behavior."""
        # Success if command has parts and is recognized
        return len(command.split()) > 0 and command.startswith(("ls", "cd", "pwd"))
    
    def _realistic_ai_handler(self, command):
        """Realistic AI handler behavior."""
        # Success if not empty
        return len(command.strip()) > 0
    
    def test_realistic_command_scenarios(self):
        """Test realistic command processing scenarios."""
        scenarios = [
            ("clear", True, "Control command should succeed"),
            ("ls", True, "Shell command should succeed"),
            ("help me", True, "AI request should succeed"),
            ("", False, "Empty command should be handled gracefully"),
            ("   ", True, "Whitespace command should be handled gracefully"),
        ]
        
        for command, expected, description in scenarios:
            with self.subTest(command=command, description=description):
                try:
                    result = self.processor.process_command(command)
                    self.assertEqual(result, expected, f"{description}: expected {expected}, got {result}")
                except Exception as e:
                    self.fail(f"{description}: Unexpected exception - {e}")
    
    def test_handler_priority_order(self):
        """Test that handlers are checked in the correct priority order."""
        # Command that could match multiple handlers
        # "cd" should go to shell handler, not AI handler (even though AI can handle everything)
        handler = self.processor.get_handler_for_input("cd /home")
        self.assertEqual(handler.__class__.__name__, "ShellCommandHandler")
        
        # Control commands should go to control handler first
        handler = self.processor.get_handler_for_input("exit")
        self.assertEqual(handler.__class__.__name__, "ControlCommandHandler")
    
    def test_comprehensive_statistics(self):
        """Test comprehensive statistics across multiple command types."""
        commands = ["exit", "ls", "help", "", "cd /home", "invalid", "clear"]
        
        for command in commands:
            try:
                self.processor.process_command(command)
            except Exception:
                pass  # Some commands might fail, that's okay for stats testing
        
        stats = self.processor.get_processing_stats()
        
        # Verify stats structure
        self.assertIn('total_commands', stats)
        self.assertIn('successful_commands', stats)
        self.assertIn('failed_commands', stats)
        self.assertIn('success_rate', stats)
        self.assertIn('handler_stats', stats)
        
        # Verify handler stats exist for each handler
        for handler_name in ["ControlCommandHandler", "ShellCommandHandler", "AIRequestHandler"]:
            self.assertIn(handler_name, stats['handler_stats'])
    
    def test_mock_call_verification(self):
        """Test that mocks are called correctly."""
        # Process a control command
        self.processor.process_command("exit")
        
        # Verify the control handler was called
        self.control_handler.can_handle.assert_called_with("exit")
        self.control_handler.handle.assert_called_with("exit")
        
        # Verify other handlers weren't called for handling (but may have been called for can_handle)
        self.shell_handler.handle.assert_not_called()
        self.ai_handler.handle.assert_not_called()


def run_tests():
    """Run all tests with detailed output."""
    # Create test loader
    loader = unittest.TestLoader()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases using modern approach
    test_suite.addTests(loader.loadTestsFromTestCase(TestCommandProcessor))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCommandProcessorIntegration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"🧪 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    if result.wasSuccessful():
        print(f"\n✅ All tests passed!")
    else:
        print(f"\n⚠️  Some tests failed!")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Alternative: Use unittest.main() for simpler execution
    # unittest.main(verbosity=2, exit=False)
    
    success = run_tests()