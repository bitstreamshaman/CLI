from use_azure.utils import _call_azure_tool
from strands.tools import tool


@tool
def get_azure_best_practices(service_type: str = None) -> dict:
    """
    Get Azure best practices recommendations.
    
    This tool retrieves best practice recommendations for Azure services and configurations.
    
    Args:
        service_type: Optional. The specific Azure service type to get best practices for.
                     If not provided, returns general Azure best practices.
    
    Returns:
        A dictionary containing the best practices recommendations.
    """
    args = {}
    if service_type:
        args["serviceType"] = service_type
    
    return _call_azure_tool("azmcp-bestpractices-get", **args)