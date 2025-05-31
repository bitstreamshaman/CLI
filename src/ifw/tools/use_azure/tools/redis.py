from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_redis_caches(resource_group: str = None) -> dict:
    """
    List Azure Redis Cache instances in the subscription or a specific resource group.
    
    This tool retrieves information about all Redis Cache instances accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter Redis caches.
                       If not provided, lists caches from all resource groups.
    
    Returns:
        A dictionary containing the list of Redis Cache instances.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-redis-cache-list", **args)

@tool
def list_azure_redis_access_policies(cache_name: str, resource_group: str = None) -> dict:
    """
    List access policies for an Azure Redis Cache instance.
    
    This tool retrieves all access policies configured for the specified Redis Cache.
    
    Args:
        cache_name: The name of the Redis Cache instance.
        resource_group: Optional. The name of the resource group containing the cache.
    
    Returns:
        A dictionary containing the list of access policies for the Redis Cache.
    """
    args = {"cacheName": cache_name}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-redis-cache-accesspolicy-list", **args)

@tool
def list_azure_redis_clusters(resource_group: str = None) -> dict:
    """
    List Azure Redis Enterprise clusters in the subscription or a specific resource group.
    
    This tool retrieves information about all Redis Enterprise clusters accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter Redis clusters.
                       If not provided, lists clusters from all resource groups.
    
    Returns:
        A dictionary containing the list of Redis Enterprise clusters.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-redis-cluster-list", **args)

@tool
def list_azure_redis_cluster_databases(cluster_name: str, resource_group: str = None) -> dict:
    """
    List databases in an Azure Redis Enterprise cluster.
    
    This tool retrieves all databases within the specified Redis Enterprise cluster.
    
    Args:
        cluster_name: The name of the Redis Enterprise cluster.
        resource_group: Optional. The name of the resource group containing the cluster.
    
    Returns:
        A dictionary containing the list of databases in the Redis cluster.
    """
    args = {"clusterName": cluster_name}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-redis-cluster-database-list", **args)
