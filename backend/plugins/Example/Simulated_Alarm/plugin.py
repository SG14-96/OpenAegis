"""
Simulated alarm plugin — send/receive communication test only.

No hardware, no state machine, no timers. Every receive() command
triggers one or more immediate send() calls so you can verify the full
host → plugin → host round-trip for every event type the manager handles.

Canonical commands accepted by receive()
-----------------------------------------
status                                  Replies with READY.
arm_away      partition (int=1)         Replies with ARMED_AWAY.
arm_stay      partition (int=1)         Replies with ARMED_STAY.
disarm        partition (int=1)         Replies with DISARMED.
panic         partition (int=1),        Replies with ALARM_PANICKED.
              panic_type (str="panic")
bypass_zone   zone_id (int),            Replies with ZONE_BYPASSED.
              bypassed (bool=True)

Test-only commands (not part of the canonical contract)
--------------------------------------------------------
trigger_alarm partition (int=1),        Replies with ALARM_TRIGGERED.
              zone_id (int, optional)
restore_alarm partition (int=1),        Replies with ALARM_RESTORED.
              zone_id (int, optional)
zone_open     zone_id (int)             Replies with ZONE_OPEN.
zone_close    zone_id (int)             Replies with ZONE_CLOSED.
full_sequence                           Fires one of every event type in order.
"""

import logging

from alarm.events import AlarmEvent
from plugins.AlarmInterface import AlarmInterface

logger = logging.getLogger(__name__)


class SimulatedAlarm(AlarmInterface):

    def on_load(self, setup_values: dict | None = None) -> None:
        logger.info("SimulatedAlarm: loaded (setup_values=%s)", setup_values)

    def on_unload(self) -> None:
        logger.info("SimulatedAlarm: unloaded")

    # ------------------------------------------------------------------ #
    #  Host → Plugin                                                       #
    # ------------------------------------------------------------------ #

    def receive(self, message: dict) -> None:
        msg_type = message.get("type")

        # --- Canonical commands ---

        if msg_type == "status":
            self.send({"type": AlarmEvent.READY})

        elif msg_type == "arm_away":
            self.send({"type": AlarmEvent.ARMED_AWAY, "partition_id": message.get("partition", 1)})

        elif msg_type == "arm_stay":
            self.send({"type": AlarmEvent.ARMED_STAY, "partition_id": message.get("partition", 1)})

        elif msg_type == "disarm":
            self.send({"type": AlarmEvent.DISARMED, "partition_id": message.get("partition", 1)})

        elif msg_type == "panic":
            self.send({
                "type": AlarmEvent.ALARM_PANICKED,
                "partition_id": message.get("partition", 1),
                "panic_type": message.get("panic_type", "panic"),
                "panicked": True,
            })

        elif msg_type == "bypass_zone":
            zone_id = message.get("zone_id")
            if zone_id is None:
                self.send({"type": AlarmEvent.ERROR, "detail": "bypass_zone requires 'zone_id'"})
                return
            self.send({
                "type": AlarmEvent.ZONE_BYPASSED,
                "zone_id": zone_id,
                "bypassed": message.get("bypassed", True),
            })

        # --- Test-only commands ---

        elif msg_type == "trigger_alarm":
            payload = {
                "type": AlarmEvent.ALARM_TRIGGERED,
                "partition_id": message.get("partition", 1),
            }
            if "zone_id" in message:
                payload["zone_id"] = message["zone_id"]
            self.send(payload)

        elif msg_type == "restore_alarm":
            payload = {
                "type": AlarmEvent.ALARM_RESTORED,
                "partition_id": message.get("partition", 1),
            }
            if "zone_id" in message:
                payload["zone_id"] = message["zone_id"]
            self.send(payload)

        elif msg_type == "zone_open":
            zone_id = message.get("zone_id")
            if zone_id is None:
                self.send({"type": AlarmEvent.ERROR, "detail": "zone_open requires 'zone_id'"})
                return
            self.send({"type": AlarmEvent.ZONE_OPEN, "zone_id": zone_id, "label": f"Zone {zone_id}"})

        elif msg_type == "zone_close":
            zone_id = message.get("zone_id")
            if zone_id is None:
                self.send({"type": AlarmEvent.ERROR, "detail": "zone_close requires 'zone_id'"})
                return
            self.send({"type": AlarmEvent.ZONE_CLOSED, "zone_id": zone_id})

        elif msg_type == "full_sequence":
            self._fire_full_sequence()

        else:
            self.send({"type": AlarmEvent.ERROR, "detail": f"Unknown command: {msg_type!r}"})
            logger.warning("SimulatedAlarm: unknown command %r", msg_type)

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _fire_full_sequence(self) -> None:
        """Emit one of every event type so every manager handler is exercised."""
        self.send({"type": AlarmEvent.ZONE_OPEN,       "zone_id": 1, "label": "Front Door"})
        self.send({"type": AlarmEvent.ZONE_CLOSED,     "zone_id": 1})
        self.send({"type": AlarmEvent.ZONE_BYPASSED,   "zone_id": 1, "bypassed": True})
        self.send({"type": AlarmEvent.ARMED_AWAY,      "partition_id": 1})
        self.send({"type": AlarmEvent.ARMED_STAY,      "partition_id": 1})
        self.send({"type": AlarmEvent.ALARM_TRIGGERED, "partition_id": 1, "zone_id": 1})
        self.send({"type": AlarmEvent.ALARM_RESTORED,  "partition_id": 1, "zone_id": 1})
        self.send({"type": AlarmEvent.ALARM_PANICKED,  "partition_id": 1, "panic_type": "panic", "panicked": True})
        self.send({"type": AlarmEvent.DISARMED,        "partition_id": 1})
        self.send({"type": AlarmEvent.READY})


PLUGIN_CLASS = SimulatedAlarm
