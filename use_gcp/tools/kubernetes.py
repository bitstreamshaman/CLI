""" 
GCP Kubernetes Engine Tools 
"""

from strands import tool
from ..utils import _call_gcp_tool

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
