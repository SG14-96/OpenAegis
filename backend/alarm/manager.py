from __future__ import annotations
import asyncio
import importlib
import importlib.metadata
import json
import logging
import subprocess
import sys
from typing import TYPE_CHECKING, Callable
from schema.settings import AlarmPartition, AlarmZone
from schema.state import AlarmStateSnapshot

from alarm.commands import CommandPayload
from alarm.events import AlarmEvent
from alarm.ws_manager import WSManager
from plugins.exceptions import IllegalCommandError

if TYPE_CHECKING:
    from plugins.AlarmInterface import AlarmInterface
    from sqlalchemy.orm import Session

# Plugin events that are persisted as history, and the table each goes to.
_ARMING_EVENT_TYPES = {AlarmEvent.ARMED_STAY, AlarmEvent.ARMED_AWAY, AlarmEvent.DISARMED}
_ALARM_STATE_EVENT_TYPES = {AlarmEvent.ALARM_TRIGGERED, AlarmEvent.ALARM_RESTORED, AlarmEvent.ALARM_PANICKED}

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin's on_load raises — includes the plugin name and root cause."""
    def __init__(self, plugin_name: str, cause: Exception) -> None:
        self.plugin_name = plugin_name
        self.cause = cause
        super().__init__(f"Plugin '{plugin_name}' failed to load: {cause}")


