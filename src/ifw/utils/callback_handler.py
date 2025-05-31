
from rich.console import Console
from rich.markdown import Markdown
console = Console()
class CustomCallbackHandler:
    """Callback handler using event-based completion detection."""
    
    def __init__(self):
        self.tool_count = 0
        self.previous_tool_use = None
        self.text_buffer = ""

    def __call__(self, **kwargs):
        data = kwargs.get("data", "")
        event = kwargs.get("event", {})
        current_tool_use = kwargs.get("current_tool_use", {})

        # Accumulate streaming text
        if data:
            self.text_buffer += data

        # Check for completion using the messageStop event
        if event and "messageStop" in event:
            if self.text_buffer.strip():
                console.print(Markdown(self.text_buffer.strip()))
                console.print()
                self.text_buffer = ""

        # Handle tool usage display
        if current_tool_use and current_tool_use.get("name"):
            tool_name = current_tool_use.get("name", "Unknown tool")
            if self.previous_tool_use != current_tool_use:
                # If we have buffered text, render it before showing tool usage
                if self.text_buffer.strip():
                    console.print(Markdown(self.text_buffer.strip()))
                    self.text_buffer = ""
                
                self.previous_tool_use = current_tool_use
                self.tool_count += 1
                console.print(f"\n[bold blue]Tool #{self.tool_count}: {tool_name}[/bold blue]")