#!/usr/bin/env python3
"""
Test script for CLI Controller.
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch
from io import StringIO
from rich.console import Console

# Add current directory to Python path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import the CLI controller
from ifw.cli.controller import CLIController, CLIInitializationError, create_cli_controller


class TestCLIController(unittest.TestCase):
    """Test suite for CLI Controller."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock agent
        self.mock_agent = Mock()
        self.mock_agent.side_effect = lambda x: f"AI response to: {x}"
        
        # Create console that captures output
        self.test_console = Console(file=StringIO(), width=80)
        
        # Mock the shell components to avoid file system dependencies
        self.shell_executor_patcher = patch('ifw.cli.controller.ShellCommandExecutor')
        self.shell_detector_patcher = patch('ifw.cli.controller.ShellCommandDetector')
        
        self.mock_shell_executor = self.shell_executor_patcher.start()
        self.mock_shell_detector = self.shell_detector_patcher.start()
        
        # Configure shell executor mock
        self.mock_shell_executor.return_value.get_current_directory.return_value = "/test/dir"
        self.mock_shell_executor.return_value.interrupt_current_command.return_value = False
        
        # Configure shell detector mock
        self.mock_shell_detector.return_value.is_shell_command.side_effect = lambda x: x.startswith(("ls", "cd", "pwd"))
    
    def tearDown(self):
        """Clean up after tests."""
        self.shell_executor_patcher.stop()
        self.shell_detector_patcher.stop()
    
    def test_cli_controller_initialization(self):
        """Test CLI controller initialization."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console)
        
        self.assertIsNotNone(cli.session_manager)
        self.assertIsNotNone(cli.command_processor)
        self.assertEqual(len(cli.handlers), 3)  # control, shell, ai
        self.assertFalse(cli.running)
        self.assertFalse(cli.exit_requested)
    
    def test_cli_controller_initialization_without_agent(self):
        """Test CLI controller initialization without agent."""
        cli = CLIController(console=self.test_console)
        
        # Should still initialize but agent will be None
        self.assertIsNotNone(cli.session_manager)
        self.assertIsNotNone(cli.command_processor)
        self.assertIsNone(cli.agent)
    
    def test_factory_function(self):
        """Test factory function for creating CLI controller."""
        cli = create_cli_controller(agent=self.mock_agent, console=self.test_console)
        
        self.assertIsInstance(cli, CLIController)
        self.assertEqual(cli.agent, self.mock_agent)
        self.assertEqual(cli.console, self.test_console)
    
    def test_handler_management(self):
        """Test adding and removing handlers."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console)
        
        initial_count = len(cli.handlers)
        
        # Add a mock handler
        mock_handler = Mock()
        mock_handler.__class__ = Mock()
        mock_handler.__class__.__name__ = "TestHandler"
        
        cli.add_handler(mock_handler)
        self.assertEqual(len(cli.handlers), initial_count + 1)
        
        # Remove the handler
        removed = cli.remove_handler(type(mock_handler))
        self.assertTrue(removed)
        self.assertEqual(len(cli.handlers), initial_count)
    
    def test_statistics_and_reset(self):
        """Test statistics gathering and reset."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console)
        
        # Get initial statistics
        stats = cli.get_statistics()
        
        self.assertIn('cli_status', stats)
        self.assertIn('session', stats)
        self.assertIn('command_processing', stats)
        self.assertIn('handlers', stats)
        
        # Test reset
        cli.reset_statistics()
        # Should not raise an error
    
    def test_session_context(self):
        """Test session context retrieval."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console)
        
        context = cli.get_session_context()
        
        self.assertIsInstance(context, dict)
        # Should have basic context keys (mock will provide defaults)
    
    def test_debug_mode(self):
        """Test debug mode setting."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console, debug_mode=True)
        
        self.assertTrue(cli.debug_mode)
        
        cli.set_debug_mode(False)
        self.assertFalse(cli.debug_mode)
    
    def test_string_representations(self):
        """Test string representation methods."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console)
        
        str_repr = str(cli)
        self.assertIn("CLIController", str_repr)
        
        repr_str = repr(cli)
        self.assertIn("CLIController", repr_str)
        self.assertIn("handlers=3", repr_str)
    
    def test_stop_method(self):
        """Test stop method."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console)
        
        cli.stop()
        
        self.assertTrue(cli.exit_requested)
        self.assertFalse(cli.running)
    
    @patch('ifw.cli.controller.SessionManager')
    def test_initialization_error_handling(self, mock_session_manager):
        """Test error handling during initialization."""
        # Make session manager initialization fail
        mock_session_manager.side_effect = Exception("Session manager failed")
        
        with self.assertRaises(CLIInitializationError):
            CLIController(agent=self.mock_agent, console=self.test_console)


class TestCLIControllerIntegration(unittest.TestCase):
    """Integration tests for CLI Controller with mocked dependencies."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.mock_agent = Mock()
        self.test_console = Console(file=StringIO(), width=80)
        
        # Patch all external dependencies
        self.patches = {
            'ShellCommandExecutor': patch('ifw.cli.controller.ShellCommandExecutor'),
            'ShellCommandDetector': patch('ifw.cli.controller.ShellCommandDetector'),
            'SessionManager': patch('ifw.cli.controller.SessionManager'),
            'ControlCommandHandler': patch('ifw.cli.controller.ControlCommandHandler'),
            'ShellCommandHandler': patch('ifw.cli.controller.ShellCommandHandler'),
            'AIRequestHandler': patch('ifw.cli.controller.AIRequestHandler'),
            'CommandProcessor': patch('ifw.cli.controller.CommandProcessor'),
        }
        
        self.mocks = {}
        for name, patcher in self.patches.items():
            self.mocks[name] = patcher.start()
    
    def tearDown(self):
        """Clean up patches."""
        for patcher in self.patches.values():
            patcher.stop()
    
    def test_component_initialization_order(self):
        """Test that components are initialized in correct order."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console)
        
        # Verify initialization calls were made
        self.mocks['ShellCommandExecutor'].assert_called_once()
        self.mocks['ShellCommandDetector'].assert_called_once()
        self.mocks['SessionManager'].assert_called_once()
        self.mocks['ControlCommandHandler'].assert_called_once()
        self.mocks['ShellCommandHandler'].assert_called_once()
        self.mocks['AIRequestHandler'].assert_called_once()
        self.mocks['CommandProcessor'].assert_called_once()
    
    def test_handler_dependency_injection(self):
        """Test that handlers are created with correct dependencies."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console)
        
        # Check that handlers were created with expected arguments
        shell_executor_instance = self.mocks['ShellCommandExecutor'].return_value
        shell_detector_instance = self.mocks['ShellCommandDetector'].return_value
        
        # Control handler should get executor and console
        self.mocks['ControlCommandHandler'].assert_called_with(
            shell_executor_instance, self.test_console
        )
        
        # Shell handler should get agent, executor, detector, console
        self.mocks['ShellCommandHandler'].assert_called_with(
            self.mock_agent, shell_executor_instance, shell_detector_instance, self.test_console
        )
        
        # AI handler should get agent, executor, console
        self.mocks['AIRequestHandler'].assert_called_with(
            self.mock_agent, shell_executor_instance, self.test_console
        )
    
    @patch('builtins.input', return_value='n')
    def test_error_recovery_user_choice(self, mock_input):
        """Test error recovery with user choosing to exit."""
        cli = CLIController(agent=self.mock_agent, console=self.test_console, debug_mode=True)
        
        # Simulate an unexpected error
        test_error = Exception("Test error")
        cli._handle_unexpected_error(test_error)
        
        # Should set exit_requested to True
        self.assertTrue(cli.exit_requested)


