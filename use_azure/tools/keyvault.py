from use_azure.utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_key_vaults(resource_group: str = None) -> dict:
    """
    List Azure Key Vaults in the subscription or a specific resource group.
    
    This tool retrieves information about all Key Vaults accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter Key Vaults.
                       If not provided, lists Key Vaults from all resource groups.
    
    Returns:
        A dictionary containing the list of Key Vaults.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-keyvault-key-list", **args)

@tool
def create_azure_key_vault_key(vault_name: str, key_name: str, key_type: str = "RSA", key_size: int = 2048) -> dict:
    """
    Create a new key in an Azure Key Vault.
    
    This tool creates a new cryptographic key in the specified Key Vault.
    
    Args:
        vault_name: The name of the Key Vault.
        key_name: The name of the key to create.
        key_type: Optional. The type of key to create (RSA, EC). Default is "RSA".
        key_size: Optional. The size of the key in bits. Default is 2048.
    
    Returns:
        A dictionary containing the created key information.
    """
    return _call_azure_tool("azmcp-keyvault-key-create", 
                           vaultName=vault_name, 
                           keyName=key_name,
                           keyType=key_type,
                           keySize=key_size)

@tool
def get_azure_key_vault_key(vault_name: str, key_name: str, key_version: str = None) -> dict:
    """
    Get a key from an Azure Key Vault.
    
    This tool retrieves information about a specific key from the Key Vault.
    
    Args:
        vault_name: The name of the Key Vault.
        key_name: The name of the key to retrieve.
        key_version: Optional. The specific version of the key to retrieve.
                    If not provided, retrieves the latest version.
    
    Returns:
        A dictionary containing the key information and properties.
    """
    args = {"vaultName": vault_name, "keyName": key_name}
    if key_version:
        args["keyVersion"] = key_version
    
    return _call_azure_tool("azmcp-keyvault-key-get", **args)


