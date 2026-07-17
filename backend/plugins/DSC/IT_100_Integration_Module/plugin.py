"""
DSC IT-100 integration plugin for OpenAegis.

Uses the py-dsc-it100 package's synchronous facade (IT100Client) and typed
event model.  The IT100Client runs the serial driver on a background
thread; typed Event callbacks arrive on that thread and are translated to
canonical AlarmEvent messages via self.send() (thread-safe per
AlarmInterface).

Host commands are executed on a single worker thread so receive() never
blocks the host, and command failures (panel 502 errors, timeouts) are
reported as canonical "error" events.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from alarm.events import AlarmEvent
from plugins.AlarmInterface import AlarmInterface

from dsc_it100 import (
    IT100Client, IT100Error,
    ZoneEvent, PartitionEvent, PanicEvent, SystemEvent,
    ZoneEventKind, PartitionEventKind, SystemEventKind,
    PANIC_FIRE, PANIC_AMBULANCE, PANIC_PANIC,
)

logger = logging.getLogger(__name__)

_PANIC_TYPES = {
    "fire":      PANIC_FIRE,
    "ambulance": PANIC_AMBULANCE,
    "medical":   PANIC_AMBULANCE,
    "panic":     PANIC_PANIC,
    "police":    PANIC_PANIC,
}

#: PartitionEventKind values that map 1:1 to a canonical alarm event.
_ZONE_EVENT_MAP = {
    ZoneEventKind.OPEN:     AlarmEvent.ZONE_OPEN,
    ZoneEventKind.RESTORED: AlarmEvent.ZONE_CLOSED,
}


def _setup_value(setup_values: dict, *keys, default=None):
    """Fetch a wizard value by any of several keys (name or step index)."""
    for key in keys:
        for k in (key, str(key)):
            if k in setup_values and setup_values[k] not in (None, ""):
                return setup_values[k]
    return default


class DSCIntegrationModule(AlarmInterface):

    def __init__(self) -> None:
        super().__init__()
        self._panel: IT100Client | None = None
        self._code: str | None = None          # arm/disarm code from setup
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="dsc-it100-cmd")

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                           #
    # ------------------------------------------------------------------ #

    def on_load(self, setup_values: dict | None = None) -> None:
        """
        Connect using the setup wizard values.

        Expected values (keyed by name or by wizard step index):
          port  (or step 0) : serial port, e.g. /dev/ttyUSB0   [required]
          baud  (or step 1) : baud rate (default 9600)
          code  (or step 2) : user code for arm/disarm commands (optional)

        If no port was configured, loading succeeds and connection is
        deferred until a "connect" message is received.
        """
        values = setup_values or {}
        code = _setup_value(values, "code", "user_code", 2)
        self._code = str(code) if code is not None else None

        port = _setup_value(values, "port", "serial_port", 0)
        baud = int(_setup_value(values, "baud", "baud_rate", 1, default=9600))
        if port:
            self._connect(str(port), baud)   # raises on failure → PluginLoadError
        else:
            logger.info("DSC plugin loaded without a port; waiting for 'connect'.")

    def on_unload(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
        if self._panel:
            try:
                self._panel.disconnect()
            finally:
                self._panel = None

    # ------------------------------------------------------------------ #
    #  Host → Plugin commands                                              #
    # ------------------------------------------------------------------ #

    def receive(self, message: dict) -> None:
        """
        Dispatch a command from the host.  Never blocks: commands run on a
        worker thread and failures are reported as "error" events.

        Canonical commands (see alarm.commands.AlarmCommand):

          status        → replies with a "status" snapshot + READY
          arm_away      partition: int = 1
          arm_stay      partition: int = 1
          disarm        partition: int = 1, user_code: str (falls back to setup code)
          bypass_zone   zone_id: int, bypassed: bool (keypad toggle; see note)
          panic         panic_type: "fire"|"ambulance"|"medical"|"panic"|"police"

        Additional commands:

          connect            port: str, baud: int = 9600
          disconnect         (none)
          poll               (none)
          arm_no_delay       partition: int = 1
          arm_with_code      partition: int, code: str
          key_press          key: str, long_press: bool = False
          set_time_stamp / set_time_broadcast / set_temp_broadcast   enabled: bool
          change_baud_rate   baud: int

        Note on bypass: the IT-100 virtual keypad *toggles* bypass and only
        operates on the partition the module is enrolled on.
        """
        self._executor.submit(self._execute, message)

    def _execute(self, message: dict) -> None:
        msg_type = message.get("type")
        try:
            self._dispatch(msg_type, message)
        except IT100Error as exc:
            self.send({"type": AlarmEvent.ERROR,
                       "detail": f"{msg_type}: {exc}"})
        except Exception as exc:   # noqa: BLE001 — surface anything to the host
            logger.exception("DSC plugin command %r failed", msg_type)
            self.send({"type": AlarmEvent.ERROR,
                       "detail": f"{msg_type}: {exc}"})

    def _dispatch(self, msg_type: str | None, message: dict) -> None:
        if msg_type == "connect":
            port = message.get("port")
            if not port:
                self.send({"type": AlarmEvent.ERROR,
                           "detail": "'connect' message missing 'port'"})
                return
            self._connect(port, message.get("baud", 9600))
            return

        if msg_type == "disconnect":
            if self._panel:
                self._panel.disconnect()
                self._panel = None
            return

        panel = self._require_panel()
        partition = int(message.get("partition", 1))
        code = message.get("user_code") or message.get("code") or self._code

        if msg_type == "status":
            panel.request_status()
            self.send({"type": "status", **panel.snapshot()})
            self.send({"type": AlarmEvent.READY})

        elif msg_type == "poll":
            panel.poll()

        elif msg_type in ("arm_away", "arm_stay", "arm_no_delay"):
            mode = {"arm_away": "away", "arm_stay": "stay",
                    "arm_no_delay": "no_delay"}[msg_type]
            if code:
                panel.arm_with_auto_code(partition, code, mode=mode)
            elif msg_type == "arm_away":
                panel.arm_away(partition)
            elif msg_type == "arm_stay":
                panel.arm_stay(partition)
            else:
                panel.arm_no_entry_delay(partition)

        elif msg_type == "arm_with_code":
            panel.arm_with_code(partition, message["code"])

        elif msg_type == "disarm":
            if not code:
                self.send({"type": AlarmEvent.ERROR,
                           "detail": "disarm requires 'user_code' (none configured)"})
                return
            panel.disarm(partition, code)

        elif msg_type in ("panic", "trigger_panic"):
            raw = message.get("panic_type", "panic")
            panel.trigger_panic(_PANIC_TYPES.get(raw, PANIC_PANIC))

        elif msg_type == "bypass_zone":
            zone = message.get("zone_id") or message.get("zone")
            if zone is None:
                self.send({"type": AlarmEvent.ERROR,
                           "detail": "bypass_zone requires 'zone_id'"})
                return
            panel.bypass_zone(int(zone), code)
            self.send({"type": AlarmEvent.ZONE_BYPASSED,
                       "zone_id": int(zone),
                       "bypassed": bool(message.get("bypassed", True))})

        elif msg_type == "key_press":
            panel.key_press(message["key"], message.get("long_press", False))

        elif msg_type == "set_time_stamp":
            panel.set_time_stamp(message["enabled"])

        elif msg_type == "set_time_broadcast":
            panel.set_time_broadcast(message["enabled"])

        elif msg_type == "set_temp_broadcast":
            panel.set_temp_broadcast(message["enabled"])

        elif msg_type == "change_baud_rate":
            panel.change_baud_rate(message["baud"])

        else:
            logger.warning("DSC plugin received unknown command type: %r", msg_type)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _require_panel(self) -> IT100Client:
        if self._panel is None:
            raise IT100Error("Not connected. Send a 'connect' message first.")
        return self._panel

    def _connect(self, port: str, baud: int = 9600) -> None:
        if self._panel:
            self._panel.disconnect()
            self._panel = None

        panel = IT100Client(port=port, baud=int(baud))
        panel.on_event(self._on_panel_event)
        panel.connect()          # raises on failure
        self._panel = panel

        # Populate the state store; ignore startup hiccups (e.g. panel busy).
        try:
            panel.request_status()
        except IT100Error as exc:
            logger.warning("Initial status request failed: %s", exc)

        self.send({"type": AlarmEvent.READY})

    # ------------------------------------------------------------------ #
    #  Panel → Host event translation                                      #
    # ------------------------------------------------------------------ #

    def _on_panel_event(self, event) -> None:
        """Translate typed dsc_it100 events into canonical AlarmEvents.

        Runs on the IT100Client driver thread; self.send() is thread-safe.
        """
        if isinstance(event, ZoneEvent):
            simple = _ZONE_EVENT_MAP.get(event.kind)
            if simple is not None:
                self.send({"type": simple, "zone_id": event.zone})
            elif event.kind is ZoneEventKind.ALARM:
                self.send({"type": AlarmEvent.ALARM_TRIGGERED,
                           "partition_id": event.partition,
                           "zone_id": event.zone})
            elif event.kind is ZoneEventKind.ALARM_RESTORED:
                self.send({"type": AlarmEvent.ALARM_RESTORED,
                           "partition_id": event.partition,
                           "zone_id": event.zone})

        elif isinstance(event, PartitionEvent):
            if event.kind is PartitionEventKind.ARMED:
                armed = (AlarmEvent.ARMED_STAY
                         if event.arm_mode and event.arm_mode.is_stay
                         else AlarmEvent.ARMED_AWAY)
                self.send({"type": armed, "partition_id": event.partition})
            elif event.kind is PartitionEventKind.DISARMED:
                self.send({"type": AlarmEvent.DISARMED,
                           "partition_id": event.partition})
            elif event.kind is PartitionEventKind.IN_ALARM:
                self.send({"type": AlarmEvent.ALARM_TRIGGERED,
                           "partition_id": event.partition})

        elif isinstance(event, PanicEvent):
            self.send({"type": AlarmEvent.ALARM_PANICKED,
                       # Panic key events don't carry a partition on the wire.
                       "partition_id": 1,
                       "panicked": not event.restored,
                       "panic_type": event.kind.value})

        elif isinstance(event, SystemEvent):
            if event.kind is SystemEventKind.SYSTEM_ERROR:
                # Errors for our own commands surface as exceptions in
                # _execute; this catches unsolicited/async 502s.
                self.send({"type": AlarmEvent.ERROR,
                           "detail": event.data.get("error_description",
                                                    "Unknown panel error")})


PLUGIN_CLASS = DSCIntegrationModule
