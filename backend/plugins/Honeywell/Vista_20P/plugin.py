import logging
from plugins.AlarmInterface import AlarmInterface
from schema.AlarmPluginManifest import AlarmPluginManifest

logger = logging.getLogger(__name__)


class HoneywellVista20P(AlarmInterface):

    def on_load(self) -> AlarmPluginManifest:
        return AlarmPluginManifest(
            name="Honeywell Vista 20P",
            version="1.0.0",
            author="Santiago Gutierrez",
            description="Stub plugin for the Honeywell Vista 20P alarm panel.",
            connectionType="serial",
            connectionSetupSteps=[
                {
                    "step": "Connect a Honeywell serial interface module to your server.",
                    "details": "Note the assigned serial port.",
                },
                {
                    "step": "Enter your 4-digit installer code.",
                    "input": {"type": "integer", "placeholder": "Installer code (default 4112)"},
                },
                {
                    "step": "Set the number of zones in your installation.",
                    "input": {"type": "integer", "placeholder": "Zone count (1–48)"},
                },
            ],
            capabilities={},
            dependencies=[],
        )

    def on_unload(self) -> None:
        logger.info("Honeywell Vista 20P stub unloaded.")

    def receive(self, message: dict) -> None:
        logger.debug("Honeywell Vista 20P stub received: %r", message)


PLUGIN_CLASS = HoneywellVista20P
