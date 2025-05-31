#!/usr/bin/env python3

# System and external dependencies
from strands import Agent
from strands_tools import use_aws
import os

# Internal modules (relative imports)
from .utils.model import get_model
from .tools.use_gcp import use_gcp
from .tools.use_azure import use_azure
from .tools.use_docker import use_docker
from .utils.banner import print_banner
from .utils.callback_handler import CustomCallbackHandler
from .utils.thinking_indicator import start_thinking, stop_thinking

# Console output
from rich.prompt import Prompt
from rich.console import Console 

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


def chat(agent):
    """Enhanced chat with thinking indicator."""
    while True:
        try:
            user_input = Prompt.ask(
                "\n[bold]|>|[/bold]",
                default="",
                show_default=False
            )

            if user_input.lower().strip() == "exit":
                console.print("\n👋 Thanks for using Infraware CLI! Goodbye!")
                break
            elif user_input.lower().strip() == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            elif user_input.strip() == "":
                continue
            
            # Start thinking animation immediately after user input
            thinking_control = start_thinking()
            
            
            console.print()
            agent(user_input)
            console.print()


        except KeyboardInterrupt:
            # Make sure to clean up thinking animation on Ctrl+C
            if 'thinking_control' in locals():
                stop_thinking(thinking_control)
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