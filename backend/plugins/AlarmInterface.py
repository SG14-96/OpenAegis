from abc import ABC, abstractmethod
from typing import Callable, Optional

from schema.PluginManifest import PluginManifest


class AlarmInterface(ABC):
    """
    Every plugin module must subclass this and implement the abstract methods.

    Communication model
    -------------------
    Host → Plugin : host calls `receive(message)` on the plugin instance.
    Plugin → Host : plugin calls `self.send(message)`; the host registers a
                    handler via `set_message_handler` which is invoked immediately
                    on each outgoing message — no polling, no queue.

    A message is any JSON-serializable dict with a required "type" key.
    """

    def __init__(self) -> None:
        self._message_handler: Optional[Callable[[dict], None]] = None
        self._running: bool = False
        self.manifest: Optional[PluginManifest] = None

    # ------------------------------------------------------------------ #
    #  Lifecycle hooks (optional to override)                              #
    # ------------------------------------------------------------------ #

    def on_load(self, setup_values: dict | None = None) -> None:
        """Called once after the plugin is instantiated.

        setup_values contains the user's wizard configuration keyed by step index.
        Use it to configure the connection (port, baud rate, credentials, etc.).
        The manifest is already set on self.manifest before this is called.
        """

    def on_unload(self) -> None:
        """Called just before the module is removed from the loader."""

    # ------------------------------------------------------------------ #
    #  Communication API                                                   #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def receive(self, message: dict) -> None:
        """
        Host → Plugin.
        The host calls this to push a command into the plugin.
        Must not block; do heavy work in a background thread if needed.
        """

    def send(self, message: dict) -> None:
        """
        Plugin → Host.
        The plugin calls this to deliver a message to the host immediately.
        Thread-safe: can be called from background threads.
        """
        if "type" not in message:
            raise ValueError("Every outgoing message must include a 'type' key.")
        if self._message_handler is not None:
            self._message_handler(message)

    def set_message_handler(self, handler: Callable[[dict], None]) -> None:
        """Registered by the host after loading; routes send() calls to the manager."""
        self._message_handler = handler
