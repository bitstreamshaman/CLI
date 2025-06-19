"""
AI Request Handler for Infraware Cloud Assistant.
Processes AI requests and manages agent interactions.
"""

from ...utils.thinking_indicator import start_thinking, stop_thinking
from .base_handler import BaseHandler


class AIRequestHandler(BaseHandler):
    def __init__(self, agent, executor, console):
        self.agent = agent
        self.executor = executor
        self.console = console

    def can_handle(self, user_input: str) -> bool:
        """Always returns True as this is the fallback handler"""
        return True

    def handle(self, user_input: str) -> bool:
        """Execute AI request with current shell context and user identification."""
        thinking_control = None
        try:

            # Start thinking animation
            thinking_control = start_thinking()

            self.console.print()
            self.agent(user_input)
            self.console.print()

            return True

        except KeyboardInterrupt:
            self.console.print("\n🛑 AI request interrupted")
            return False
        except Exception as e:
            self.console.print(f"❌ Error processing AI request: {e}")
            return False
        finally:
            # Always stop thinking animation if it was started
            if thinking_control is not None:
                stop_thinking()
