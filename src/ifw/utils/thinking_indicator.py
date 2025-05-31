from rich.console import Console
from rich.spinner import Spinner
from rich.live import Live

console = Console()

# Global variable to track the current thinking animation
_active_thinking = None

def start_thinking():
    """Show simple thinking message."""
    console.print("\nProcessing...")

def stop_thinking():
    """Clear thinking message."""
    # Move cursor up and clear the line
    console.print("\033[A\033[K", end="")

def is_thinking():
    """Check if thinking animation is currently active.
    
    Returns:
        bool: True if thinking animation is running
    """
    global _active_thinking
    return _active_thinking is not None