class TestCLIControllerCommandProcessing(unittest.TestCase):
    """Test command processing in CLI Controller."""
    
    def setUp(self):
        """Set up command processing test fixtures."""
        self.mock_agent = Mock()
        self.test_console = Console(file=StringIO(), width=80)
        
        # Create CLI with mocked components
        with patch.multiple(
            'ifw.cli.controller',
            ShellCommandExecutor=Mock(),
            ShellCommandDetector=Mock(),
            SessionManager=Mock(),
            ControlCommandHandler=Mock(),
            ShellCommandHandler=Mock(),
            AIRequestHandler=Mock(),
            CommandProcessor=Mock()
        ):
            self.cli = CLIController(agent=self.mock_agent, console=self.test_console)
    
    def test_process_command_success(self):
        """Test successful command processing."""
        # Mock successful command processing
        self.cli.command_processor.process_command.return_value = True
        
        # Should not raise any exceptions
        self.cli._process_command("test command")
        
        # Verify command processor was called
        self.cli.command_processor.process_command.assert_called_once_with("test command")
    
    def test_process_command_failure(self):
        """Test command processing failure."""
        # Mock failed command processing
        self.cli.command_processor.process_command.return_value = False
        
        # Should handle gracefully
        self.cli._process_command("test command")
        
        # Check that warning was printed to console
        output = self.test_console.file.getvalue()
        self.assertIn("Command execution was not successful", output)
    
    def test_process_command_exception(self):
        """Test command processing with exception."""
        from ifw.cli.command_processor import CommandProcessingError
        
        # Mock command processor raising exception
        self.cli.command_processor.process_command.side_effect = CommandProcessingError("Test error")
        
        # Should handle gracefully
        self.cli._process_command("test command")
        
        # Check that error was printed to console
        output = self.test_console.file.getvalue()
        self.assertIn("Command processing error", output)


