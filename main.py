from strands import Agent
import use_gcp  
from strands_tools import use_aws
from model import get_model
import os 

#System
from rich.console import Console
from rich import print as console_print 

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
- "Set up monitoring for my AWS Lambda functions"
- "Compare costs between my GCP and AWS usage"
- "Help me troubleshoot connectivity issues"

Ready to help you manage your cloud infrastructure efficiently and effectively!
"""

def chat(agent: Agent):
    
    while True:
        try:
            user_input = input("\n\n|>| ")

            
            if user_input.lower().strip() == "exit":
                print("Bye!")
                break
            elif user_input.lower().strip() == "clear":
                os.system('cls' if os.name == 'nt' else 'clear')
                continue

            elif user_input == "":
                print("DEBUG: Empty input, skipping")
                continue
            
            print("\n")
            response = agent(user_input)

            console_print()

        except KeyboardInterrupt:
            break
        
if __name__ == "__main__":
    orchestrator_agent = Agent(
        tools=[use_gcp, use_aws],
        model=get_model(),
        system_prompt=SYSTEM_PROMPT
    )

    # Print Infraware banner
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
    
    chat(orchestrator_agent)