# gcp_tools.py
from strands import Agent, tool
from mcp import stdio_client, StdioServerParameters
from strands.tools.mcp import MCPClient
from strands_tools import shell
import json
import uuid
from model import get_model

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

@tool
def list_gcp_projects() -> dict:
    """
    List all Google Cloud Platform projects accessible with the current credentials.
    
    This tool connects to your GCP environment and retrieves a list of all projects
    that you have access to using your locally configured credentials.
    
    No parameters are required for this tool.
    
    Returns:
        A dictionary containing the list of projects with their IDs.
        Example: {"projects": ["project-id-1", "project-id-2"]}
    """
    return _call_gcp_tool("list-projects")

@tool
def select_gcp_project(project_id: str, region: str = None) -> dict:
    """
    Select a Google Cloud Platform project for subsequent operations.
    
    This tool sets the active GCP project for all future GCP tool calls.
    You must call this tool before using other GCP-specific tools.
    
    Args:
        project_id: The ID of the GCP project to use.
               Example: "my-project-123456"
        region: Optional. The GCP region to use. Defaults to us-central1 if not specified.
                Example: "us-east1"
    
    Returns:
        A dictionary confirming the selected project and region.
    """
    global _current_project, _current_region
    
    args = {"projectId": project_id}
    if region:
        args["region"] = region
        _current_region = region
    
    result = _call_gcp_tool("select-project", **args)
    
    # Store the current project ID
    if "error" not in result:
        _current_project = project_id
    
    return result

@tool
def get_gcp_billing_info(project_id: str = None) -> dict:
    """
    Get billing information for a Google Cloud Platform project.
    
    This tool retrieves detailed billing information for the specified GCP project,
    including billing account status, current charges, and payment methods.
    
    Args:
        project_id: Optional. The ID of the GCP project to get billing information for.
                  If not provided, uses the currently selected project.
    
    Returns:
        A dictionary containing the billing information.
    """
    args = {}
    if project_id:
        args["projectId"] = project_id
    
    return _call_gcp_tool("get-billing-info", **args)

@tool
def get_gcp_cost_forecast(project_id: str = None, months: int = 3) -> dict:
    """
    Get cost forecast for a Google Cloud Platform project.
    
    This tool provides a cost forecast for the specified GCP project,
    estimating future costs based on current usage patterns.
    
    Args:
        project_id: Optional. The ID of the GCP project to get the forecast for.
                  If not provided, uses the currently selected project.
        months: Optional. Number of months to forecast. Default is 3.
    
    Returns:
        A dictionary containing the cost forecast information.
    """
    args = {"months": months}
    if project_id:
        args["projectId"] = project_id
    
    return _call_gcp_tool("get-cost-forecast", **args)

@tool
def get_gcp_billing_budget(project_id: str = None) -> dict:
    """
    Get billing budgets for a Google Cloud Platform project.
    
    This tool retrieves information about any budget alerts set up for the
    specified GCP project, including budget amounts and alert thresholds.
    
    Args:
        project_id: Optional. The ID of the GCP project to get budget information for.
                  If not provided, uses the currently selected project.
    
    Returns:
        A dictionary containing the budget information.
    """
    args = {}
    if project_id:
        args["projectId"] = project_id
    
    return _call_gcp_tool("get-billing-budget", **args)

@tool
def list_gcp_gke_clusters(location: str = None) -> dict:
    """
    List all Google Kubernetes Engine (GKE) clusters in a GCP project.
    
    This tool retrieves information about all GKE clusters in the currently selected
    GCP project, including their names, locations, and status.
    
    Args:
        location: Optional. The region or zone to list clusters from.
                If not provided, lists clusters from all locations.
    
    Returns:
        A dictionary containing the list of GKE clusters.
    """
    args = {}
    if location:
        args["location"] = location
    
    return _call_gcp_tool("list-gke-clusters", **args)

@tool
def list_gcp_sql_instances() -> dict:
    """
    List all Cloud SQL instances in a GCP project.
    
    This tool retrieves information about all Cloud SQL instances in the currently
    selected GCP project, including their names, database types, and status.
    
    Returns:
        A dictionary containing the list of Cloud SQL instances.
    """
    return _call_gcp_tool("list-sql-instances")

@tool
def get_gcp_logs(filter_str: str = None, page_size: int = 10) -> dict:
    """
    Get Cloud Logging entries for a GCP project.
    
    This tool retrieves log entries from Cloud Logging for the currently selected
    GCP project, filtered by the specified criteria.
    
    Args:
        filter_str: Optional. Filter for the log entries using Cloud Logging query syntax.
                  Example: "resource.type=gce_instance"
        page_size: Optional. Maximum number of entries to return. Default is 10.
    
    Returns:
        A dictionary containing the log entries.
    """
    args = {"pageSize": page_size}
    if filter_str:
        args["filter"] = filter_str
    
    return _call_gcp_tool("get-logs", **args)

