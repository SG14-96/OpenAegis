"""
DSC IT-100 plugin, backed by py-dsc-it100 (https://github.com/SG14-96/dsc_it100).

Uses IT100Client, the library's blocking/threaded facade built specifically
for hosts like AlarmInterface: it runs the panel's asyncio driver on its own
background thread and calls our on_event callback from that thread, which is
safe here because AlarmInterface.send() is thread-safe by contract.

Event mapping
-------------
Only DSC events with a direct AlarmEvent counterpart are translated 1:1
(zone open/restore, partition armed/disarmed/in-alarm, panic). Everything
else that changes panel state (ready/not-ready/exit-delay/entry-delay/busy/
zone tamper/fault/...) has no matching AlarmEvent, so instead of inventing
new event semantics we just push a fresh STATE_SNAPSHOT — the frontend can
still read the fine-grained `state` string per partition from there.

Known limitations (protocol, not implementation gaps):
* bypass_zone drives the virtual keypad blindly — the IT-100 only confirms
  a bypass via keypad LCD text (901), not a discrete event, so we can't
  reliably emit a confirmed AlarmEvent.ZONE_BYPASSED here.
* The IT-100 has no partition-scoped "alarm restored" signal distinct from
  disarm (disarm silences the alarm), so AlarmEvent.ALARM_RESTORED is never
  emitted by this plugin — emitting it on every disarm would be a guess.
* PanicEvent from the panel doesn't carry a partition number; we report it
  against partition 1, matching this app's single-partition-by-default
  command shape (CommandPayload.partition_id defaults to 1 too).
"""
from __future__ import annotations

import logging

from dsc_it100 import (
    IT100Client,
    ZoneEvent, ZoneEventKind,
    PartitionEvent, PartitionEventKind,
    PanicEvent,
    TroubleEvent,
    SystemEvent, SystemEventKind,
    PANIC_FIRE, PANIC_AMBULANCE, PANIC_PANIC,
    PanelError, CommandTimeout, CommandRejected, NotConnectedError,
)

from alarm.commands import AlarmCommand, CommandPayload
from alarm.events import AlarmEvent
from plugins.AlarmInterface import AlarmInterface
from plugins.exceptions import PluginConfigError
from schema.state import AlarmStateSnapshot

logger = logging.getLogger(__name__)

# setup_values is keyed by wizard step index — see manifest.json's
# connectionSetupSteps (0: serial port, 1: baud rate, 2: arm/disarm code).
_STEP_PORT = "0"
_STEP_BAUD = "1"
_STEP_CODE = "2"

_DEFAULT_BAUD = 9600

# AlarmCommand.PANIC's panic_type string -> the wire value trigger_panic() expects.
_PANIC_TYPE_TO_WIRE = {
    "fire": PANIC_FIRE,
    "ambulance": PANIC_AMBULANCE,
    "panic": PANIC_PANIC,
}

# Partition states that block arming — everything else (ready, ready_to_force_arm,
# unknown, ...) is left for the panel itself to accept or reject.
_NOT_READY_TO_ARM = {"not_ready", "busy", "keypad_lockout"}

_PANEL_COMMAND_ERRORS = (PanelError, CommandTimeout, CommandRejected, NotConnectedError)


