# System and external dependencies
from strands import Agent
from strands_tools import use_aws, shell
import os
import sys

# Enhanced terminal input dependencies
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

# Internal modules (relative imports)
from .utils.model import get_model
from .tools.use_gcp import use_gcp
from .tools.use_azure import use_azure
from .tools.use_docker import use_docker
from .utils.banner import print_banner
from .utils.callback_handler import CustomCallbackHandler
from .utils.thinking_indicator import start_thinking, stop_thinking
from .utils.shell.is_shell import ShellCommandDetector
from .utils.shell.exec_shell import ShellExecutor

# Import the completion system
from .utils.shell.completion import SmartCompleter

# Console output
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

MANDATORY COMMAND DISCLOSURE FOR SHELL OPERATIONS: You MUST always explicitly state every command before executing it in the terminal/shell. This requirement applies ONLY to shell/terminal commands, NOT to custom MCP tools or other specialized tools.

SCOPE:
- APPLIES TO: Shell commands, terminal operations, bash/zsh/cmd commands
- DOES NOT APPLY TO: Custom MCP tools, API calls, specialized function calls, or non-shell operations

REQUIRED FORMAT:
Before executing any shell command, you must write:
"EXECUTING SHELL COMMAND: [exact command]"

EXAMPLES:
- EXECUTING SHELL COMMAND: ls -l /home/user
- EXECUTING SHELL COMMAND: cd /var/log && tail -f syslog
- EXECUTING SHELL COMMAND: sudo systemctl restart nginx
- EXECUTING SHELL COMMAND: grep "error" /var/log/apache2/error.log

ENFORCEMENT RULES:
1. Never execute a shell command without first printing it using the exact format above
2. This applies to ALL shell commands - no matter how simple or obvious
3. If you need to run multiple shell commands, print each one separately before execution
4. Even basic commands like 'pwd', 'whoami', or 'ls' must be announced first
5. This requirement is specific to shell/terminal operations only
6. Custom MCP tools and other specialized functions do not require this disclosure
7. Failure to follow this format for shell commands indicates non-compliance with system requirements

This disclosure requirement exists for transparency, security, and audit purposes when interacting with the system shell. Non-compliance is not acceptable under any circumstances for shell operations.

"""

console = Console()
detector = ShellCommandDetector()
# Create a SINGLE persistent executor instance
executor = ShellExecutor()

# Create smart completer and command history
smart_completer = SmartCompleter(executor)
command_history = InMemoryHistory()

# Create key bindings
def create_key_bindings():
    """Create custom key bindings."""
    kb = KeyBindings()
    
    # Ctrl+L to clear screen
    @kb.add('c-l')
    def clear_screen(event):
        event.app.renderer.clear()
        
    return kb

key_bindings = create_key_bindings()

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
    
    # Determine what to store in conversation history
    if output and output.startswith("❌"):
        # Error case
        history_output = output
        console.print(output)
    elif output and output.strip():
        # Command produced actual output
        history_output = output
    else:
        # Command succeeded but no meaningful output (like mkdir, cd, etc.)
        # Store a confirmation message instead of empty string
        history_output = f"✓ Executed: {command}"
    
    # Add shell command to conversation history in the correct format
    shell_command_message = {
        'role': 'user', 
        'content': [{'text': command}]
    }
    
    shell_result_message = {
        'role': 'assistant', 
        'content': [{'text': history_output}]
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
        console.print("\n👋 Thanks for using [bold #2B1BD1]Infraware CLI[/bold #2B1BD1] Goodbye!")
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

def execute_ai_request(user_input: str) -> bool:
    """Execute AI request with current shell context."""
    # You can optionally provide shell context to the AI
    current_dir = executor.get_current_directory()
    
    # Add context about current directory to the AI request
    contextual_input = f"[Current directory: {current_dir}] {user_input}"
    
    console.print()
    orchestrator_agent(contextual_input)
    console.print()

def get_prompt_info():
    """Get prompt information for enhanced terminal."""
    import getpass
    import socket
    
    username = getpass.getuser()
    hostname = socket.gethostname()
    cwd = executor.get_current_directory()
    
    return username, hostname, cwd

def chat():
    """Enhanced chat with dynamic completion, command history, and reverse search."""


    while True:
        thinking_control = None  # Initialize outside try block
        try:
            username, hostname, cwd = get_prompt_info()
            
           # Create formatted prompt
            prompt_text = HTML(f'<blue><b>|>| {username}@{hostname}:{cwd} </b></blue> ')
            
            # Get user input with enhanced features
            user_input = prompt(
                prompt_text,
                completer=smart_completer,
                history=command_history,
                complete_style=CompleteStyle.READLINE_LIKE,
                key_bindings=key_bindings,
                enable_history_search=True,  # Enables Ctrl+R reverse search
                complete_while_typing=False,  # Set to True for real-time completion
            )

            # Check if input is a control command
            if is_control_command(user_input):
                execute_control_command(user_input)
                continue
                
            # Check if input is a shell command
            if is_shell_command(user_input):
                # Handle shell commands separately
                execute_shell_command(user_input)
                continue


            if user_input.strip() == "":
                # Skip empty input
                continue
            
            # If input is not a control or shell command, treat it as an AI request
            # Start thinking animation immediately after user input
            thinking_control = start_thinking()
            try:
                execute_ai_request(user_input)
                console.print()
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
        except EOFError:
            # Handle Ctrl+D (EOF)
            console.print("\n👋 Thanks for using [bold #2B1BD1]Infraware CLI[/bold #2B1BD1] Goodbye!")
            sys.exit(0)

def main():
    """Main entry point for the CLI application."""
    print_banner()
    chat()

if __name__ == "__main__":
    main()