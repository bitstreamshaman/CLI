""" 
GCP SQL Tools 
"""

from strands import tool
from ..utils import _call_gcp_tool

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
