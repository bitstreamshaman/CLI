# docker_tools.py
from strands import Agent, tool
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient
from strands_tools import shell
import json
import uuid
import logging
from ..model import get_model

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Storage for our MCP client to maintain connection
_mcp_client = None

def _get_mcp_client():
    """Get or create the MCP client connection."""
    global _mcp_client
    if _mcp_client is None:
        logger.info("🔌 Creating new Docker MCP client connection...")
        try:
            _mcp_client = MCPClient(lambda: stdio_client(
                StdioServerParameters(command="uvx", args=["docker-mcp"])
            ))
            _mcp_client.__enter__()
            logger.info("✅ Docker MCP client connected successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create Docker MCP client: {e}")
            raise
    else:
        logger.debug("♻️ Reusing existing Docker MCP client connection")
    return _mcp_client

def _call_docker_tool(name, **kwargs):
    """Call a Docker MCP tool with the given arguments."""
    logger.info(f"🐳 Calling Docker MCP tool: {name}")
    logger.info(f"📋 Tool arguments: {json.dumps(kwargs, indent=2)}")
    
    mcp_client = _get_mcp_client()
    tool_use_id = f"docker-{name}-{uuid.uuid4()}"
    
    # Make sure the name doesn't have angle brackets
    clean_name = name.strip('<>') if name.startswith('<') and name.endswith('>') else name
    
    logger.info(f"🔧 Executing tool '{clean_name}' with ID: {tool_use_id}")
    
    try:
        # Call the tool
        result = mcp_client.call_tool_sync(
            tool_use_id=tool_use_id,
            name=clean_name,  # Use the clean name
            arguments=kwargs
        )
        
        logger.info(f"📨 Raw MCP response: {json.dumps(result, indent=2) if result else 'None'}")
        
        # Process the result
        if result and result.get("status") == "success" and result.get("content"):
            logger.info("✅ Tool execution successful, processing content...")
            # Extract the content
            for item in result.get("content", []):
                if "text" in item:
                    try:
                        # Try to parse as JSON
                        parsed_result = json.loads(item["text"])
                        logger.info(f"📊 Parsed JSON result: {json.dumps(parsed_result, indent=2)}")
                        return parsed_result
                    except json.JSONDecodeError:
                        # Return as text if not JSON
                        logger.info(f"📝 Text result: {item['text']}")
                        return item["text"]
        
        # If we got here, something went wrong
        error_result = {"error": f"Error executing tool {name}", "result": result}
        logger.warning(f"⚠️ Tool execution failed: {json.dumps(error_result, indent=2)}")
        return error_result
        
    except Exception as e:
        error_msg = f"Exception calling Docker MCP tool {name}: {str(e)}"
        logger.error(f"💥 {error_msg}")
        return {"error": error_msg, "exception": str(e)}

@tool
def list_docker_containers(all: bool = True) -> dict:
    """
    List all Docker containers using the Docker MCP server.
    
    This tool retrieves information about Docker containers running on the system.
    
    Args:
        all: Optional. Whether to list all containers (including stopped ones).
             Default is True. Set to False to list only running containers.
    
    Returns:
        A dictionary containing the list of containers with their details.
    """
    logger.info(f"🐳 list_docker_containers called with all={all}")
    args = {"all": all}
    result = _call_docker_tool("list-containers", **args)
    logger.info(f"📋 list_docker_containers returning: {type(result).__name__}")
    return result

@tool
def create_docker_container(image: str, name: str = None, ports: dict = None, 
                          volumes: dict = None, environment: dict = None, 
                          command: str = None) -> dict:
    """
    Create a new Docker container using the Docker MCP server.
    
    This tool creates a new Docker container with the specified configuration.
    
    Args:
        image: The Docker image to use for the container.
               Example: "nginx:latest"
        name: Optional. Name for the container.
              Example: "my-web-server"
        ports: Optional. Port mappings as a dictionary.
               Example: {"80": "8080"} maps container port 80 to host port 8080
        volumes: Optional. Volume mounts as a dictionary.
                Example: {"/host/path": "/container/path"}
        environment: Optional. Environment variables as a dictionary.
                    Example: {"ENV_VAR": "value"}
        command: Optional. Command to run in the container.
                Example: "/bin/bash"
    
    Returns:
        A dictionary containing the container creation result.
    """
    logger.info(f"🚀 create_docker_container called with image={image}, name={name}")
    args = {"image": image}
    
    if name:
        args["name"] = name
    if ports:
        args["ports"] = ports
        logger.info(f"🔌 Port mappings: {ports}")
    if volumes:
        args["volumes"] = volumes
        logger.info(f"💾 Volume mounts: {volumes}")
    if environment:
        args["environment"] = environment
        logger.info(f"🔧 Environment variables: {environment}")
    if command:
        args["command"] = command
        logger.info(f"⚙️ Custom command: {command}")
    
    result = _call_docker_tool("create-container", **args)
    logger.info(f"🚀 create_docker_container returning: {type(result).__name__}")
    return result

