import time
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

console = Console()

class CustomCallbackHandler:
    """Clean typing effect callback handler for Strands agents."""
    
    def __init__(self, typing_speed=0.02):
        self.tool_count = 0
        self.previous_tool_use = None
        self.typing_speed = typing_speed
        self.is_typing = False

    def _smooth_typing_effect(self, text):
        """Show typing effect using Rich Live."""
        if not text.strip():
            return
            
        self.is_typing = True
        
        with Live("", refresh_per_second=30, console=console) as live:
            displayed_text = ""
            
            for char in text:
                displayed_text += char
                live.update(Markdown(displayed_text))
                time.sleep(self.typing_speed)
            
            # Hold the final result for a moment
            time.sleep(0.3)
        
        self.is_typing = False

    def __call__(self, **kwargs):
        # Handle tool usage display
        current_tool_use = kwargs.get("current_tool_use", {})
        if current_tool_use and current_tool_use.get("name"):
            tool_name = current_tool_use.get("name", "Unknown tool")
            if self.previous_tool_use != current_tool_use:
                self.previous_tool_use = current_tool_use
                self.tool_count += 1
                console.print(f"\n[bold blue]Tool #{self.tool_count}: {tool_name}[/bold blue]")

        # Handle complete messages with typing effect
        if "message" in kwargs and kwargs["message"].get("role") == "assistant":
            message_content = kwargs["message"].get("content", [])
            if message_content and len(message_content) > 0:
                text = message_content[0].get("text", "")
                if text.strip():
                    self._smooth_typing_effect(text.strip())