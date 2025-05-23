""" 
GCP Logging Tools 
"""

from strands import tool
from ..utils import _call_gcp_tool

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
        A dicaining tool files (kubernetes.py, sql.py,tionary containing the log entries.
    """
    args = {"pageSize": page_size}
    if filter_str:
        args["filter"] = filter_str
    
    return _call_gcp_tool("get-logs", **args)