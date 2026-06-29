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

from alarm.ws_manager import WSManager

if TYPE_CHECKING:
    from plugins.AlarmInterface import AlarmInterface
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Raised when a plugin's on_load raises — includes the plugin name and root cause."""
    def __init__(self, plugin_name: str, cause: Exception) -> None:
        self.plugin_name = plugin_name
        self.cause = cause
        super().__init__(f"Plugin '{plugin_name}' failed to load: {cause}")


class AlarmManager:
    def __init__(self, ws_manager: WSManager) -> None:
        self._ws = ws_manager # WebSocket manager for sending events to clients
        self._plugin: AlarmInterface | None = None # Currently loaded plugin instance
        self._plugin_name: str | None = None # Name of the currently loaded plugin (from its manifest)
        self._module_path: str | None = None # Python module path of the currently loaded plugin

        self.partitions: list[AlarmPartition] = [] # List of alarm partitions, each containing zones and their states

    # ------------------------------------------------------------------ #
    #  Plugin lifecycle                                                  #
    # ------------------------------------------------------------------ #

    def load_plugin(self, module_path: str, setup_values: dict | None = None) -> str:
        if self._plugin is not None:
            raise RuntimeError(
                f"Plugin '{self._plugin_name}' is already loaded. "
                "Unload it before loading another."
            )

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

    # ------------------------------------------------------------------ #
    #  Command dispatch                                                    #
    # ------------------------------------------------------------------ #

    def dispatch_command(self, payload: object) -> None:
        if self._plugin is None:
            raise RuntimeError("No plugin is loaded.")
        self._plugin.receive(self._build_plugin_message(payload))

    @staticmethod
    def _build_plugin_message(payload: object) -> dict:
        from alarm.commands import AlarmCommand

        msg: dict = {"type": payload.command.value}  # type: ignore[attr-defined]
        msg["partition"] = payload.partition_id       # type: ignore[attr-defined]
        if payload.zone_id is not None:               # type: ignore[attr-defined]
            msg["zone_id"] = payload.zone_id          # type: ignore[attr-defined]
        if payload.user_code is not None:             # type: ignore[attr-defined]
            msg["user_code"] = payload.user_code      # type: ignore[attr-defined]
        if payload.panic_type is not None:            # type: ignore[attr-defined]
            msg["panic_type"] = payload.panic_type    # type: ignore[attr-defined]
        if payload.command is AlarmCommand.BYPASS_ZONE:  # type: ignore[attr-defined]
            msg["bypassed"] = payload.bypassed        # type: ignore[attr-defined]
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
        await self._ws.broadcast(json.dumps(msg))

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
