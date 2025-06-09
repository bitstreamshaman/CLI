from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def get_azure_postgres_table_schema(server_name: str, database_name: str, table_name: str) -> dict:
    """
    Get schema for a table in an Azure PostgreSQL database.
    
    This tool retrieves the schema information for the specified table.
    
    Args:
        server_name: The name of the Azure PostgreSQL server.
        database_name: The name of the database.
        table_name: The name of the table.
    
    Returns:
        A dictionary containing the table schema information.
    """
    return _call_azure_tool("azmcp-postgres-table-schema", 
                           serverName=server_name, 
                           databaseName=database_name, 
                           tableName=table_name)

@tool
def list_azure_postgres_tables(server_name: str, database_name: str) -> dict:
    """
    List tables in an Azure PostgreSQL database.
    
    This tool retrieves all tables within the specified PostgreSQL database.
    
    Args:
        server_name: The name of the Azure PostgreSQL server.
        database_name: The name of the database.
    
    Returns:
        A dictionary containing the list of tables in the database.
    """
    return _call_azure_tool("azmcp-postgres-table-list", 
                           serverName=server_name, 
                           databaseName=database_name)

@tool
def get_azure_postgres_server_parameters(server_name: str) -> dict:
    """
    Get parameters for an Azure PostgreSQL server.
    
    This tool retrieves the parameters for the specified PostgreSQL server.
    
    Args:
        server_name: The name of the Azure PostgreSQL server.
    
    Returns:
        A dictionary containing the server parameters.
    """
    return _call_azure_tool("azmcp-postgres-server-param", serverName=server_name)

@tool
def list_azure_postgres_servers(resource_group: str = None) -> dict:
    """
    List Azure PostgreSQL servers in the subscription or a specific resource group.
    
    This tool retrieves information about all PostgreSQL servers accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter PostgreSQL servers.
                       If not provided, lists servers from all resource groups.
    
    Returns:
        A dictionary containing the list of PostgreSQL servers.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-postgres-server-list", **args)

@tool
def get_azure_postgres_server_config(server_name: str) -> dict:
    """
    Get configuration settings for an Azure PostgreSQL server.
    
    This tool retrieves the configuration settings for the specified PostgreSQL server.
    
    Args:
        server_name: The name of the Azure PostgreSQL server.
    
    Returns:
        A dictionary containing the server configuration settings.
    """
    return _call_azure_tool("azmcp-postgres-server-config", serverName=server_name)

@tool
def query_azure_postgres_database(server_name: str, database_name: str, query: str) -> dict:
    """
    Execute a SQL query against an Azure PostgreSQL database.
    
    This tool runs a SQL query against the specified PostgreSQL database and returns the results.
    
    Args:
        server_name: The name of the Azure PostgreSQL server.
        database_name: The name of the database.
        query: The SQL query to execute.
               Example: "SELECT * FROM users WHERE active = true"
    
    Returns:
        A dictionary containing the query results.
    """
    return _call_azure_tool("azmcp-postgres-database-query", 
                           serverName=server_name, 
                           databaseName=database_name, 
                           query=query)

@tool
def list_azure_postgres_databases(server_name: str) -> dict:
    """
    List databases in an Azure PostgreSQL server.
    
    This tool retrieves all databases within the specified PostgreSQL server.
    
    Args:
        server_name: The name of the Azure PostgreSQL server.
    
    Returns:
        A dictionary containing the list of databases in the PostgreSQL server.
    """
    return _call_azure_tool("azmcp-postgres-database-list", serverName=server_name)
