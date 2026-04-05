from __future__ import annotations
import asyncio
import importlib
import logging
from typing import TYPE_CHECKING

from alarm.state import AlarmState, ArmState, PartitionState, ZoneState
from alarm.events import AlarmEvent
from alarm.ws_manager import WSManager

if TYPE_CHECKING:
    from plugins.AlarmInterface import AlarmInterface

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 0.05  # seconds


class AlarmManager:
    def __init__(self, state: AlarmState, ws_manager: WSManager) -> None:
        self._state = state
        self._ws = ws_manager
        self._plugins: dict[str, AlarmInterface] = {}
        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        """Schedule the outbox-poll loop. Must be called after the event loop is running."""
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("AlarmManager poll loop started.")

    def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("AlarmManager poll loop stopped.")

    # ------------------------------------------------------------------ #
    #  Plugin management                                                   #
    # ------------------------------------------------------------------ #

    def load_plugin(self, module_path: str) -> str:
        """
        Dynamically load a plugin from *module_path* (e.g. "plugins.DSC").

        The target module must expose a PLUGIN_CLASS attribute pointing to an
        AlarmInterface subclass. Returns the plugin name from its manifest.
        """
        mod = importlib.import_module(module_path)
        plugin: AlarmInterface = mod.PLUGIN_CLASS()
        manifest = plugin.on_load()
        plugin.manifest = manifest
        name = manifest.name
        self._plugins[name] = plugin
        self._state.active_plugin = name
        logger.info("Plugin loaded: %s v%s", manifest.name, manifest.version)
        return name

    def unload_plugin(self, name: str) -> None:
        plugin = self._plugins.pop(name, None)
        if plugin:
            plugin.on_unload()
            if self._state.active_plugin == name:
                self._state.active_plugin = None
            logger.info("Plugin unloaded: %s", name)

    def send_to_plugin(self, plugin_name: str, message: dict) -> None:
        """Route a command from the host (HTTP/WS request) into a loaded plugin."""
        plugin = self._plugins.get(plugin_name)
        if plugin is None:
            raise KeyError(f"No plugin named '{plugin_name}' is loaded.")
        plugin.receive(message)

    @property
    def loaded_plugins(self) -> list[str]:
        return list(self._plugins.keys())

    # ------------------------------------------------------------------ #
    #  Internal message handling                                           #
    # ------------------------------------------------------------------ #

    async def _poll_loop(self) -> None:
        while True:
            try:
                for name, plugin in list(self._plugins.items()):
                    messages = plugin.drain_outbox()
                    for msg in messages:
                        await self._handle_plugin_message(name, msg)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in AlarmManager poll loop")
            await asyncio.sleep(_POLL_INTERVAL)

    async def _handle_plugin_message(self, source: str, msg: dict) -> None:
        event_type = msg.get("type")
        mutated = True

        if event_type == AlarmEvent.ZONE_OPEN:
            zone_id = msg.get("zone_id")
            if zone_id is not None:
                zone = self._state.zones.setdefault(
                    zone_id,
                    ZoneState(id=zone_id, label=msg.get("label", f"Zone {zone_id}"))
                )
                zone.open = True

        elif event_type == AlarmEvent.ZONE_CLOSED:
            zone_id = msg.get("zone_id")
            if zone_id is not None and zone_id in self._state.zones:
                self._state.zones[zone_id].open = False

        elif event_type == AlarmEvent.ZONE_BYPASSED:
            zone_id = msg.get("zone_id")
            if zone_id is not None and zone_id in self._state.zones:
                self._state.zones[zone_id].bypassed = msg.get("bypassed", True)

        elif event_type in (AlarmEvent.ARMED_STAY, AlarmEvent.ARMED_AWAY, AlarmEvent.DISARMED,
                            AlarmEvent.ALARM_TRIGGERED, AlarmEvent.ALARM_RESTORED):
            partition_id = msg.get("partition_id")
            if partition_id is None:
                logger.warning("Event '%s' from '%s' missing 'partition_id'", event_type, source)
                mutated = False
            else:
                partition = self._state.partitions.setdefault(
                    partition_id,
                    PartitionState(id=partition_id, label=msg.get("label", f"Partition {partition_id}"))
                )
                arm_map = {
                    AlarmEvent.ARMED_STAY:      ArmState.ARMED_STAY,
                    AlarmEvent.ARMED_AWAY:      ArmState.ARMED_AWAY,
                    AlarmEvent.DISARMED:        ArmState.DISARMED,
                    AlarmEvent.ALARM_TRIGGERED: ArmState.TRIGGERED,
                    AlarmEvent.ALARM_RESTORED:  ArmState.DISARMED,
                }
                partition.arm_state = arm_map[event_type]

        elif event_type == AlarmEvent.READY:
            logger.info("Plugin '%s' reported ready.", source)
            mutated = False

        elif event_type == AlarmEvent.ERROR:
            logger.error("Plugin '%s' error: %s", source, msg.get("detail"))
            mutated = False

        elif event_type == AlarmEvent.ALARM_PANICKED:
            partition_id = msg.get("partition_id")
            panicked = msg.get("panicked", False)
            panic_type = msg.get("panic_type", "unknown")
            if partition_id is None:
                logger.warning("Event '%s' from '%s' missing 'partition_id'", event_type, source)
                mutated = False
            else:
                logger.warning("Partition %d panicked: %s (type: %s)", partition_id, "PANICKED" if panicked else "RESTORED", panic_type)

        else:
            logger.warning("Unhandled event type '%s' from plugin '%s'", event_type, source)
            mutated = False

        if mutated:
            self._state.last_event = event_type
            await self._ws.broadcast(self._state.model_dump_json())
