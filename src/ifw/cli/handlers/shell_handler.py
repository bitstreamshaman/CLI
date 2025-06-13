"""
Shell Command Handler for Infraware Cloud Assistant.
Processes and executes shell commands.
"""

from .base_handler import BaseHandler


class ShellCommandHandler(BaseHandler):
    def __init__(self, agent, executor, detector, console):
        self.detector = detector
        self.executor = executor
        self.agent = agent
        self.console = console

    def can_handle(self, user_input: str) -> bool:
        """Detect if input is a traditional shell command."""
        return self.detector.is_shell_command(user_input)

    def handle(self, user_input: str) -> bool:
        """Execute shell command using persistent executor, add to conversation history."""
        try:
            output = self.executor.execute_shell_command(user_input)

            # Determine what to store in conversation history
            if output and output.startswith("❌"):
                # Error case
                history_output = output
                self.console.print(output)
                success = False
            elif output and output.strip():
                # Command produced actual output
                history_output = output
                success = True
            else:
                # Command succeeded but no meaningful output (like mkdir, cd, etc.)
                history_output = f"✓ Executed: {user_input}"
                success = True

            # Add shell command to conversation history in the correct format
            shell_command_message = {"role": "user", "content": [{"text": user_input}]}

            shell_result_message = {
                "role": "assistant",
                "content": [{"text": history_output}],
            }

            # Add to agent's conversation history
            self.agent.messages.append(shell_command_message)
            self.agent.messages.append(shell_result_message)

            return success

        except Exception as e:
            self.console.print(f"❌ Error executing command: {e}")
            return False
