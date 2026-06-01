import logging
from plugins.AlarmInterface import AlarmInterface
from schema.AlarmPluginManifest import AlarmPluginManifest

logger = logging.getLogger(__name__)


class DSCPC1616(AlarmInterface):

    def on_load(self) -> AlarmPluginManifest:
        return AlarmPluginManifest(
            name="DSC PC1616",
            version="1.0.0",
            author="Santiago Gutierrez",
            description="Stub plugin for the DSC PC1616 alarm panel.",
            connectionType="serial",
            connectionSetupSteps=[
                {
                    "step": "Connect the PC1616 to your server via a serial-to-USB adapter.",
                    "details": "Note the assigned serial port (e.g. /dev/ttyUSB0).",
                },
                {
                    "step": "Enter your installer code.",
                    "input": {"type": "integer", "placeholder": "Installer code"},
                },
            ],
            capabilities={},
            dependencies=[],
        )

    def on_unload(self) -> None:
        logger.info("DSC PC1616 stub unloaded.")

    def receive(self, message: dict) -> None:
        logger.debug("DSC PC1616 stub received: %r", message)


PLUGIN_CLASS = DSCPC1616
