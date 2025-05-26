from use_azure.utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_ai_search_services(resource_group: str = None) -> dict:
    """
    List Azure AI Search services in the subscription or a specific resource group.
    
    This tool retrieves information about all Azure AI Search services accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter search services.
                       If not provided, lists services from all resource groups.
    
    Returns:
        A dictionary containing the list of Azure AI Search services.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-search-service-list", **args)

@tool
def list_azure_ai_search_indexes(service_name: str) -> dict:
    """
    List indexes in an Azure AI Search service.
    
    This tool retrieves all search indexes within the specified Azure AI Search service.
    
    Args:
        service_name: The name of the Azure AI Search service.
    
    Returns:
        A dictionary containing the list of search indexes and their configurations.
    """
    return _call_azure_tool("azmcp-search-index-list", serviceName=service_name)

@tool
def describe_azure_ai_search_index(service_name: str, index_name: str) -> dict:
    """
    Get detailed description of an Azure AI Search index.
    
    This tool retrieves comprehensive information about the specified search index,
    including its schema, fields, analyzers, and configuration details.
    
    Args:
        service_name: The name of the Azure AI Search service.
        index_name: The name of the search index to describe.
    
    Returns:
        A dictionary containing the detailed index description and schema.
    """
    return _call_azure_tool("azmcp-search-index-describe", 
                           serviceName=service_name, 
                           indexName=index_name)

@tool
def search_azure_ai_search(service_name: str, index_name: str, query: str, top: int = 10) -> dict:
    """
    Search an Azure AI Search index.
    
    This tool executes a search query against the specified search index.
    
    Args:
        service_name: The name of the Azure AI Search service.
        index_name: The name of the search index.
        query: The search query string.
        top: Optional. Maximum number of results to return. Default is 10.
    
    Returns:
        A dictionary containing the search results.
    """
    return _call_azure_tool("azmcp-search-index-query", 
                           serviceName=service_name, 
                           indexName=index_name, 
                           query=query, 
                           top=top)