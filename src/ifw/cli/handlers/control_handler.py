"""
Control Command Handler for Infraware Cloud Assistant.
Handles control commands like exit, clear, reset.
"""
import sys
import os
from .base_handler import BaseHandler

class ControlCommandHandler(BaseHandler):
    def __init__(self, shell_command_executor, console):
        self.shell_executor = shell_command_executor
        self.console = console
        self.control_commands = ["clear", "exit"]
    
    def can_handle(self, user_input: str) -> bool:
        return user_input.lower().strip() in self.control_commands
        
    def handle(self, user_input: str) -> bool:
        """Execute control commands including shell state management commands."""
        cmd = user_input.lower().strip()

        if cmd == "exit":
            self.console.print(f"\n👋 Thanks for using [bold #2B1BD1]Infraware CLI[/bold #2B1BD1] Goodbye!")
            sys.exit(0)

        elif cmd == "clear":
            os.system('cls' if os.name == 'nt' else 'clear')
            return True
            
        return False