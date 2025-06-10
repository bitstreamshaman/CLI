"""
Base handler class providing common interface for all command handlers.
"""
from abc import ABC, abstractmethod

class BaseHandler(ABC):
    @abstractmethod
    def can_handle(self, user_input: str) -> bool:
        """Check if this handler can process the given input"""
        pass
    
    @abstractmethod
    def handle(self, user_input: str) -> bool:
        """Process the input and return success status"""
        pass