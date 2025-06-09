from ..utils import _call_azure_tool
from strands.tools import tool

@tool
def get_azure_servicebus_topic_subscription_details(namespace_name: str, topic_name: str, subscription_name: str) -> dict:
    """
    Get details for an Azure Service Bus topic subscription.
    
    This tool retrieves detailed information about a specific Service Bus topic subscription.
    
    Args:
        namespace_name: The name of the Service Bus namespace.
        topic_name: The name of the topic.
        subscription_name: The name of the subscription.
    
    Returns:
        A dictionary containing the subscription details and runtime information.
    """
    return _call_azure_tool("azmcp-servicebus-topic-subscription-details", 
                           namespaceName=namespace_name, 
                           topicName=topic_name, 
                           subscriptionName=subscription_name)

@tool
def get_azure_servicebus_topic_details(namespace_name: str, topic_name: str) -> dict:
    """
    Get details for an Azure Service Bus topic.
    
    This tool retrieves detailed information about a specific Service Bus topic.
    
    Args:
        namespace_name: The name of the Service Bus namespace.
        topic_name: The name of the topic.
    
    Returns:
        A dictionary containing the topic details and runtime information.
    """
    return _call_azure_tool("azmcp-servicebus-topic-details", 
                           namespaceName=namespace_name, 
                           topicName=topic_name)

@tool
def get_azure_servicebus_queue_details(namespace_name: str, queue_name: str) -> dict:
    """
    Get details for an Azure Service Bus queue.
    
    This tool retrieves detailed information about a specific Service Bus queue.
    
    Args:
        namespace_name: The name of the Service Bus namespace.
        queue_name: The name of the queue.
    
    Returns:
        A dictionary containing the queue details and runtime information.
    """
    return _call_azure_tool("azmcp-servicebus-queue-details", 
                           namespaceName=namespace_name, 
                           queueName=queue_name)