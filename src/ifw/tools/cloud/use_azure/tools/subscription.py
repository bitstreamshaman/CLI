from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_subscriptions() -> dict:
    """
    List all Azure subscriptions accessible with the current credentials.
    
    This tool connects to your Azure environment and retrieves a list of all subscriptions
    that you have access to using your locally configured credentials.
    
    No parameters are required for this tool.
    
    Returns:
        A dictionary containing the list of subscriptions with their IDs and names.
        Example: {"subscriptions": [{"id": "sub-id-1", "name": "Subscription 1"}]}
    """
    return _call_azure_tool("azmcp-subscription-list")

@tool
def list_azure_resource_groups(subscription_id: str = None) -> dict:
    """
    List all Azure resource groups in the current subscription.
    
    This tool connects to your Azure environment and retrieves a list of all resource groups
    that you have access to using your locally configured credentials.
    
    Args:
        subscription_id: Optional. The Azure subscription ID to list resource groups from.
                        If not provided, will try to use the default subscription.
    
    Returns:
        A dictionary containing the list of resource groups with their names and locations.
        Example: {"resource_groups": ["rg-1", "rg-2"]}
    """
    args = {}
    if subscription_id:
        args["subscription"] = subscription_id
    
    return _call_azure_tool("azmcp-group-list", **args)