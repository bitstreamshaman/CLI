#!/usr/bin/env python3
"""
Script to discover available tools in the Docker MCP Server.
Run this while the Docker MCP server is running or let it start automatically.

Usage:
1. Make sure docker-mcp is available via uvx: uvx docker-mcp
2. Run: python discover_docker_mcp_tools.py
"""

from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient

def discover_docker_mcp_tools():
    """Discover and list all available tools from the Docker MCP server."""
    
    print("🔍 Discovering Docker MCP Server tools...")
    print("=" * 60)
    
    try:
        # Create MCP client connection
        print("📡 Connecting to Docker MCP server...")
        mcp_client = MCPClient(lambda: stdio_client(
            StdioServerParameters(command="uvx", args=["docker-mcp"])
        ))
        
        with mcp_client:
            print("✅ Connected successfully!")
            print()
            
            # List all available tools
            print("📋 Listing available tools...")
            tools = mcp_client.list_tools_sync()
            
            if not tools:
                print("❌ No tools found!")
                return
            
            print(f"✅ Found {len(tools)} tools:")
            print()
            
            # Display tools in a nice format
            for i, tool in enumerate(tools, 1):
                print(f"{i:2d}. Tool Name: '{tool.tool_name}'")
                if hasattr(tool, 'tool_spec') and tool.tool_spec:
                    spec = tool.tool_spec
                    if hasattr(spec, 'description') and spec.description:
                        print(f"    Description: {spec.description}")
                    if hasattr(spec, 'inputSchema') and spec.inputSchema:
                        schema = spec.inputSchema
                        if hasattr(schema, 'properties') and schema.properties:
                            props = list(schema.properties.keys())
                            print(f"    Parameters: {', '.join(props) if props else 'None'}")
                print()
            
            # Also print tool names in a simple list
            print("=" * 60)
            print("📄 All tool names:")
            for tool in tools:
                print(f"  - {tool.tool_name}")
            print("=" * 60)
            
            # Create a mapping for Docker tools
            print("🔧 Tool name mapping for your code:")
            print("DOCKER_TOOL_NAME_MAPPING = {")
            for tool in tools:
                tool_name = tool.tool_name
                if 'ps' in tool_name.lower() or 'list' in tool_name.lower() and 'container' in tool_name.lower():
                    print(f"    'list_containers': '{tool_name}',")
                elif 'exec' in tool_name.lower():
                    print(f"    'execute_command': '{tool_name}',")
                elif 'logs' in tool_name.lower():
                    print(f"    'get_logs': '{tool_name}',")
                elif 'images' in tool_name.lower() or 'image' in tool_name.lower() and 'list' in tool_name.lower():
                    print(f"    'list_images': '{tool_name}',")
                elif 'inspect' in tool_name.lower():
                    print(f"    'inspect_container': '{tool_name}',")
                elif 'start' in tool_name.lower():
                    print(f"    'start_container': '{tool_name}',")
                elif 'stop' in tool_name.lower():
                    print(f"    'stop_container': '{tool_name}',")
                elif 'restart' in tool_name.lower():
                    print(f"    'restart_container': '{tool_name}',")
                elif 'remove' in tool_name.lower() or 'rm' in tool_name.lower():
                    print(f"    'remove_container': '{tool_name}',")
                elif 'pull' in tool_name.lower():
                    print(f"    'pull_image': '{tool_name}',")
                elif 'build' in tool_name.lower():
                    print(f"    'build_image': '{tool_name}',")
                elif 'run' in tool_name.lower():
                    print(f"    'run_container': '{tool_name}',")
                elif 'stats' in tool_name.lower():
                    print(f"    'container_stats': '{tool_name}',")
                elif 'network' in tool_name.lower():
                    print(f"    'list_networks': '{tool_name}',")
                elif 'volume' in tool_name.lower():
                    print(f"    'list_volumes': '{tool_name}',")
                else:
                    # Generic mapping for unrecognized tools
                    clean_name = tool_name.replace('-', '_').replace(' ', '_').lower()
                    print(f"    '{clean_name}': '{tool_name}',")
            print("}")
            print("=" * 60)
            
            # Show detailed parameter information
            print("🔍 Detailed tool specifications:")
            for tool in tools:
                print(f"\nTool: {tool.tool_name}")
                if hasattr(tool, 'tool_spec') and tool.tool_spec:
                    spec = tool.tool_spec
                    if hasattr(spec, 'inputSchema') and spec.inputSchema:
                        schema = spec.inputSchema
                        if hasattr(schema, 'properties') and schema.properties:
                            print("  Parameters:")
                            for param_name, param_info in schema.properties.items():
                                param_type = param_info.get('type', 'unknown')
                                param_desc = param_info.get('description', 'No description')
                                required = param_name in schema.get('required', [])
                                req_marker = " (required)" if required else " (optional)"
                                print(f"    - {param_name} ({param_type}){req_marker}: {param_desc}")
            print("=" * 60)
            
    except FileNotFoundError:
        print("❌ Error: uvx or docker-mcp command not found.")
        print("Make sure uvx is installed and docker-mcp is available.")
        print("Install uvx with: pip install uv")
        print("Then run: uvx docker-mcp (to test if it works)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Troubleshooting tips:")
        print("1. Make sure Docker is running")
        print("2. Ensure uvx is installed: pip install uv")
        print("3. Test docker-mcp availability: uvx docker-mcp")
        print("4. Check that docker-mcp can connect to Docker daemon")

if __name__ == "__main__":
    discover_docker_mcp_tools()