class DSCIntegrationModule(AlarmInterface):

    def __init__(self) -> None:
        super().__init__()
        self._panel: IT100Client | None = None
        self._code: str | None = None

    # ------------------------------------------------------------------ #
    #  Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def on_load(self, setup_values: dict | None = None) -> None:
        setup_values = setup_values or {}
        port = setup_values.get(_STEP_PORT)
        if not port:
            raise PluginConfigError("DSC IT-100: no serial port configured.")
        baud = int(setup_values.get(_STEP_BAUD) or _DEFAULT_BAUD)
        code = setup_values.get(_STEP_CODE)
        self._code = str(code) if code is not None else None

        self._panel = IT100Client(str(port), baud=baud)
        self._panel.on_event(self._on_panel_event)
        self._panel.connect()

        try:
            self._panel.request_status()
            self._panel.request_labels()
        except _PANEL_COMMAND_ERRORS as exc:
            logger.warning("DSC IT-100: startup status/labels request failed: %s", exc)

        self._emit_snapshot()
        self.send({"type": AlarmEvent.READY})

    def on_unload(self) -> None:
        if self._panel is not None:
            self._panel.disconnect()
            self._panel = None

    # ------------------------------------------------------------------ #
    #  Legality                                                             #
    # ------------------------------------------------------------------ #

    def is_legal(self, command: CommandPayload, state: AlarmStateSnapshot) -> tuple[bool, str | None]:
        partition = state.partitions.get(str(command.partition_id))

        if command.command in (AlarmCommand.ARM_STAY, AlarmCommand.ARM_AWAY):
            if partition is None:
                return True, None
            if partition.is_armed:
                return False, f"Partition {command.partition_id} is already armed."
            if partition.state in _NOT_READY_TO_ARM:
                return False, f"Partition {command.partition_id} is not ready to arm ({partition.state})."
            return True, None

        if command.command is AlarmCommand.BYPASS_ZONE:
            # The IT-100's virtual keypad bypass sequence only works while
            # the partition is disarmed (see module docstring).
            if partition is not None and partition.is_armed:
                return False, "Zones cannot be bypassed while the partition is armed."
            return True, None

        # DISARM also silences an active alarm and must always reach the
        # panel; PANIC and STATUS are never blocked either.
        return True, None

    # ------------------------------------------------------------------ #
    #  Host → Plugin                                                       #
    # ------------------------------------------------------------------ #

    def receive(self, message: dict) -> None:
        if self._panel is None:
            self.send({"type": AlarmEvent.ERROR, "detail": "DSC IT-100: plugin not connected."})
            return

        msg_type = message.get("type")
        partition = message.get("partition", 1)

        try:
            if msg_type == AlarmCommand.STATUS.value:
                self._panel.request_status()

            elif msg_type == AlarmCommand.ARM_AWAY.value:
                self._arm(partition, mode="away")

            elif msg_type == AlarmCommand.ARM_STAY.value:
                self._arm(partition, mode="stay")

            elif msg_type == AlarmCommand.DISARM.value:
                code = message.get("user_code") or self._code
                if not code:
                    self.send({"type": AlarmEvent.ERROR, "detail": "DSC IT-100: disarm requires a user code."})
                    return
                self._panel.disarm(partition, code)

            elif msg_type == AlarmCommand.BYPASS_ZONE.value:
                zone_id = message.get("zone_id")
                if zone_id is None:
                    self.send({"type": AlarmEvent.ERROR, "detail": "bypass_zone requires 'zone_id'"})
                    return
                code = message.get("user_code") or self._code
                self._panel.bypass_zone(zone_id, code)

            elif msg_type == AlarmCommand.PANIC.value:
                panic_type = message.get("panic_type", "panic")
                self._panel.trigger_panic(_PANIC_TYPE_TO_WIRE.get(panic_type, PANIC_PANIC))

            else:
                self.send({"type": AlarmEvent.ERROR, "detail": f"Unknown command: {msg_type!r}"})
                logger.warning("DSC IT-100: unknown command %r", msg_type)

        except _PANEL_COMMAND_ERRORS as exc:
            self.send({"type": AlarmEvent.ERROR, "detail": str(exc)})

    def _arm(self, partition: int, mode: str) -> None:
        # With a stored code, use arm_with_auto_code so the driver can answer
        # a Code Required (900) event on panels that need one to finish
        # arming; plain arm_away/arm_stay carry no code on the wire at all.
        if self._code:
            self._panel.arm_with_auto_code(partition, self._code, mode=mode)
        elif mode == "away":
            self._panel.arm_away(partition)
        else:
            self._panel.arm_stay(partition)

    # ------------------------------------------------------------------ #
    #  Plugin → Host                                                       #
    # ------------------------------------------------------------------ #

    def _on_panel_event(self, event) -> None:
        if isinstance(event, ZoneEvent):
            self._handle_zone_event(event)
        elif isinstance(event, PartitionEvent):
            self._handle_partition_event(event)
        elif isinstance(event, PanicEvent):
            self._handle_panic_event(event)
        elif isinstance(event, SystemEvent):
            self._handle_system_event(event)
        elif isinstance(event, TroubleEvent):
            logger.info("DSC IT-100: trouble %s restored=%s", event.kind.value, event.restored)
        else:
            logger.debug("DSC IT-100: unhandled event %r", event)

    def _handle_zone_event(self, event: ZoneEvent) -> None:
        if event.kind is ZoneEventKind.OPEN:
            self.send({"type": AlarmEvent.ZONE_OPEN, "zone_id": event.zone})
        elif event.kind is ZoneEventKind.RESTORED:
            self.send({"type": AlarmEvent.ZONE_CLOSED, "zone_id": event.zone})
        else:
            # Alarm/tamper/fault (and their restores) have no dedicated
            # AlarmEvent — refresh the snapshot so the flag is still visible.
            self._emit_snapshot()

    def _handle_partition_event(self, event: PartitionEvent) -> None:
        if event.kind is PartitionEventKind.ARMED:
            is_stay = event.arm_mode is not None and event.arm_mode.is_stay
            self.send({
                "type": AlarmEvent.ARMED_STAY if is_stay else AlarmEvent.ARMED_AWAY,
                "partition_id": event.partition,
            })
        elif event.kind is PartitionEventKind.DISARMED:
            self.send({"type": AlarmEvent.DISARMED, "partition_id": event.partition})
        elif event.kind is PartitionEventKind.IN_ALARM:
            self.send({"type": AlarmEvent.ALARM_TRIGGERED, "partition_id": event.partition})
        else:
            # ready/not_ready/exit_delay/entry_delay/busy/code_required/...
            # have no AlarmEvent counterpart — surface them via a snapshot
            # refresh instead of inventing new event semantics.
            self._emit_snapshot()

    def _handle_panic_event(self, event: PanicEvent) -> None:
        self.send({
            "type": AlarmEvent.ALARM_PANICKED,
            "partition_id": 1,
            "panic_type": event.kind.value,
            "panicked": not event.restored,
        })

    def _handle_system_event(self, event: SystemEvent) -> None:
        if event.kind in (SystemEventKind.SYSTEM_ERROR, SystemEventKind.COMMAND_ERROR):
            self.send({"type": AlarmEvent.ERROR, "detail": f"{event.kind.value}: {event.data}"})

    def _emit_snapshot(self) -> None:
        snapshot = self._panel.snapshot()
        self.send({
            "type": AlarmEvent.STATE_SNAPSHOT,
            "partitions": snapshot["partitions"],
            "zones": snapshot["zones"],
        })


PLUGIN_CLASS = DSCIntegrationModule
