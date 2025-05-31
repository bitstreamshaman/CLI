from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_cosmosdb_accounts(resource_group: str = None) -> dict:
    """
    List Azure Cosmos DB accounts in the subscription or a specific resource group.
    
    This tool retrieves information about all Cosmos DB accounts accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter Cosmos DB accounts.
                       If not provided, lists accounts from all resource groups.
    
    Returns:
        A dictionary containing the list of Cosmos DB accounts.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-cosmos-account-list", **args)

@tool
def list_azure_cosmosdb_databases(account_name: str) -> dict:
    """
    List databases in an Azure Cosmos DB account.
    
    This tool retrieves all databases within the specified Cosmos DB account.
    
    Args:
        account_name: The name of the Azure Cosmos DB account.
    
    Returns:
        A dictionary containing the list of databases in the Cosmos DB account.
    """
    return _call_azure_tool("azmcp-cosmos-database-list", accountName=account_name)

@tool
def list_azure_cosmosdb_containers(account_name: str, database_name: str) -> dict:
    """
    List containers in an Azure Cosmos DB database.
    
    This tool retrieves all containers within the specified Cosmos DB database.
    
    Args:
        account_name: The name of the Azure Cosmos DB account.
        database_name: The name of the database.
    
    Returns:
        A dictionary containing the list of containers in the Cosmos DB database.
    """
    return _call_azure_tool("azmcp-cosmos-database-container-list", 
                           accountName=account_name, 
                           databaseName=database_name)

@tool
def query_azure_cosmosdb(account_name: str, database_name: str, container_name: str, query: str) -> dict:
    """
    Execute a SQL query against an Azure Cosmos DB container.
    
    This tool runs a SQL query against the specified Cosmos DB container and returns the results.
    
    Args:
        account_name: The name of the Azure Cosmos DB account.
        database_name: The name of the database.
        container_name: The name of the container.
        query: The SQL query to execute.
               Example: "SELECT * FROM c WHERE c.category = 'electronics'"
    
    Returns:
        A dictionary containing the query results.
    """
    return _call_azure_tool("azmcp-cosmos-database-container-item-query", 
                           accountName=account_name, 
                           databaseName=database_name, 
                           containerName=container_name, 
                           query=query)