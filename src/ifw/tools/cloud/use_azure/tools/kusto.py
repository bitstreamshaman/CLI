from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_kusto_clusters(resource_group: str = None) -> dict:
    """
    List Azure Data Explorer (Kusto) clusters in the subscription or a specific resource group.
    
    This tool retrieves information about all Kusto clusters accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter clusters.
                       If not provided, lists clusters from all resource groups.
    
    Returns:
        A dictionary containing the list of Kusto clusters.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-kusto-cluster-list", **args)

@tool
def query_azure_kusto(cluster_name: str, database_name: str, query: str) -> dict:
    """
    Query Azure Data Explorer (Kusto) using KQL.
    
    This tool executes a KQL query against the specified Kusto database.
    
    Args:
        cluster_name: The name of the Kusto cluster.
        database_name: The name of the database.
        query: The KQL query to execute.
               Example: "StormEvents | take 10"
    
    Returns:
        A dictionary containing the query results.
    """
    return _call_azure_tool("azmcp-kusto-query", 
                           clusterName=cluster_name, 
                           databaseName=database_name, 
                           query=query)

@tool
def list_azure_kusto_databases(cluster_name: str) -> dict:
    """
    List databases in an Azure Data Explorer (Kusto) cluster.
    
    This tool retrieves all databases within the specified Kusto cluster.
    
    Args:
        cluster_name: The name of the Kusto cluster.
    
    Returns:
        A dictionary containing the list of databases in the Kusto cluster.
    """
    return _call_azure_tool("azmcp-kusto-database-list", 
                           clusterName=cluster_name)

@tool
def get_azure_kusto_table_schema(cluster_name: str, database_name: str, table_name: str) -> dict:
    """
    Get schema information for an Azure Data Explorer (Kusto) table.
    
    This tool retrieves the schema details for the specified Kusto table,
    including column names, data types, and other metadata.
    
    Args:
        cluster_name: The name of the Kusto cluster.
        database_name: The name of the database.
        table_name: The name of the table.
    
    Returns:
        A dictionary containing the table schema information.
    """
    return _call_azure_tool("azmcp-kusto-table-schema", 
                           clusterName=cluster_name, 
                           databaseName=database_name, 
                           tableName=table_name)

@tool
def get_azure_kusto_sample_data(cluster_name: str, database_name: str, table_name: str, count: int = 10) -> dict:
    """
    Get sample data from an Azure Data Explorer (Kusto) table.
    
    This tool retrieves sample records from the specified Kusto table for data exploration.
    
    Args:
        cluster_name: The name of the Kusto cluster.
        database_name: The name of the database.
        table_name: The name of the table to sample from.
        count: Optional. Number of sample records to retrieve. Default is 10.
    
    Returns:
        A dictionary containing the sample data from the Kusto table.
    """
    return _call_azure_tool("azmcp-kusto-sample", 
                           clusterName=cluster_name, 
                           databaseName=database_name, 
                           tableName=table_name,
                           count=count)

@tool
def get_azure_kusto_cluster_details(cluster_name: str) -> dict:
    """
    Get detailed information about an Azure Data Explorer (Kusto) cluster.
    
    This tool retrieves comprehensive details about the specified Kusto cluster,
    including configuration, status, and properties.
    
    Args:
        cluster_name: The name of the Kusto cluster.
    
    Returns:
        A dictionary containing the detailed cluster information.
    """
    return _call_azure_tool("azmcp-kusto-cluster-get", 
                           clusterName=cluster_name)

@tool
def list_azure_kusto_tables(cluster_name: str, database_name: str) -> dict:
    """
    List tables in an Azure Data Explorer (Kusto) database.
    
    This tool retrieves all tables within the specified Kusto database.
    
    Args:
        cluster_name: The name of the Kusto cluster.
        database_name: The name of the database.
    
    Returns:
        A dictionary containing the list of tables in the Kusto database.
    """
    return _call_azure_tool("azmcp-kusto-table-list", 
                           clusterName=cluster_name, 
                           databaseName=database_name)