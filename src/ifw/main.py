# System and external dependencies
import argparse

# Internal modules (relative imports)

from .cli.controller import create_cli_controller
from .utils.banner import print_banner
from .config.agent_config import create_orchestrator_agent
from .config.loggin_config import setup_logging

def main():
    """Main entry point for the CLI application."""
    # Keep: argument parsing and logging setup
    parser = argparse.ArgumentParser(description='Infraware CLI')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()
    setup_logging(args.verbose)
    print_banner()
    
    orchestrator_agent = create_orchestrator_agent()
    
    # NEW: Replace chat() with CLI Controller
    cli = create_cli_controller(
        agent=orchestrator_agent, 
        debug_mode=args.verbose
    )
    cli.run()

if __name__ == "__main__":
    main()

