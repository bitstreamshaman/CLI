"""
GCP Project management tools.
"""

from strands import tool
from ..utils import _call_gcp_tool, set_current_project, set_current_region

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
    args = {"projectId": project_id}
    if region:
        args["region"] = region
        set_current_region(region)
    
    result = _call_gcp_tool("select-project", **args)
    
    # Store the current project ID
    if "error" not in result:
        set_current_project(project_id)
    
    return result

@tool
def get_gcp_project_info(project_id: str = None) -> dict:
    """
    Get detailed information about a Google Cloud Platform project.
    
    This tool retrieves comprehensive information about the specified GCP project,
    including metadata, labels, and project settings.
    
    Args:
        project_id: Optional. The ID of the GCP project to get information for.
                  If not provided, uses the currently selected project.
    
    Returns:
        A dictionary containing the project information.
    """
    args = {}
    if project_id:
        args["projectId"] = project_id
    
    return _call_gcp_tool("get-project-info", **args)
    

