from dotenv import load_dotenv
from os import getenv
from rich.panel import Panel
from rich import print as print_console
from strands.models.anthropic import AnthropicModel

def get_model():

    load_dotenv(".env")
    api_key = getenv('ANTHROPIC_API_KEY')

    if not api_key:
        # Create an eye-catching error panel
        error_message = Panel(
            "[bold red]API KEY MISSING[/bold red]\n\n"
            "You must assign [yellow]ANTHROPIC_API_KEY[/yellow] in your [blue].env[/blue] file before proceeding.",
            title="⚠️ WARNING",
            border_style="red"
        )
        print_console(error_message)
        exit()

    model = AnthropicModel(
        client_args={
            "api_key": api_key,
        },
        # **model_config
        max_tokens=1028,
        model_id="claude-sonnet-4-20250514",
        params={
            "temperature": 0.7,
        }
    )

    return model 