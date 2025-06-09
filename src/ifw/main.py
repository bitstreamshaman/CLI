# System and external dependencies
from strands import Agent
from strands_tools import use_aws, shell
import os
import sys

#Suppress Pydantic deprecation warnings from strands
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="strands")
warnings.filterwarnings("ignore", message=".*The `dict` method is deprecated.*", category=DeprecationWarning)




# Enhanced terminal input dependencies
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

# Internal modules (relative imports)
from .utils.model import get_model
from .tools.cloud.use_gcp import use_gcp
from .tools.cloud.use_azure import use_azure
from .tools.containers.use_docker import use_docker
from .utils.banner import print_banner
from .utils.callback_handler import CustomCallbackHandler
from .utils.thinking_indicator import start_thinking, stop_thinking
from .shell.is_shell import ShellCommandDetector
from .shell.exec_shell import ShellExecutor
from .shell.completion import SmartCompleter

# Import memory tools
from .tools.memory import use_memory
# Console output
from rich.console import Console 

# Enhanced system prompt that includes memory capabilities
SYSTEM_PROMPT = """
You are Infraware Cloud Assistant, an expert AI cloud operations assistant specializing in multi-cloud environments with advanced persistent memory capabilities.
You help users create, manage and operate their cloud infrastructure across Google Cloud Platform (GCP), Amazon Web Services (AWS) and Microsoft Azure (Azure).
You also have expertise in Docker container management and orchestration.

🧠 MEMORY CAPABILITIES:
You have access to powerful memory tools that allow you to:
- store_memory: Store important information for future reference (user preferences, configurations, solutions)
- recall_memory: Search and retrieve relevant past information 
- generate_memory_response: Generate responses enhanced with stored context
- list_recent_memories: Review recent stored memories
- clear_user_memories: Clear user memories when needed (use with caution)

🔧 YOUR CAPABILITIES:
- Multi-cloud strategy and best practices guidance
- Cloud cost optimization and billing analysis
- Infrastructure troubleshooting and monitoring
- Security and IAM management across cloud platforms
- Persistent memory of user configurations and preferences

📋 YOUR ENHANCED WORKFLOW:
1. **Check Memory First** - Use recall_memory to find relevant past context before responding
2. **Analyze** the user's request to understand their cloud operation needs
3. **Identify** the appropriate cloud platform and recall user preferences
4. **Select** the correct tool (use_gcp, use_aws, use_azure, use_docker) based on request and history
5. **Execute** the operation using the most suitable approach
6. **Store Important Results** - Use store_memory to save significant outcomes, configurations, or learnings
7. **Provide** clear, actionable results enhanced with relevant historical context

🧠 MEMORY USAGE BEST PRACTICES:
**What to Store:**
- User preferences (preferred AWS regions, naming conventions, etc.)
- Important configurations and environment details
- Solutions to problems and troubleshooting steps
- Project information and deployment patterns
- Cost optimization strategies that worked
- Security configurations and best practices used

**What to Recall:**
- Check for similar past issues before troubleshooting
- Recall user's typical deployment patterns
- Remember previous cost optimization strategies
- Look up past security configurations
- Find relevant project context

**When to Use generate_memory_response:**
- For questions that benefit from historical context
- When user asks about past configurations or issues
- To provide personalized recommendations based on history

🤝 YOUR INTERACTION STYLE:
- Be friendly, professional, and helpful
- Always check memory for relevant context before major operations
- Use stored context to provide personalized, informed responses
- Store important outcomes and learnings for future reference
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
- "What's my hostname and current directory?"
- "Deploy a new service in my Kubernetes cluster"
- "Compare costs between my GCP and AWS usage"
- "Deploy a new Kubernetes cluster in Azure"
- "Help me troubleshoot connectivity issues"
- "List all files in my Docker container"

💡 MEMORY-ENHANCED EXAMPLES:
- "What regions did I use last time for my AWS deployment?" → use recall_memory
- "Remember my preference for t3.medium instances" → use store_memory
- "Based on my past GCP setup, what would you recommend?" → use generate_memory_response
- Store successful troubleshooting solutions for future reference
- Recall past security configurations when setting up new resources

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

# Create orchestrator agent with memory tools
orchestrator_agent = Agent(
    tools=[
        # Cloud and infrastructure tools
        use_gcp, 
        use_aws,
        use_azure,
        use_docker,
        shell,
        # Memory tools
        use_memory
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
    """Execute AI request with current shell context and user identification."""
    # Get current shell context
    current_dir = executor.get_current_directory()
    
    # Get user identification (you might want to make this configurable)
    import getpass
    current_user = getpass.getuser()
    
    # Add context about current directory and user to the AI request
    contextual_input = f"[User: {current_user}, Current directory: {current_dir}] {user_input}"
    
    console.print()
    # The orchestrator agent now has access to all memory tools
    # It will automatically use them as needed based on the enhanced system prompt
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
    """Chat function with dynamic completion, command history, reverse search, and memory capabilities."""
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
                    stop_thinking()
            
        except KeyboardInterrupt:
            # Handle Ctrl+C during input or other operations
            
            # Stop thinking animation if it was started
            if thinking_control is not None:
                stop_thinking()
            
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