"""
GCP Billing and cost management tools.
"""

from strands import tool
from ..utils import _call_gcp_tool

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