@tool
def use_gcp(prompt: str):
    """
    Tool Usage: Comprehensive GCP operations using specialized MCP tools and gcloud CLI commands.
    
    This tool provides access to GCP operations through a combination of specialized MCP tools
    and gcloud CLI commands via the shell tool. For any operations not covered by the MCP tools,
    it defaults to using gcloud CLI commands.
    """
    
    system_prompt = """
    You are a helpful GCP operations assistant with access to specialized GCP MCP tools and gcloud CLI commands.
    
    AVAILABLE SPECIALIZED MCP TOOLS (use these when applicable):
    - list_gcp_projects: List all accessible GCP projects
    - select_gcp_project: Set the active project for operations
    - get_gcp_billing_info: Get billing information for a project
    - get_gcp_cost_forecast: Get cost forecasts for a project
    - get_gcp_billing_budget: Get budget information for a project
    - list_gcp_gke_clusters: List GKE clusters in a project
    - list_gcp_sql_instances: List Cloud SQL instances in a project
    - get_gcp_logs: Get Cloud Logging entries with filters
    
    EXECUTION STRATEGY:
    1. First, check if the requested operation can be handled by one of the specialized MCP tools above
    2. If not, use gcloud CLI commands through the shell tool
    3. Always use the most appropriate tool for the task
    
    COMMAND PREVIEW REQUIREMENT (CRITICAL):
    - Before executing ANY shell command, you MUST explicitly state: "I will execute the following command: `command_here`"
    - This applies to ALL gcloud commands and shell operations
    - Format example: "I will execute the following command: `gcloud compute networks subnets list --filter='region:southamerica-west1' --project=my-project-id --format='table(name,region,ipCidrRange)'`"
    
    COMPREHENSIVE GCLOUD CLI COMMAND PATTERNS:
    
    COMPUTE ENGINE:
    * List instances: `gcloud compute instances list --project=PROJECT_ID --format="table(name,zone,status,machineType)"`
    * List subnets: `gcloud compute networks subnets list --filter="region:REGION_NAME" --project=PROJECT_ID --format="table(name,region,ipCidrRange)"`
    * List networks: `gcloud compute networks list --project=PROJECT_ID --format="table(name,mode,subnet_mode)"`
    * List firewalls: `gcloud compute firewall-rules list --project=PROJECT_ID --format="table(name,direction,priority,sourceRanges)"`
    * List regions: `gcloud compute regions list --project=PROJECT_ID --format="table(name,status)"`
    * List zones: `gcloud compute zones list --project=PROJECT_ID --format="table(name,region,status)"`
    * Describe instance: `gcloud compute instances describe INSTANCE_NAME --zone=ZONE --project=PROJECT_ID`
    
    STORAGE:
    * List buckets: `gcloud storage buckets list --project=PROJECT_ID --format="table(name,location,storageClass)"`
    * List objects in bucket: `gcloud storage ls gs://BUCKET_NAME`
    * Bucket details: `gcloud storage buckets describe gs://BUCKET_NAME`
    
    IAM & SECURITY:
    * List IAM policies: `gcloud projects get-iam-policy PROJECT_ID --format="table(bindings.role,bindings.members)"`
    * List service accounts: `gcloud iam service-accounts list --project=PROJECT_ID --format="table(email,displayName)"`
    * List roles: `gcloud iam roles list --project=PROJECT_ID --format="table(name,title)"`
    
    SERVICES & APIs:
    * List enabled services: `gcloud services list --enabled --project=PROJECT_ID --format="table(name,title)"`
    * List available services: `gcloud services list --available --project=PROJECT_ID`
    
    APP ENGINE & CLOUD FUNCTIONS:
    * List App Engine services: `gcloud app services list --project=PROJECT_ID`
    * List Cloud Functions: `gcloud functions list --project=PROJECT_ID --format="table(name,status,trigger)"`
    
    KUBERNETES & CONTAINERS:
    * List GKE clusters: `gcloud container clusters list --project=PROJECT_ID --format="table(name,location,status)"`
    * Get cluster credentials: `gcloud container clusters get-credentials CLUSTER_NAME --zone=ZONE --project=PROJECT_ID`
    
    PROJECT & ORGANIZATION:
    * Get project info: `gcloud projects describe PROJECT_ID`
    * List projects: `gcloud projects list --format="table(projectId,name,projectNumber)"`
    
    BEST PRACTICES FOR SHELL COMMANDS:
    - Always specify --project=PROJECT_ID in gcloud commands
    - Use --format="table(...)" for better readable output
    - Use --filter for targeted results when appropriate
    - Use --limit if you need to restrict results
    - Include relevant columns in table format for better information display
    
    WORKFLOW:
    1. Analyze the user's request
    2. Determine if a specialized MCP tool can handle it
    3. If yes, use the MCP tool
    4. If no, state the gcloud command you will execute: "I will execute the following command: `command`"
    5. Execute the gcloud CLI command via shell tool
    6. Present the results clearly to the user
    """
    
    agent = Agent(
        model=get_model(),
        system_prompt=system_prompt,
        tools=[
            list_gcp_projects,
            select_gcp_project,
            get_gcp_billing_info,
            get_gcp_cost_forecast,
            get_gcp_billing_budget,
            list_gcp_gke_clusters,
            list_gcp_sql_instances,
            get_gcp_logs,
            shell,
        ])

    result = agent(prompt)
    return result