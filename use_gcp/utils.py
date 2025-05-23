"""
Shared utilities for GCP MCP tools.
Contains MCP client management and common functions.
"""

from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient
import json
import uuid

# Storage for our MCP client to maintain connection
_mcp_client = None
_current_project = None
_current_region = "us-central1"  # Default region

def _get_mcp_client():
    """Get or create the MCP client connection."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(command="npx", args=["-y", "gcp-mcp"])
        ))
        _mcp_client.__enter__()
    return _mcp_client

def _call_gcp_tool(name, **kwargs):
    """Call a GCP MCP tool with the given arguments."""
    mcp_client = _get_mcp_client()
    tool_use_id = f"gcp-{name}-{uuid.uuid4()}"
    
    # Make sure the name doesn't have angle brackets
    clean_name = name.strip('<>') if name.startswith('<') and name.endswith('>') else name
    
    # Call the tool
    result = mcp_client.call_tool_sync(
        tool_use_id=tool_use_id,
        name=clean_name,  # Use the clean name
        arguments=kwargs
    )
    
    # Process the result
    if result and result.get("status") == "success" and result.get("content"):
        # Extract the content
        for item in result.get("content", []):
            if "text" in item:
                try:
                    # Try to parse as JSON
                    return json.loads(item["text"])
                except json.JSONDecodeError:
                    # Return as text if not JSON
                    return item["text"]
    
    # If we got here, something went wrong
    return {"error": f"Error executing tool {name}", "result": result}

def get_current_project():
    """Get the currently selected GCP project."""
    return _current_project

def set_current_project(project_id: str):
    """Set the currently selected GCP project."""
    global _current_project
    _current_project = project_id

def get_current_region():
    """Get the currently selected GCP region."""
    return _current_region

def set_current_region(region: str):
    """Set the currently selected GCP region."""
    global _current_region
    _current_region = region

