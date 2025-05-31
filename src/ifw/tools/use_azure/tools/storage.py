from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_storage_containers(storage_account: str) -> dict:
    """
    List containers in an Azure Storage account.
    
    This tool retrieves all blob containers within the specified storage account.
    
    Args:
        storage_account: The name of the Azure Storage account.
    
    Returns:
        A dictionary containing the list of containers in the storage account.
    """
    return _call_azure_tool("azmcp-storage-blob-container-list", storageAccount=storage_account)

@tool
def list_azure_storage_accounts(resource_group: str = None) -> dict:
    """
    List Azure Storage accounts in the subscription or a specific resource group.
    
    This tool retrieves information about all storage accounts accessible with your credentials,
    including their names, locations, and performance tiers.
    
    Args:
        resource_group: Optional. The name of the resource group to filter storage accounts.
                       If not provided, lists storage accounts from all resource groups.
    
    Returns:
        A dictionary containing the list of storage accounts.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-storage-account-list", **args)

@tool
def list_azure_storage_tables(storage_account: str) -> dict:
    """
    List tables in an Azure Storage account.
    
    This tool retrieves all tables within the specified storage account.
    
    Args:
        storage_account: The name of the Azure Storage account.
    
    Returns:
        A dictionary containing the list of tables in the storage account.
    """
    return _call_azure_tool("azmcp-storage-table-list", storageAccount=storage_account)

@tool
def list_azure_storage_blobs(storage_account: str, container_name: str) -> dict:
    """
    List blobs in an Azure Storage container.
    
    This tool retrieves all blobs within the specified storage container.
    
    Args:
        storage_account: The name of the Azure Storage account.
        container_name: The name of the blob container.
    
    Returns:
        A dictionary containing the list of blobs in the container.
    """
    return _call_azure_tool("azmcp-storage-blob-list", 
                           storageAccount=storage_account, 
                           containerName=container_name)

@tool
def get_azure_storage_container_details(storage_account: str, container_name: str) -> dict:
    """
    Get detailed information about an Azure Storage blob container.
    
    This tool retrieves detailed properties and metadata for a specific blob container.
    
    Args:
        storage_account: The name of the Azure Storage account.
        container_name: The name of the blob container.
    
    Returns:
        A dictionary containing the container details, properties, and metadata.
    """
    return _call_azure_tool("azmcp-storage-blob-container-details", 
                           storageAccount=storage_account, 
                           containerName=container_name)