@tool
def get_docker_logs(container: str, lines: int = 100, follow: bool = False) -> dict:
    """
    Get logs from a Docker container using the Docker MCP server.
    
    This tool retrieves log output from the specified Docker container.
    
    Args:
        container: The container name or ID to get logs from.
                  Example: "my-web-server" or "a1b2c3d4e5f6"
        lines: Optional. Number of log lines to retrieve. Default is 100.
        follow: Optional. Whether to follow log output (stream). Default is False.
    
    Returns:
        A dictionary containing the container logs.
    """
    logger.info(f"📜 get_docker_logs called for container={container}, lines={lines}, follow={follow}")
    args = {
        "container": container,
        "lines": lines,
        "follow": follow
    }
    
    result = _call_docker_tool("get-logs", **args)
    logger.info(f"📜 get_docker_logs returning: {type(result).__name__}")
    return result

@tool
def deploy_docker_compose(compose_file: str = "docker-compose.yml", 
                         project_name: str = None, detach: bool = True) -> dict:
    """
    Deploy a Docker Compose application using the Docker MCP server.
    
    This tool deploys services defined in a Docker Compose file.
    
    Args:
        compose_file: Optional. Path to the Docker Compose file.
                     Default is "docker-compose.yml"
        project_name: Optional. Name for the Docker Compose project.
                     If not provided, uses the directory name.
        detach: Optional. Whether to run in detached mode. Default is True.
    
    Returns:
        A dictionary containing the deployment result.
    """
    logger.info(f"🐙 deploy_docker_compose called with compose_file={compose_file}, project_name={project_name}, detach={detach}")
    args = {
        "compose_file": compose_file,
        "detach": detach
    }
    
    if project_name:
        args["project_name"] = project_name
    
    result = _call_docker_tool("deploy-compose", **args)
    logger.info(f"🐙 deploy_docker_compose returning: {type(result).__name__}")
    return result

