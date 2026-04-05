"""
AlarmInterface.py
-----------------
Defines the AlarmInterface class, which serves as an abstract base class for alarm plugins.
This interface specifies the methods that any alarm plugin must implement to be compatible with the system.
The AlarmInterface ensures that all alarm plugins provide a consistent way to trigger alarms and handle alarm-related functionality.
"""

import queue
from abc import ABC, abstractmethod
from schema.AlarmPluginManifest import AlarmPluginManifest

class AlarmInterface(ABC):
    """
    Every plugin module must subclass this and implement the abstract methods.

    Communication model
    -------------------
    Host → Module : host calls `receive(message)` on the module instance.
    Module → Host : module calls `self.send(message)` internally; the host
                    drains `module.outbox` whenever it likes.

    A message is any JSON-serialisable dict, but the only required key is
    "type" (a string), which lets the host route messages without inspecting
    the full payload.

    """

    def __init__(self) -> None:
        # Module → Host outbox; the host reads from this queue.
        self.outbox: queue.Queue[dict] = queue.Queue()
        self._running: bool = False
        self.manifest: AlarmPluginManifest = None

    # ------------------------------------------------------------------ #
    #  Lifecycle hooks (optional to override)                              #
    # ------------------------------------------------------------------ #

    def on_load(self) -> AlarmPluginManifest:
        """Called once right after the module is instantiated by the loader."""

    def on_unload(self) -> None:
        """Called just before the module is removed from the loader."""

    # ------------------------------------------------------------------ #
    #  Communication API                                                   #
    # ------------------------------------------------------------------ #

    @abstractmethod
    def receive(self, message: dict) -> None:
        """
        Host → Module.
        The host calls this to push a message into the module.
        Must not block; do heavy work in a background thread if needed.
        """

    def send(self, message: dict) -> None:
        """
        Module → Host.
        The module calls this internally to post a message to the host.
        Thread-safe: can be called from background threads.
        """
        if "type" not in message:
            raise ValueError("Every outgoing message must include a 'type' key.")
        self.outbox.put(message)

    def drain_outbox(self) -> list[dict]:
        """
        Convenience helper: returns all pending outgoing messages as a list.
        The host can call this instead of reading the queue directly.
        """
        messages = []
        while not self.outbox.empty():
            try:
                messages.append(self.outbox.get_nowait())
            except queue.Empty:
                break
        return messages