#!/usr/bin/env python3

# System and external dependencies
from strands import Agent
from strands_tools import use_aws
import os


# Internal modules (relative imports)
from .model import get_model
from .use_gcp import use_gcp
from .use_azure import use_azure
from .use_docker import use_docker

# Console output
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

console = Console()

SYSTEM_PROMPT = """
You are Infraware Cloud Assistant, an expert AI cloud operations assistant specializing in multi-cloud environments. 
You help users create,manage and operate their cloud infrastructure across Google Cloud Platform (GCP), Amazon Web Services (AWS) and Microsoft Azure (Azure) .

🔧 YOUR CAPABILITIES:
- Multi-cloud strategy and best practices guidance
- Cloud cost optimization and billing analysis
- Infrastructure troubleshooting and monitoring
- Security and IAM management across cloud platforms

📋 YOUR WORKFLOW:
1. **Analyze** the user's request to understand their cloud operation needs
2. **Identify** the appropriate cloud platform
3. **Select** the correct tool (use_gcp or use_aws) based on the request
4. **Execute** the operation using the most suitable approach
5. **Provide** clear, actionable results and recommendations

🤝 YOUR INTERACTION STYLE:
- Be friendly, professional, and helpful
- Provide clear explanations of what you're doing and why
- Offer best practices and optimization suggestions when relevant
- Ask clarifying questions when the cloud platform or specific requirements are unclear
- Present results in a clear, organized manner
- Suggest next steps or related operations that might be useful

💡 EXAMPLES OF REQUESTS YOU HANDLE:
- "List all my GCP projects"
- "Show me my AWS EC2 instances in us-east-1"
- "Check my cloud billing costs for this month"
- "Create a new subnet in GCP"
- "List all my Azure resource groups"
- "Set up monitoring for my AWS Lambda functions"
- "Compare costs between my GCP and AWS usage"
- "Deploy a new Kubernetes cluster in Azure"
- "Help me troubleshoot connectivity issues"

Ready to help you manage your cloud infrastructure efficiently and effectively!
"""

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



def print_banner():
    """Print the Infraware banner."""
    print("\n" + "="*60)
    print("██╗███╗   ██╗███████╗██████╗  █████╗ ██╗    ██╗ █████╗ ██████╗ ███████╗")
    print("██║████╗  ██║██╔════╝██╔══██╗██╔══██╗██║    ██║██╔══██╗██╔══██╗██╔════╝")
    print("██║██╔██╗ ██║█████╗  ██████╔╝███████║██║ █╗ ██║███████║██████╔╝█████╗  ")
    print("██║██║╚██╗██║██╔══╝  ██╔══██╗██╔══██║██║███╗██║██╔══██║██╔══██╗██╔══╝  ")
    print("██║██║ ╚████║██║     ██║  ██║██║  ██║╚███╔███╔╝██║  ██║██║  ██║███████╗")
    print("╚═╝╚═╝  ╚═══╝╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝")
    print("")
    print("                    ▶▶▶ INFRAWARE CLI ALPHA ◀◀◀")
    print("                  Your AI Cloud Operations Helper")
    print("                        |>| GCP & AWS & Azure |>|")
    print("="*60)
    print("\n🌟 Welcome! I can help you manage your GCP and AWS resources.")
    print("💡 Commands: Type 'exit' to quit, 'clear' to clear screen, or ask me anything!")
    print("-"*60)


def chat(agent):
    """Enhanced chat with more Rich styling."""
    while True:
        try:
            
            user_input = Prompt.ask(
                "\n[bold cyan]|>|[/bold cyan]",
                default="",
                show_default=False
            )

            if user_input.lower().strip() == "exit":
                console.print("\n[bold green]👋 Thanks for using Infraware CLI! Goodbye![/bold green]")
                break
            elif user_input.lower().strip() == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                print_banner()
                continue
            elif user_input.strip() == "":
                continue
            
            console.print()
            agent(user_input)

        except KeyboardInterrupt:
            break


def main():
    """Main entry point for the CLI application."""
    
    orchestrator_agent = Agent(
        tools=[
            use_gcp, 
            use_aws,
            use_azure,
            use_docker,
        ],
        model=get_model(),
        callback_handler=CustomCallbackHandler(),
        system_prompt=SYSTEM_PROMPT
    )

    print_banner()
    chat(orchestrator_agent)


if __name__ == "__main__":
    main()