@tool
def use_docker(prompt: str):
    """
    Tool Usage: Comprehensive Docker operations using specialized MCP tools and Docker CLI commands.
    
    This tool provides access to Docker operations through a combination of specialized MCP tools
    and Docker CLI commands via the shell tool. For any operations not covered by the MCP tools,
    it defaults to using Docker CLI commands.
    """
    
    logger.info(f"🤖 use_docker called with prompt: {prompt}")
    
    system_prompt = """
    You are a helpful Docker operations assistant with access to specialized Docker MCP tools and Docker CLI commands.
    
    LOGGING REQUIREMENT (CRITICAL):
    - Before using ANY tool (MCP or shell), you MUST log what you're about to do
    - Format: "I am using the [TOOL_NAME] tool to [ACTION_DESCRIPTION]"
    - Example: "I am using the list_docker_containers tool to check all containers on the system"
    - Example: "I am using the shell tool to execute: docker ps -a --format 'table {{.Names}}\t{{.Status}}'"
    
    AVAILABLE SPECIALIZED MCP TOOLS (use these when applicable):
    - list_docker_containers: List all Docker containers (running and stopped)
    - create_docker_container: Create a new Docker container with specified configuration
    - get_docker_logs: Get logs from a specific container
    - deploy_docker_compose: Deploy services using Docker Compose
    
    EXECUTION STRATEGY:
    1. First, check if the requested operation can be handled by one of the specialized MCP tools above
    2. If not, use Docker CLI commands through the shell tool
    3. Always use the most appropriate tool for the task
    4. ALWAYS announce which tool you're using and why before executing it
    
    COMMAND PREVIEW REQUIREMENT (CRITICAL):
    - Before executing ANY shell command, you MUST explicitly state: "I will execute the following command: `command_here`"
    - This applies to ALL docker commands and shell operations
    - Format example: "I will execute the following command: `docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'`"
    
    COMPREHENSIVE DOCKER CLI COMMAND PATTERNS:
    
    CONTAINER MANAGEMENT:
    * List all containers: `docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"`
    * List running containers: `docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"`
    * Start container: `docker start CONTAINER_NAME`
    * Stop container: `docker stop CONTAINER_NAME`
    * Restart container: `docker restart CONTAINER_NAME`
    * Remove container: `docker rm CONTAINER_NAME`
    * Execute command in container: `docker exec -it CONTAINER_NAME COMMAND`
    * Inspect container: `docker inspect CONTAINER_NAME`
    * Container stats: `docker stats CONTAINER_NAME --no-stream`
    * Copy files: `docker cp SOURCE CONTAINER:DEST` or `docker cp CONTAINER:SOURCE DEST`
    
    IMAGE MANAGEMENT:
    * List images: `docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"`
    * Pull image: `docker pull IMAGE_NAME:TAG`
    * Build image: `docker build -t IMAGE_NAME:TAG PATH`
    * Remove image: `docker rmi IMAGE_NAME:TAG`
    * Image history: `docker history IMAGE_NAME`
    * Inspect image: `docker inspect IMAGE_NAME`
    * Tag image: `docker tag SOURCE_IMAGE:TAG TARGET_IMAGE:TAG`
    
    NETWORK MANAGEMENT:
    * List networks: `docker network ls`
    * Create network: `docker network create NETWORK_NAME`
    * Connect container to network: `docker network connect NETWORK_NAME CONTAINER_NAME`
    * Disconnect container: `docker network disconnect NETWORK_NAME CONTAINER_NAME`
    * Inspect network: `docker network inspect NETWORK_NAME`
    * Remove network: `docker network rm NETWORK_NAME`
    
    VOLUME MANAGEMENT:
    * List volumes: `docker volume ls`
    * Create volume: `docker volume create VOLUME_NAME`
    * Inspect volume: `docker volume inspect VOLUME_NAME`
    * Remove volume: `docker volume rm VOLUME_NAME`
    * Prune unused volumes: `docker volume prune`
    
    DOCKER COMPOSE:
    * Start services: `docker-compose up -d`
    * Stop services: `docker-compose down`
    * View logs: `docker-compose logs SERVICE_NAME`
    * Scale service: `docker-compose up --scale SERVICE_NAME=3`
    * List services: `docker-compose ps`
    * Execute in service: `docker-compose exec SERVICE_NAME COMMAND`
    
    SYSTEM & CLEANUP:
    * System info: `docker system info`
    * Disk usage: `docker system df`
    * System prune: `docker system prune`
    * Remove unused containers: `docker container prune`
    * Remove unused images: `docker image prune`
    
    LOGS & MONITORING:
    * Container logs: `docker logs CONTAINER_NAME --tail 100`
    * Follow logs: `docker logs -f CONTAINER_NAME`
    * System events: `docker events --since '1h'`
    
    BEST PRACTICES FOR SHELL COMMANDS:
    - Use --format for better readable output when available
    - Include relevant columns in table format for better information display
    - Use appropriate flags like -a for all, -q for quiet output
    - Always specify container/image names clearly
    - Use --tail for log commands to limit output
    
    WORKFLOW:
    1. Analyze the user's request
    2. Determine if a specialized MCP tool can handle it
    3. Announce which tool you will use and why: "I am using the [TOOL_NAME] tool to [ACTION]"
    4. If using shell, state the command: "I will execute the following command: `command`"
    5. Execute the appropriate tool
    6. Present the results clearly to the user
    
    CONTAINER CREATION EXAMPLES:
    - Simple web server: `docker run -d --name web-server -p 8080:80 nginx:latest`
    - Database with volume: `docker run -d --name mysql-db -e MYSQL_ROOT_PASSWORD=password -v mysql-data:/var/lib/mysql mysql:8.0`
    - Interactive container: `docker run -it --name ubuntu-container ubuntu:latest /bin/bash`
    
    TROUBLESHOOTING:
    - Check if Docker daemon is running
    - Verify container/image names are correct
    - Check port conflicts for new containers
    - Ensure sufficient disk space for operations
    - Check network connectivity for image pulls
    """
    
    agent = Agent(
        model=get_model(),
        system_prompt=system_prompt,
        tools=[
            list_docker_containers,
            create_docker_container,
            get_docker_logs,
            deploy_docker_compose,
            shell,
        ])

    logger.info("🚀 Starting Docker agent execution...")
    result = agent(prompt)
    logger.info(f"✅ Docker agent execution completed, result type: {type(result).__name__}")
    return result