import os
from pathlib import Path
from dotenv import load_dotenv
from rich.panel import Panel
from rich import print as print_console
from strands.models.anthropic import AnthropicModel


def load_env_file(file_path):
    """Load environment variables from a file."""
    try:
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value.strip('"\'')
    except Exception:
        # Silently ignore file reading errors
        pass


def get_api_key():
    """Get API key from .ifw.env"""
    
    # 3. Home directory .ifw.env (user-specific config)
    home_env = Path.home() / '~/.ifw/.ifw.env'
    if home_env.exists():
        load_env_file(home_env)
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if api_key:
            return api_key


def create_config_file():
    """Interactively create the API key config file."""
    # Create .ifw directory in user home
    config_dir = Path.home() / '.ifw'
    config_file = config_dir / '.ifw.env'
    
    # Show setup message
    setup_message = Panel(
        f"[bold yellow]FIRST TIME SETUP[/bold yellow]\n\n"
        f"Let's set up your Anthropic API key!\n\n"
        f"[blue]Get your API key from:[/blue] https://console.anthropic.com/\n"
        f"[blue]Config will be saved to:[/blue] {config_file}",
        title="🔧 SETUP",
        border_style="yellow",
        width=70
    )
    print_console(setup_message)
    print_console()
    
    try:
        # Get API key from user
        api_key = input("Enter your Anthropic API key: ").strip()
        
        if not api_key:
            print_console("[red]❌ No API key provided. Setup cancelled.[/red]")
            return None
        
        # Create the .ifw directory if it doesn't exist
        config_dir.mkdir(mode=0o700, exist_ok=True)
        
        # Create the config file
        with open(config_file, 'w') as f:
            f.write(f"ANTHROPIC_API_KEY={api_key}\n")
            # Avoid using `tokenizers` before the fork 
            f.write("TOKENIZERS_PARALLELISM='false'\n")
        
        # Set file permissions (read/write for owner only)
        config_file.chmod(0o600)
        
        # Load the new environment variable
        os.environ['ANTHROPIC_API_KEY'] = api_key
        
        success_message = Panel(
            f"[bold green]✅ API key saved successfully![/bold green]\n\n"
            f"Config file created: {config_file}\n"
            f"You're all set to use Infraware CLI!",
            title="🎉 SUCCESS",
            border_style="green"
        )
        print_console(success_message)
        print_console()
        
        return api_key
        
    except KeyboardInterrupt:
        print_console("\n[yellow]⚠️  Setup cancelled by user.[/yellow]")
        return None
    except Exception as e:
        print_console(f"[red]❌ Error creating config file: {e}[/red]")
        return None

def prompt_for_setup():
    """Ask user if they want to create a config file."""
    print_console()
    response = input("Would you like to set up your API key now? (y/n): ").strip().lower()
    
    if response in ['y', 'yes', '']:
        return create_config_file()
    else:
        print_console("[yellow]💡 You can run the setup later or set the API key manually.[/yellow]")
        print_console("[blue]Manual setup:[/blue] echo 'ANTHROPIC_API_KEY=your_key' > ~/.ifw.env")
        return None


def get_model():
    """Initialize and return the Anthropic model with API key from multiple sources."""
    
    api_key = get_api_key()
    
    if not api_key:
        # Show original error message first
        error_message = Panel(
            "[bold red]API KEY MISSING[/bold red]\n\n"
            "You must assign [yellow]ANTHROPIC_API_KEY[/yellow] in your [blue].env[/blue] file before proceeding.",
            title="⚠️ WARNING",
            border_style="red"
        )
        print_console(error_message)
        
        # Then try interactive setup
        api_key = prompt_for_setup()
        
        if not api_key:
            # User declined setup or it failed
            exit(1)

    model = AnthropicModel(
        client_args={
            "api_key": api_key,
        },
        max_tokens=1028,
        model_id="claude-sonnet-4-20250514",
        params={
            "temperature": 0.7,
        }
    )

    return model