from use_azure.utils import _call_azure_tool
from strands.tools import tool

@tool
def list_azure_app_config_stores(resource_group: str = None) -> dict:
    """
    List Azure App Configuration stores in the subscription or a specific resource group.
    
    This tool retrieves information about all App Configuration stores accessible with your credentials.
    
    Args:
        resource_group: Optional. The name of the resource group to filter stores.
                       If not provided, lists stores from all resource groups.
    
    Returns:
        A dictionary containing the list of App Configuration stores.
    """
    args = {}
    if resource_group:
        args["resourceGroup"] = resource_group
    
    return _call_azure_tool("azmcp-appconfig-account-list", **args)

@tool
def get_azure_app_config_values(store_name: str, key_filter: str = None) -> dict:
    """
    Get key-value pairs from an Azure App Configuration store.
    
    This tool retrieves configuration values from the specified App Configuration store.
    
    Args:
        store_name: The name of the App Configuration store.
        key_filter: Optional. Filter for specific keys. Example: "MyApp:*"
    
    Returns:
        A dictionary containing the configuration key-value pairs.
    """
    args = {"storeName": store_name}
    if key_filter:
        args["keyFilter"] = key_filter
    
    return _call_azure_tool("azmcp-appconfig-kv-list", **args)

@tool
def show_azure_app_config_value(store_name: str, key: str, label: str = None) -> dict:
    """
    Show a specific key-value pair from an Azure App Configuration store.
    
    This tool retrieves a specific configuration value from the App Configuration store.
    
    Args:
        store_name: The name of the App Configuration store.
        key: The configuration key to show.
        label: Optional. The label for the configuration key.
    
    Returns:
        A dictionary containing the configuration value details.
    """
    args = {"storeName": store_name, "key": key}
    if label:
        args["label"] = label
    
    return _call_azure_tool("azmcp-appconfig-kv-show", **args)

@tool
def set_azure_app_config_value(store_name: str, key: str, value: str, label: str = None) -> dict:
    """
    Set a key-value pair in an Azure App Configuration store.
    
    This tool sets or updates a configuration value in the specified App Configuration store.
    
    Args:
        store_name: The name of the App Configuration store.
        key: The configuration key to set.
        value: The value to set for the configuration key.
        label: Optional. The label for the configuration key.
    
    Returns:
        A dictionary containing the set result.
    """
    args = {"storeName": store_name, "key": key, "value": value}
    if label:
        args["label"] = label
    
    return _call_azure_tool("azmcp-appconfig-kv-set", **args)

@tool
def lock_azure_app_config_value(store_name: str, key: str, label: str = None) -> dict:
    """
    Lock a key-value pair in an Azure App Configuration store.
    
    This tool locks a configuration value to prevent modification.
    
    Args:
        store_name: The name of the App Configuration store.
        key: The configuration key to lock.
        label: Optional. The label for the configuration key.
    
    Returns:
        A dictionary containing the lock result.
    """
    args = {"storeName": store_name, "key": key}
    if label:
        args["label"] = label
    
    return _call_azure_tool("azmcp-appconfig-kv-lock", **args)

@tool
def delete_azure_app_config_value(store_name: str, key: str, label: str = None) -> dict:
    """
    Delete a key-value pair from an Azure App Configuration store.
    
    This tool deletes a configuration value from the specified App Configuration store.
    
    Args:
        store_name: The name of the App Configuration store.
        key: The configuration key to delete.
        label: Optional. The label for the configuration key.
    
    Returns:
        A dictionary containing the deletion result.
    """
    args = {"storeName": store_name, "key": key}
    if label:
        args["label"] = label
    
    return _call_azure_tool("azmcp-appconfig-kv-delete", **args)

@tool
def unlock_azure_app_config_value(store_name: str, key: str, label: str = None) -> dict:
    """
    Unlock a key-value pair in an Azure App Configuration store.
    
    This tool unlocks a configuration value to allow modification.
    
    Args:
        store_name: The name of the App Configuration store.
        key: The configuration key to unlock.
        label: Optional. The label for the configuration key.
    
    Returns:
        A dictionary containing the unlock result.
    """
    args = {"storeName": store_name, "key": key}
    if label:
        args["label"] = label
    
    return _call_azure_tool("azmcp-appconfig-kv-unlock", **args)