def run_manual_test():
    """Manual test that doesn't require all dependencies."""
    print("🧪 Manual CLI Controller Test")
    print("=" * 50)
    
    try:
        # Create mock agent
        mock_agent = Mock()
        mock_agent.side_effect = lambda x: print(f"[AI] Processing: {x}")
        
        console = Console()
        
        # Test basic creation (may fail due to missing dependencies)
        try:
            cli = create_cli_controller(agent=mock_agent, console=console, debug_mode=True)
            print("✅ CLI Controller created successfully")
            print(f"   Controller: {cli}")
            
            # Test statistics
            stats = cli.get_statistics()
            print(f"✅ Statistics retrieved: {len(stats)} keys")
            
            # Test string representations
            print(f"✅ String repr: {str(cli)}")
            print(f"✅ Detailed repr: {repr(cli)}")
            
            print("\n📋 Available methods:")
            methods = [method for method in dir(cli) if not method.startswith('_')]
            for method in sorted(methods):
                print(f"   - {method}")
            
        except Exception as e:
            print(f"⚠️  CLI creation failed (expected if dependencies missing): {e}")
            print("   This is normal if running without proper imports.")
        
        print("\n✅ Manual test completed!")
        
    except Exception as e:
        print(f"❌ Manual test failed: {e}")


def run_tests():
    """Run all tests."""
    # Create test loader
    loader = unittest.TestLoader()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTests(loader.loadTestsFromTestCase(TestCLIController))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCLIControllerIntegration))
    test_suite.addTests(loader.loadTestsFromTestCase(TestCLIControllerCommandProcessing))
    
    # Run tests
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
            print(f"  {test}")
    
    if result.errors:
        print(f"\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"  {test}")
    
    if result.wasSuccessful():
        print(f"\n✅ All tests passed!")
    else:
        print(f"\n⚠️  Some tests failed!")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Choose test mode:")
    print("1. Run unit tests")
    print("2. Run manual test")
    print("3. Run both")
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice in ["1", "3"]:
            print("\n" + "="*60)
            print("RUNNING UNIT TESTS")
            print("="*60)
            success = run_tests()
        
        if choice in ["2", "3"]:
            print("\n" + "="*60)
            print("RUNNING MANUAL TEST")
            print("="*60)
            run_manual_test()
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")