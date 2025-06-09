from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def execute_azure_cli_extension(command: str) -> dict:
    """
    Execute Azure CLI commands through the Azure MCP extension.
    
    This tool allows execution of Azure CLI commands via the MCP server.
    
    Args:
        command: The Azure CLI command to execute (without the 'az' prefix).
                Example: "vm list --resource-group myRG --output table"
    
    Returns:
        A dictionary containing the command execution results.
    """
    return _call_azure_tool("azmcp-extension-az", 
                           command=command)

@tool
def execute_azure_developer_cli_extension(command: str) -> dict:
    """
    Execute Azure Developer CLI (azd) commands through the Azure MCP extension.
    
    This tool allows execution of Azure Developer CLI commands via the MCP server.
    
    Args:
        command: The Azure Developer CLI command to execute (without the 'azd' prefix).
                Example: "env list" or "up --environment production"
    
    Returns:
        A dictionary containing the command execution results.
    """
    return _call_azure_tool("azmcp-extension-azd", 
                           command=command)