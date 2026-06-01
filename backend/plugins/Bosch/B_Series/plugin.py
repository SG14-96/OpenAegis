import logging
from plugins.AlarmInterface import AlarmInterface
from schema.AlarmPluginManifest import AlarmPluginManifest

logger = logging.getLogger(__name__)


class BoschBSeries(AlarmInterface):

    def on_load(self) -> AlarmPluginManifest:
        return AlarmPluginManifest(
            name="Bosch B-Series",
            version="1.0.0",
            author="Santiago Gutierrez",
            description="Stub plugin for Bosch B-Series alarm panels (B3512 / B4512 / B5512).",
            connectionType="http",
            connectionSetupSteps=[
                {
                    "step": "Ensure the Bosch RPS (Remote Programming Software) integration is enabled on your panel.",
                    "details": "Access panel programming and enable the IP interface.",
                },
                {
                    "step": "Enter the panel IP address and port.",
                    "input": {"type": "string", "placeholder": "e.g. 192.168.1.50:7700"},
                },
                {
                    "step": "Enter the automation passcode configured in the panel.",
                    "input": {"type": "string", "placeholder": "Automation passcode"},
                },
            ],
            capabilities={},
            dependencies=[],
        )

    def on_unload(self) -> None:
        logger.info("Bosch B-Series stub unloaded.")

    def receive(self, message: dict) -> None:
        logger.debug("Bosch B-Series stub received: %r", message)


PLUGIN_CLASS = BoschBSeries
