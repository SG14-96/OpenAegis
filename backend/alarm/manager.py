from __future__ import annotations
import asyncio
import importlib
import importlib.metadata
import logging
import subprocess
import sys
from typing import TYPE_CHECKING, Callable

from alarm.state import AlarmState, ArmState, PartitionState, ZoneState
from alarm.events import AlarmEvent
from alarm.ws_manager import WSManager

if TYPE_CHECKING:
    from plugins.AlarmInterface import AlarmInterface

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin's on_load raises — includes the plugin name and root cause."""
    def __init__(self, plugin_name: str, cause: Exception) -> None:
        self.plugin_name = plugin_name
        self.cause = cause
        super().__init__(f"Plugin '{plugin_name}' failed to load: {cause}")


class AlarmManager:
    def __init__(self, state: AlarmState, ws_manager: WSManager) -> None:
        self._state = state
        self._ws = ws_manager
        self._plugins: dict[str, AlarmInterface] = {}

    # ------------------------------------------------------------------ #
    #  Plugin management                                                   #
    # ------------------------------------------------------------------ #

    def load_plugin(self, module_path: str, setup_values: dict | None = None) -> str:
        """
        Dynamically load a plugin from *module_path*
        (e.g. "plugins.DSC.IT_100_Integration_Module").

        The target module must expose a PLUGIN_CLASS attribute pointing to an
        AlarmInterface subclass. Returns the plugin name from its manifest.

        Any packages listed in the manifest's `dependencies` field that are not
        already installed will be pip-installed before the plugin is instantiated.
        """
        from pathlib import Path
        from schema.PluginManifest import PluginManifest

        mod = importlib.import_module(module_path)

        manifest_path = Path(mod.__file__).parent / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"No manifest.json found for plugin '{module_path}'")
        manifest = PluginManifest.from_file(manifest_path)

        if manifest.dependencies:
            self._install_deps(manifest.dependencies)

        plugin_cls = getattr(mod, 'PLUGIN_CLASS', None)
        if plugin_cls is None:
            plugin_mod = importlib.import_module(f"{module_path}.plugin")
            plugin_cls = getattr(plugin_mod, 'PLUGIN_CLASS', None)
        if plugin_cls is None:
            raise AttributeError(
                f"Plugin '{module_path}' does not expose PLUGIN_CLASS in its "
                "__init__.py or plugin.py."
            )
        plugin: AlarmInterface = plugin_cls()
        plugin.manifest = manifest
        try:
            plugin.on_load(setup_values)
        except Exception as exc:
            logger.error("Plugin '%s' on_load failed: %s", manifest.name, exc)
            try:
                plugin.on_unload()
            except Exception:
                logger.exception("Plugin '%s' on_unload raised during cleanup", manifest.name)
            raise PluginLoadError(manifest.name, exc) from exc

        plugin.set_message_handler(self._make_handler(manifest.name))
        self._plugins[manifest.name] = plugin
        self._state.active_plugin = manifest.name

        logger.info("Plugin loaded: %s v%s", manifest.name, manifest.version)
        return manifest.name

    def _make_handler(self, plugin_name: str) -> Callable[[dict], None]:
        """
        Returns a thread-safe callback that schedules _handle_plugin_message
        on the running event loop. Safe to call from background threads.
        """
        loop = asyncio.get_event_loop()

        def handler(msg: dict) -> None:
            asyncio.run_coroutine_threadsafe(
                self._handle_plugin_message(plugin_name, msg), loop
            )

        return handler

    def _install_deps(self, deps: list[str]) -> None:
        """Install any pip packages from *deps* that are not already present."""
        import re
        installed = {
            d.metadata["Name"].lower()
            for d in importlib.metadata.distributions()
        }
        # Extract the bare package name from specifiers like "pyserial>=3.5"
        to_install = [
            dep for dep in deps
            if re.split(r"[><=!~\[;]", dep)[0].strip().lower() not in installed
        ]
        if not to_install:
            return
        logger.info("Installing plugin dependencies: %s", to_install)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", *to_install]
        )
        # Invalidate the metadata cache so newly installed packages are visible
        importlib.invalidate_caches()

    def unload_plugin(self, name: str) -> None:
        plugin = self._plugins.pop(name, None)
        if plugin:
            plugin.set_message_handler(None)
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

    @property
    def list_available_plugins(self) -> list[dict]:
        from plugins.discovery import discover_plugins
        return discover_plugins()

    @property
    def active_plugin(self) -> str | None:
        return self._state.active_plugin

    # ------------------------------------------------------------------ #
    #  Internal message handling                                           #
    # ------------------------------------------------------------------ #

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
