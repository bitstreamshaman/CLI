import time
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live

console = Console()

class CustomCallbackHandler:
    """Clean callback handler focused only on response rendering."""
    
    def __init__(self, typing_speed=0.02):
        self.tool_count = 0
        self.previous_tool_use = None
        self.typing_speed = typing_speed
        self.is_typing = False
        self.has_stopped_thinking = False  # Add this line

    def _estimate_content_height(self, text):
        """Simple estimation: just count newlines plus a small buffer."""
        if not text.strip():
            return 0
        
        # Simple count of newlines + 1 for the last line
        lines = text.count('\n') + 1
        
        # Add small buffer for markdown formatting (but much less aggressive)
        markdown_elements = text.count('#') + text.count('```') + text.count('---')
        buffer = min(markdown_elements, 3)  # Cap the buffer at 3 lines
        
        return lines + buffer

    def _should_use_typing_effect(self, text):
        """Use a much more permissive threshold."""
        terminal_height = console.size.height
        estimated_height = self._estimate_content_height(text)
        
        # Much more generous - only skip typing for really tall content
        max_allowed_height = terminal_height - 5  # Leave 5 lines buffer for terminal UI
        
        return estimated_height <= max_allowed_height

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

    def _instant_display(self, text):
        """Display content instantly for long responses."""
        if not text.strip():
            return
            
        # Optional: Show a brief "loading" indicator for very long content
        if self._estimate_content_height(text) > console.size.height:
            console.print("[dim]📄 Displaying response...[/dim]")
            time.sleep(0.2)  # Brief pause to show the indicator
        
        console.print(Markdown(text))
        console.print()  # Add spacing

    def __call__(self, **kwargs):
        # Handle tool usage display
        current_tool_use = kwargs.get("current_tool_use", {})
        if current_tool_use and current_tool_use.get("name"):
            tool_name = current_tool_use.get("name", "Unknown tool")
            if self.previous_tool_use != current_tool_use:
                self.previous_tool_use = current_tool_use
                self.tool_count += 1
                console.print(f"\n[bold blue]Tool #{self.tool_count}: {tool_name}[/bold blue]")

        # Handle complete messages with smart display choice
        if "message" in kwargs and kwargs["message"].get("role") == "assistant":
            message_content = kwargs["message"].get("content", [])
            if message_content and len(message_content) > 0:
                text = message_content[0].get("text", "")
                if text.strip():
                    # Smart decision: typing effect vs instant display
                    if self._should_use_typing_effect(text):
                        self._smooth_typing_effect(text.strip())
                    else:
                        self._instant_display(text.strip())