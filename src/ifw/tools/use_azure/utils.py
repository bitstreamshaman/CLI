from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
import json
import uuid

# Storage for our MCP client to maintain connection
_mcp_client = None

def _get_mcp_client():
    """Get or create the MCP client connection."""
    global _mcp_client
    if _mcp_client is None:
        try:
            _mcp_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(command="npx", args=["-y", "@azure/mcp@latest", "server", "start"])
            ))
            _mcp_client.__enter__()
        except Exception as e:
            raise
    return _mcp_client

def _call_azure_tool(name, **kwargs):
    """Call an Azure MCP tool with the given arguments."""
    try:
        mcp_client = _get_mcp_client()
        tool_use_id = f"azure-{name}-{uuid.uuid4()}"
        
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
                        parsed_result = json.loads(item["text"])
                        return parsed_result
                    except json.JSONDecodeError:
                        # Return as text if not JSON
                        return item["text"]
        
        # If we got here, something went wrong
        return {"error": f"Error executing tool {name}", "result": result}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": f"Exception calling tool {name}: {str(e)}"}
