from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_log_analytics_workspaces(resource_group: str = None) -> dict:
    """
    List Azure Log Analytics workspaces in the subscription or a specific resource group.
    
    This tool retrieves information about all Log Analytics workspaces accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter workspaces.
                       If not provided, lists workspaces from all resource groups.
    
    Returns:
        A dictionary containing the list of Log Analytics workspaces.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-monitor-workspace-list", **args)

@tool
def query_azure_log_analytics(workspace_id: str, query: str, timespan: str = "P1D") -> dict:
    """
    Query Azure Log Analytics using KQL (Kusto Query Language).
    
    This tool executes a KQL query against the specified Log Analytics workspace.
    
    Args:
        workspace_id: The ID of the Log Analytics workspace.
        query: The KQL query to execute.
               Example: "AzureActivity | where TimeGenerated > ago(1h) | limit 10"
        timespan: Optional. The timespan for the query in ISO 8601 duration format.
                 Default is "P1D" (1 day). Example: "PT1H" (1 hour), "P7D" (7 days)
    
    Returns:
        A dictionary containing the query results.
    """
    return _call_azure_tool("azmcp-monitor-log-query", 
                           workspaceId=workspace_id, 
                           query=query, 
                           timespan=timespan)

@tool
def list_azure_monitor_table_types(workspace_id: str) -> dict:
    """
    List table types available in an Azure Monitor Log Analytics workspace.
    
    This tool retrieves the different types of tables (standard, custom, etc.) 
    available in the specified Log Analytics workspace.
    
    Args:
        workspace_id: The ID of the Log Analytics workspace.
    
    Returns:
        A dictionary containing the list of table types in the workspace.
    """
    return _call_azure_tool("azmcp-monitor-table-type-list", 
                           workspaceId=workspace_id)

@tool
def list_azure_monitor_tables(workspace_id: str) -> dict:
    """
    List tables available in an Azure Monitor Log Analytics workspace.
    
    This tool retrieves all tables that can be queried within the specified 
    Log Analytics workspace.
    
    Args:
        workspace_id: The ID of the Log Analytics workspace.
    
    Returns:
        A dictionary containing the list of available tables in the workspace.
    """
    return _call_azure_tool("azmcp-monitor-table-list", 
                           workspaceId=workspace_id)

@tool
def get_azure_monitor_health_models(entity_id: str, entity_type: str = None) -> dict:
    """
    Get health information for Azure Monitor entities using health models.
    
    This tool retrieves health status and models for specified Azure resources or entities.
    
    Args:
        entity_id: The ID of the entity to get health information for.
        entity_type: Optional. The type of entity (e.g., 'resource', 'subscription').
    
    Returns:
        A dictionary containing the health model information for the entity.
    """
    args = {"entityId": entity_id}
    if entity_type:
        args["entityType"] = entity_type
    
    return _call_azure_tool("azmcp-monitor-healthmodels-entity-gethealth", **args)