"""
Custom Exceptions for Infraware Cloud Assistant.
Defines application-specific exception classes.
"""

"""
Custom Exceptions for Infraware Cloud Assistant.
Defines application-specific exception classes.
"""


class InfrawareError(Exception):
    """Base exception for Infraware Cloud Assistant."""

    pass


class SessionError(InfrawareError):
    """Session-related errors."""

    pass


class CommandError(InfrawareError):
    """Command processing errors."""

    pass
