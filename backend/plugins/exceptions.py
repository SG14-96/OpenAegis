"""Plugin-related exception classes for OpenAegis backend plugins.

Keep these lightweight and specific so callers can catch fine-grained
errors when loading, validating, or executing plugins.
"""

from typing import Optional


class PluginError(Exception):
    """Base class for all plugin-related errors."""

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = "An unknown plugin error occurred."
        super().__init__(message)


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin cannot be found."""


class PluginLoadError(PluginError):
    """Raised when a plugin cannot be loaded (e.g. import error, syntax error)."""


class PluginConfigError(PluginError):
    """Raised when a plugin's configuration is invalid or missing required fields."""


class PluginDependencyError(PluginError):
    """Raised when a plugin's external dependency is missing or incompatible."""


class PluginVersionMismatchError(PluginError):
    """Raised when a plugin's declared version is incompatible with the host.

    Attributes:
        required: version spec required by the host or plugin
        found: actual version discovered
    """

    def __init__(self, required: Optional[str] = None, found: Optional[str] = None):
        msg = "Plugin version mismatch."
        if required and found:
            msg = f"Plugin version mismatch: required={required}, found={found}"
        elif required:
            msg = f"Plugin version mismatch: required={required}"
        elif found:
            msg = f"Plugin version mismatch: found={found}"
        super().__init__(msg)
        self.required = required
        self.found = found


class PluginExecutionError(PluginError):
    """Raised when a plugin raises an error during execution.

    The original exception can be attached as the `cause` attribute.
    """

    def __init__(self, message: Optional[str] = None, cause: Optional[Exception] = None):
        if message is None and cause is not None:
            message = f"Plugin execution failed: {cause}"
        super().__init__(message)
        self.cause = cause


class IllegalCommandError(PluginError):
    """Raised when the active plugin reports that a command is not legal
    to send given the last-known panel state (see `AlarmInterface.is_legal`).

    Attributes:
        command: the `AlarmCommand` that was rejected
        reason: a human-readable explanation from the plugin, if any
    """

    def __init__(self, command: object, reason: Optional[str] = None):
        self.command = command
        self.reason = reason
        message = f"Command '{command}' is not legal right now."
        if reason:
            message += f" {reason}"
        super().__init__(message)


__all__ = [
    "PluginError",
    "PluginNotFoundError",
    "PluginLoadError",
    "PluginConfigError",
    "PluginDependencyError",
    "PluginVersionMismatchError",
    "PluginExecutionError",
    "IllegalCommandError",
]

