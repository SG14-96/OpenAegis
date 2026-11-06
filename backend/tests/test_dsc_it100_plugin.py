import pytest

pytest.importorskip("dsc_it100")

from dsc_it100 import (
    PANIC_AMBULANCE, PANIC_FIRE, PANIC_PANIC,
    ArmMode, PanicEvent, PanicKind, PartitionEvent, PartitionEventKind, TroubleEvent, TroubleKind,
)

from alarm.commands import AlarmCommand, CommandPayload
from alarm.events import AlarmEvent
from plugins.DSC.IT_100_Integration_Module.plugin import DSCIntegrationModule
from schema.state import AlarmStateSnapshot


class FakePanel:
    def __init__(self, partitions=None):
        self.calls = []
        self._partitions = partitions or {}

    def trigger_panic(self, wire):
        self.calls.append(("panic", wire))

    def snapshot(self):
        return {"partitions": self._partitions, "zones": {}}


@pytest.fixture
def plugin():
    p = DSCIntegrationModule()
    p.sent = []
    p.set_message_handler(p.sent.append)
    p._panel = FakePanel({1: {"partition_id": 1, "state": "armed", "is_armed": True, "last_user": 7}})
    return p


@pytest.mark.parametrize("panic_type, wire", [
    ("panic", PANIC_PANIC),
    ("fire", PANIC_FIRE),
    ("auxiliary", PANIC_AMBULANCE),
])
def test_frontend_panic_types_map_to_the_right_wire_value(plugin, panic_type, wire):
    plugin.receive({"type": "panic", "partition": 1, "panic_type": panic_type})
    assert plugin._panel.calls == [("panic", wire)]


def test_unknown_panic_type_is_rejected_not_guessed(plugin):
    plugin.receive({"type": "panic", "partition": 1, "panic_type": "police"})
    assert plugin._panel.calls == []
    assert plugin.sent[-1]["type"] == AlarmEvent.ERROR


@pytest.mark.parametrize("kind, expected", [
    (PanicKind.AMBULANCE, "auxiliary"),
    (PanicKind.AUX, "auxiliary"),
    (PanicKind.FIRE, "fire"),
    (PanicKind.DURESS, "panic"),
])
def test_panel_panic_kinds_map_to_app_vocabulary(plugin, kind, expected):
    plugin._on_panel_event(PanicEvent(command="625", packet={}, kind=kind))
    assert plugin.sent[-1]["panic_type"] == expected


def test_armed_event_carries_last_user_and_refreshes_snapshot(plugin):
    plugin._on_panel_event(PartitionEvent(
        command="652", packet={}, kind=PartitionEventKind.ARMED, partition=1, arm_mode=ArmMode.STAY,
    ))
    assert plugin.sent[0] == {"type": AlarmEvent.ARMED_STAY, "partition_id": 1, "last_user": 7}
    assert plugin.sent[1]["type"] == AlarmEvent.STATE_SNAPSHOT


def test_trouble_event_is_forwarded(plugin):
    plugin._on_panel_event(TroubleEvent(command="802", packet={}, kind=TroubleKind.AC_POWER, restored=False))
    assert plugin.sent[-1] == {"type": AlarmEvent.TROUBLE, "trouble_type": "ac_power", "restored": False}


def test_is_legal_rejects_arming_an_armed_partition(plugin):
    state = AlarmStateSnapshot.model_validate({
        "partitions": {"1": {"partition_id": 1, "state": "armed", "is_armed": True}},
    })
    legal, reason = plugin.is_legal(CommandPayload(command=AlarmCommand.ARM_AWAY), state)
    assert not legal and "already armed" in reason
