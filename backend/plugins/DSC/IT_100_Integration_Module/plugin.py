import logging
from plugins.AlarmInterface import AlarmInterface
from alarm.events import AlarmEvent
from .dsc_it100 import IT100, PANIC_FIRE, PANIC_AMBULANCE, PANIC_PANIC
from .commands import IT100_COMMANDS

logger = logging.getLogger(__name__)


class DSCIntegrationModule(AlarmInterface):

    def __init__(self) -> None:
        super().__init__()
        self._panel: IT100 | None = None
        self._setup_values: dict = {}

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def on_load(self, setup_values: dict | None = None) -> None:
        self._setup_values = setup_values or {}

    def on_unload(self) -> None:
        if self._panel:
            self._panel.disconnect()
            self._panel = None

    # ------------------------------------------------------------------ #
    #  Host → Plugin commands                                              #
    # ------------------------------------------------------------------ #

    def receive(self, message: dict) -> None:
        """
        Dispatch a command from the host to the IT-100 panel.

        Required key in every message: "type"

        Supported types and their expected additional keys:

          connect            port: str, baud: int (default 9600)
          disconnect         (none)
          poll               (none)
          status_request     (none)
          arm_away           partition: int (default 1)
          arm_stay           partition: int (default 1)
          arm_no_delay       partition: int (default 1)
          arm_with_code      partition: int, code: str
          disarm             partition: int, code: str
          trigger_panic      panic_type: "fire"|"ambulance"|"panic" (default "panic")
          key_press          key: str, long_press: bool (default False)
          bypass_zone        zone: int, code: str (optional)
          set_time_stamp     enabled: bool
          set_time_broadcast enabled: bool
          set_temp_broadcast enabled: bool
          change_baud_rate   baud: int
        """
        msg_type = message.get("type")

        if msg_type == "connect":
            self._handle_connect(message)

        elif msg_type == "disconnect":
            self.on_unload()

        elif msg_type == "poll":
            self._require_panel().poll()

        elif msg_type == "status_request":
            self._require_panel().request_status()

        elif msg_type == "arm_away":
            self._require_panel().arm_away(partition=message.get("partition", 1))

        elif msg_type == "arm_stay":
            self._require_panel().arm_stay(partition=message.get("partition", 1))

        elif msg_type == "arm_no_delay":
            self._require_panel().arm_no_entry_delay(partition=message.get("partition", 1))

        elif msg_type == "arm_with_code":
            self._require_panel().arm_with_code(
                partition=message["partition"],
                code=message["code"],
            )

        elif msg_type == "disarm":
            self._require_panel().disarm(
                partition=message["partition"],
                code=message["code"],
            )

        elif msg_type == "trigger_panic":
            _panic_map = {
                "fire":       PANIC_FIRE,
                "ambulance":  PANIC_AMBULANCE,
                "panic":      PANIC_PANIC,
            }
            panic_type = _panic_map.get(message.get("panic_type", "panic"), PANIC_PANIC)
            self._require_panel().trigger_panic(panic_type)

        elif msg_type == "key_press":
            self._require_panel().key_press(
                key=message["key"],
                long_press=message.get("long_press", False),
            )

        elif msg_type == "bypass_zone":
            self._require_panel().bypass_zone(
                zone=message["zone"],
                code=message.get("code"),
            )

        elif msg_type == "set_time_stamp":
            self._require_panel().set_time_stamp(enabled=message["enabled"])

        elif msg_type == "set_time_broadcast":
            self._require_panel().set_time_broadcast(enabled=message["enabled"])

        elif msg_type == "set_temp_broadcast":
            self._require_panel().set_temp_broadcast(enabled=message["enabled"])

        elif msg_type == "change_baud_rate":
            self._require_panel().change_baud_rate(baud=message["baud"])

        else:
            logger.warning("DSC plugin received unknown command type: %r", msg_type)

    def send(self, message: dict) -> None:
        """
        Module → Host.
        The module calls this internally to post a message to the host.
        Thread-safe: can be called from background threads.

        Outgoing messages must include a "type" key. Supported types:

          zone_open           zone_id: int, label: str (optional)
          zone_closed         zone_id: int
          zone_bypassed       zone_id: int, bypassed: bool
          partition_armed     partition_id: int, mode: "stay"|"away"
          partition_disarmed  partition_id: int
          alarm_triggered     partition_id: int, zone_id: int (optional)
          alarm_restored      partition_id: int, zone_id: int (optional)
          alarm_panicked      partition_id: int, panic_type: str, panicked: bool
          error               detail: str
          ready               (none)
        """
        super().send(message)
    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _require_panel(self) -> IT100:
        if self._panel is None:
            raise RuntimeError("DSC plugin is not connected. Send a 'connect' message first.")
        return self._panel

    def _handle_connect(self, message: dict) -> None:
        port = message.get("port")
        baud = message.get("baud", 9600)
        if not port:
            self.send({"type": AlarmEvent.ERROR, "detail": "'connect' message missing 'port'"})
            return

        if self._panel:
            self._panel.disconnect()

        panel = IT100(port=port, baud=baud)
        self._register_callbacks(panel)
        try:
            panel.connect()
        except Exception as exc:
            self.send({"type": AlarmEvent.ERROR, "detail": f"Failed to connect: {exc}"})
            return

        self._panel = panel
        self.send({"type": AlarmEvent.READY})

    def _register_callbacks(self, panel: IT100) -> None:
        """Wire all relevant IT-100 events into self.send() for the manager."""

        # --- Zone events ---
        panel.on("zone_open",
                 lambda d: self.send({"type": AlarmEvent.ZONE_OPEN, "zone_id": d["zone"]}))
        panel.on("zone_restored",
                 lambda d: self.send({"type": AlarmEvent.ZONE_CLOSED, "zone_id": d["zone"]}))

        # --- Partition arm/disarm ---
        def _on_partition_armed(d):
            mode = d.get("mode", "")
            arm_event = AlarmEvent.ARMED_STAY if "Stay" in mode else AlarmEvent.ARMED_AWAY
            self.send({"type": arm_event, "partition_id": d["partition"]})

        panel.on("partition_armed",  _on_partition_armed)
        panel.on("partition_disarmed",
                 lambda d: self.send({"type": AlarmEvent.DISARMED, "partition_id": d["partition"]}))
        panel.on("user_opening",
                 lambda d: self.send({"type": AlarmEvent.DISARMED, "partition_id": d["partition"]}))
        panel.on("special_opening",
                 lambda d: self.send({"type": AlarmEvent.DISARMED, "partition_id": d["partition"]}))

        # --- Alarm / restore ---
        panel.on("partition_alarm",
                 lambda d: self.send({"type": AlarmEvent.ALARM_TRIGGERED, "partition_id": d["partition"]}))
        panel.on("zone_alarm",
                 lambda d: self.send({"type": AlarmEvent.ALARM_TRIGGERED,
                                      "partition_id": d["partition"], "zone_id": d["zone"]}))
        panel.on("zone_alarm_restore",
                 lambda d: self.send({"type": AlarmEvent.ALARM_RESTORED,
                                      "partition_id": d["partition"], "zone_id": d["zone"]}))

        # --- Panic keys ---
        for event, panic_type in (("621", "fire"), ("623", "ambulance"), ("625", "panic")):
            _pt = panic_type
            panel.on(event, lambda d, pt=_pt: self.send({
                "type": AlarmEvent.ALARM_PANICKED,
                "partition_id": 1,   # key events don't carry a partition number
                "panicked": True,
                "panic_type": pt,
            }))
        for event, panic_type in (("622", "fire"), ("624", "ambulance"), ("626", "panic")):
            _pt = panic_type
            panel.on(event, lambda d, pt=_pt: self.send({
                "type": AlarmEvent.ALARM_PANICKED,
                "partition_id": 1,
                "panicked": False,
                "panic_type": pt,
            }))

        # --- System errors ---
        panel.on("system_error",
                 lambda d: self.send({"type": AlarmEvent.ERROR,
                                      "detail": d.get("error_description", "Unknown error")}))


PLUGIN_CLASS = DSCIntegrationModule
