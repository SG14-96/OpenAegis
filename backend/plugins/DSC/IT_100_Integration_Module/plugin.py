from plugins.AlarmInterface import AlarmInterface


class DSCIntegrationModule(AlarmInterface):
    """Empty placeholder — the py-dsc-it100 integration is being reworked
    on a separate branch. Loads and satisfies the plugin contract but does
    not talk to any hardware."""

    def receive(self, message: dict) -> None:
        pass


PLUGIN_CLASS = DSCIntegrationModule