class AlarmManager:
    def __init__(self, ws_manager: WSManager, session_factory: Callable[[], Session] | None = None) -> None:
        self._ws = ws_manager # WebSocket manager for sending events to clients
        self._session_factory = session_factory # Opens DB sessions for event history; None disables persistence
        self._plugin: AlarmInterface | None = None # Currently loaded plugin instance
        self._plugin_name: str | None = None # Name of the currently loaded plugin (from its manifest)
        self._module_path: str | None = None # Python module path of the currently loaded plugin

        self.partitions: list[AlarmPartition] = [] # List of alarm partitions, each containing zones and their states

        # Last known full state snapshot, as pushed by the active plugin via an
        # AlarmEvent.STATE_SNAPSHOT message. Served to clients on connect via
        # GET /api/v1/alarm/state so they don't have to wait for the next event,
        # and handed back to the plugin's own is_legal() as its "current state".
        self._state_snapshot: AlarmStateSnapshot = AlarmStateSnapshot()
        self._troubles: set[str] = set()

        # Why the most recent plugin load failed (e.g. the serial device was
        # missing at boot). Cleared by the next successful load or an unload.
        self.last_load_error: str | None = None

    # ------------------------------------------------------------------ #
    #  Plugin lifecycle                                                  #
    # ------------------------------------------------------------------ #

    def load_plugin(self, module_path: str, setup_values: dict | None = None) -> str:
        if self._plugin is not None:
            raise RuntimeError(
                f"Plugin '{self._plugin_name}' is already loaded. "
                "Unload it before loading another."
            )
        try:
            name = self._load_plugin(module_path, setup_values)
        except Exception as exc:
            self.last_load_error = str(exc)
            raise
        self.last_load_error = None
        return name

    def _load_plugin(self, module_path: str, setup_values: dict | None) -> str:
        from pathlib import Path
        from schema.PluginManifest import PluginManifest

        mod = importlib.import_module(module_path)

        manifest_path = Path(mod.__file__).parent / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"No manifest.json found for plugin '{module_path}'")
        manifest = PluginManifest.from_file(manifest_path)

        if manifest.dependencies:
            self._install_deps(manifest.dependencies)

        plugin_cls = getattr(mod, "PLUGIN_CLASS", None)
        if plugin_cls is None:
            plugin_mod = importlib.import_module(f"{module_path}.plugin")
            plugin_cls = getattr(plugin_mod, "PLUGIN_CLASS", None)
        if plugin_cls is None:
            raise AttributeError(
                f"Plugin '{module_path}' does not expose PLUGIN_CLASS."
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
        self._plugin = plugin
        self._plugin_name = manifest.name
        self._module_path = module_path

        logger.info("Plugin loaded: %s v%s", manifest.name, manifest.version)
        return manifest.name

    def reload_plugin(
        self,
        new_module_path: str,
        new_setup_values: dict | None,
        old_module_path: str | None,
        old_setup_values: dict | None,
    ) -> str:
        """Unload the active plugin and load a replacement. Rolls back to the old plugin on failure."""
        if self._plugin is not None:
            self.unload_plugin()
        try:
            return self.load_plugin(new_module_path, new_setup_values)
        except Exception:
            if old_module_path:
                try:
                    self.load_plugin(old_module_path, old_setup_values)
                except Exception:
                    logger.exception(
                        "Failed to restore plugin '%s' during reload rollback", old_module_path
                    )
            raise

    def unload_plugin(self) -> None:
        if self._plugin is None:
            raise RuntimeError("No plugin is currently loaded.")

        name = self._plugin_name
        self._plugin.set_message_handler(None)
        try:
            self._plugin.on_unload()
        except Exception:
            logger.exception("Plugin '%s' on_unload raised", name)

        self._plugin = None
        self._plugin_name = None
        self._module_path = None
        self._state_snapshot = AlarmStateSnapshot()
        self._troubles.clear()
        self.last_load_error = None
        logger.info("Plugin unloaded: %s", name)

    # ------------------------------------------------------------------ #
    #  Database persistence                                                #
    # ------------------------------------------------------------------ #

    async def restore_from_config(self, db: Session) -> None:
        logger.info("Restoring alarm plugin from config...")
        from crud.settings import get_active_plugin_settings

        plugin_settings = get_active_plugin_settings(db)
        if plugin_settings is None:
            logger.info("No saved alarm configuration found. Starting fresh.")
            return

        module_path = plugin_settings.data.get("module_path")
        setup_values = plugin_settings.data.get("setup_values")

        if not module_path:
            logger.warning("Active PluginSettings row found but 'module_path' is missing. Skipping.")
            return

        logger.info("Restoring plugin '%s' from database...", plugin_settings.plugin_name)
        try:
            self.load_plugin(module_path, setup_values)
        except Exception as exc:
            logger.error("Startup restore of plugin '%s' failed: %s", plugin_settings.plugin_name, exc)

    def reload_saved_plugin(self, db: Session) -> str:
        """
        (Re)load the plugin from the saved alarm configuration — e.g. after
        plugging the panel back in when the startup restore failed. Raises
        LookupError if nothing is saved; load errors propagate as from
        load_plugin (and are kept in last_load_error).
        """
        from crud.settings import get_active_plugin_settings

        plugin_settings = get_active_plugin_settings(db)
        module_path = plugin_settings.data.get("module_path") if plugin_settings else None
        if not module_path:
            raise LookupError("No saved alarm configuration to reload.")

        if self._plugin is not None:
            self.unload_plugin()
        return self.load_plugin(module_path, plugin_settings.data.get("setup_values"))

    # ------------------------------------------------------------------ #
    #  Command dispatch                                                    #
    # ------------------------------------------------------------------ #

    def dispatch_command(self, payload: CommandPayload) -> None:
        if self._plugin is None:
            raise RuntimeError("No plugin is loaded.")

        legal, reason = self._plugin.is_legal(payload, self._state_snapshot)
        if not legal:
            raise IllegalCommandError(payload.command, reason)

        self._plugin.receive(self._build_plugin_message(payload))

    @staticmethod
    def _build_plugin_message(payload: CommandPayload) -> dict:
        from alarm.commands import AlarmCommand

        msg: dict = {"type": payload.command.value}
        msg["partition"] = payload.partition_id
        if payload.zone_id is not None:
            msg["zone_id"] = payload.zone_id
        if payload.user_code is not None:
            msg["user_code"] = payload.user_code
        if payload.panic_type is not None:
            msg["panic_type"] = payload.panic_type
        if payload.command is AlarmCommand.BYPASS_ZONE:
            msg["bypassed"] = payload.bypassed
        return msg

    # ------------------------------------------------------------------ #
    #  Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def active_plugin(self) -> str | None:
        return self._plugin_name

    @property
    def list_available_plugins(self) -> list[dict]:
        from plugins.discovery import discover_plugins
        return discover_plugins()

    @property
    def state_snapshot(self) -> AlarmStateSnapshot:
        """Latest partitions/zones snapshot reported by the active plugin, plus active troubles."""
        return self._state_snapshot.model_copy(update={"troubles": sorted(self._troubles)})

    # ------------------------------------------------------------------ #
    #  Internal event handling                                             #
    # ------------------------------------------------------------------ #

    def _make_handler(self, plugin_name: str) -> Callable[[dict], None]:
        loop = asyncio.get_running_loop()

        def handler(msg: dict) -> None:
            asyncio.run_coroutine_threadsafe(
                self._on_plugin_event(plugin_name, msg), loop
            )

        return handler

    async def _on_plugin_event(self, source: str, msg: dict) -> None:
        logger.info("Event from '%s': %s", source, msg)
        if msg.get("type") == AlarmEvent.STATE_SNAPSHOT:
            self._state_snapshot = AlarmStateSnapshot.model_validate({
                "partitions": msg.get("partitions", {}),
                "zones": msg.get("zones", {}),
            })
        elif msg.get("type") == AlarmEvent.TROUBLE:
            if msg.get("restored"):
                self._troubles.discard(msg.get("trouble_type"))
            else:
                self._troubles.add(msg.get("trouble_type"))
        elif msg.get("type") in _ARMING_EVENT_TYPES | _ALARM_STATE_EVENT_TYPES:
            try:
                await asyncio.to_thread(self._record_event, msg)
            except Exception:
                # History is best-effort — never drop the live broadcast over it.
                logger.exception("Failed to record alarm event %s", msg)
        await self._ws.broadcast(json.dumps(msg))

    def _record_event(self, msg: dict) -> None:
        if self._session_factory is None:
            return
        from models.events import AlarmStateEvent, ArmingEvent

        event_type = msg["type"]
        partition_id = msg.get("partition_id", 1)
        if event_type in _ARMING_EVENT_TYPES:
            row = ArmingEvent(
                partition_id=partition_id,
                event_type=event_type,
                last_user=msg.get("last_user"),
            )
        elif event_type == AlarmEvent.ALARM_PANICKED and not msg.get("panicked", True):
            # A panic restore isn't a new alarm; nothing worth a history row.
            return
        else:
            row = AlarmStateEvent(
                partition_id=partition_id,
                event_type=event_type,
                trigger_type=msg.get("panic_type") if event_type == AlarmEvent.ALARM_PANICKED else None,
            )

        db = self._session_factory()
        try:
            db.add(row)
            db.commit()
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _install_deps(self, deps: list[str]) -> None:
        import re
        installed = {d.metadata["Name"].lower() for d in importlib.metadata.distributions()}
        to_install = [
            dep for dep in deps
            if re.split(r"[><=!~\[;]", dep)[0].strip().lower() not in installed
        ]
        if not to_install:
            return
        logger.info("Installing plugin dependencies: %s", to_install)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", *to_install])
        importlib.invalidate_caches()
