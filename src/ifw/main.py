# System and external dependencies
from strands import Agent
from strands_tools import use_aws, shell
import os
import sys

# Internal modules (relative imports)
from .utils.model import get_model
from .tools.use_gcp import use_gcp
from .tools.use_azure import use_azure
from .tools.use_docker import use_docker
from .utils.banner import print_banner
from .utils.callback_handler import CustomCallbackHandler
from .utils.thinking_indicator import start_thinking, stop_thinking
from .utils.is_shell import ShellCommandDetector
from .utils.exec_shell import ShellExecutor

# Console output
from rich.prompt import Prompt
from rich.console import Console 

SYSTEM_PROMPT = """
You are Infraware Cloud Assistant, an expert AI cloud operations assistant specializing in multi-cloud environments. 
You help users create,manage and operate their cloud infrastructure across Google Cloud Platform (GCP), Amazon Web Services (AWS) and Microsoft Azure (Azure).
You also have expertise in Docker container management and orchestration.

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
- "Create a Docker container for my web app"
- "Deploy a new service in my Kubernetes cluster"
- "Compare costs between my GCP and AWS usage"
- "Deploy a new Kubernetes cluster in Azure"
- "Help me troubleshoot connectivity issues"
"""

console = Console()
detector = ShellCommandDetector()
# Create a SINGLE persistent executor instance
executor = ShellExecutor()

orchestrator_agent = Agent(
    tools=[
        use_gcp, 
        use_aws,
        use_azure,
        use_docker,
        shell,
    ],
    model=get_model(),
    callback_handler=CustomCallbackHandler(),
    system_prompt=SYSTEM_PROMPT
)


def is_shell_command(user_input: str) -> bool:
    """Detect if input is a traditional shell command."""
    return detector.is_shell_command(user_input)

def execute_shell_command(command: str) -> str:
    """Execute shell command using persistent executor, add to conversation history, and return output."""
    # Execute the command using the persistent executor
    output = executor.execute_shell_command(command)
    
    # Add shell command to conversation history in the correct format
    shell_command_message = {
        'role': 'user', 
        'content': [{'text': f'{command}'}]
    }
    
    shell_result_message = {
        'role': 'assistant', 
        'content': [{'text': f'{output}'}]
    }
    
    # Add to agent's conversation history
    orchestrator_agent.messages.append(shell_command_message)
    orchestrator_agent.messages.append(shell_result_message)
    
    return output

def is_control_command(user_input: str) -> bool:
    """Detect if input is a control command (e.g., 'clear', 'exit', 'reset')."""
    control_commands = ["clear", "exit", "reset"]
    if user_input.lower().strip() in control_commands:
         return True
    else: return False

def execute_control_command(command: str):
    """Execute control commands including new shell state management commands."""
    cmd = command.lower().strip()
    
    if cmd == "exit":
        console.print("\n👋 Thanks for using [bold cyan]Infraware CLI[/bold cyan] Goodbye!")
        sys.exit(0)

    elif cmd == "clear":
        os.system('cls' if os.name == 'nt' else 'clear')
        return
        
    elif cmd == "reset":
        # Reset shell state
        executor.reset_state()
        console.print("🔄 Shell state reset to initial directory and environment")
        return
                
    elif command.strip() == "":
        return

def classify_intent(user_input: str) -> str:
    """Classify if input is 'shell', 'ai', or 'control'."""
    if is_shell_command(user_input):
        # Handle shell commands separately
        output = execute_shell_command(user_input)
        console.print(f"\n{output}\n")

def execute_ai_request(user_input: str) -> bool:
    """Execute AI request with current shell context."""
    # You can optionally provide shell context to the AI
    current_dir = executor.get_current_directory()
    
    # Add context about current directory to the AI request
    contextual_input = f"[Current directory: {current_dir}] {user_input}"
    
    console.print()
    orchestrator_agent(contextual_input)
    console.print()

def get_prompt() -> str:
    import getpass
    import socket
    
    username = getpass.getuser()
    hostname = socket.gethostname()
    cwd = executor.get_current_directory()  # Full path instead of basename
    
    return f"{username}@{hostname}:{cwd}"


def chat():
    """Enhanced chat with thinking indicator and persistent shell state."""
    console.print(f"🐚 Shell session started in: [bold cyan]{executor.get_current_directory()}[/bold cyan]")

    while True:
        thinking_control = None  # Initialize outside try block
        try:
           
            prompt = get_prompt()
            
            user_input = Prompt.ask(
                f"\n[bold cyan]|>| {prompt}[/bold cyan]",
                default="",
                show_default=False
            )

            # Check if input is a control command
            if is_control_command(user_input):
                execute_control_command(user_input)
                continue
                
                
            # Check if input is a shell command
            if is_shell_command(user_input):
                # Handle shell commands separately
                output = execute_shell_command(user_input)
                if output:  # Only print if there's output
                    console.print(f"\n{output}")
                continue

            if user_input.strip() == "":
                # Skip empty input
                continue
            
            # If input is not a control or shell command, treat it as an AI request
            # Start thinking animation immediately after user input
            thinking_control = start_thinking()
            try:
                execute_ai_request(user_input)
            except KeyboardInterrupt:
                # Handle Ctrl+C during AI execution
                console.print("\n🛑 AI request interrupted")
                continue
            finally:
                # Always stop thinking animation if it was started
                if thinking_control is not None:
                    stop_thinking()  # Remove the argument since function takes 0
            
        except KeyboardInterrupt:
            # Handle Ctrl+C during input or other operations
            
            # Stop thinking animation if it was started
            if thinking_control is not None:
                stop_thinking()  # Remove the argument since function takes 0
            
            # Try to interrupt current shell command
            if executor.interrupt_current_command():
                console.print("\n🛑 Command interrupted")
            else:
                console.print("\n🛑 Use 'exit' to quit")
            continue

def main():
    """Main entry point for the CLI application."""
    print_banner()
    chat()

if __name__ == "__main__":
    main()