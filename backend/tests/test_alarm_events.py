import asyncio
from datetime import datetime, timedelta, timezone

from alarm.events import AlarmEvent
from alarm.manager import AlarmManager
from crud.events import list_alarm_history
from models.events import AlarmStateEvent, ArmingEvent


class FakeWS:
    def __init__(self):
        self.sent = []

    async def broadcast(self, data: str) -> None:
        self.sent.append(data)


def _dispatch(manager: AlarmManager, msg: dict) -> None:
    asyncio.run(manager._on_plugin_event("test", msg))


def test_arming_event_is_recorded_with_last_user(session_factory):
    ws = FakeWS()
    manager = AlarmManager(ws, session_factory)

    _dispatch(manager, {"type": AlarmEvent.ARMED_AWAY, "partition_id": 1, "last_user": 40})

    with session_factory() as db:
        rows = db.query(ArmingEvent).all()
    assert [(r.event_type, r.partition_id, r.last_user) for r in rows] == [("armed_away", 1, 40)]
    assert len(ws.sent) == 1


def test_panic_records_trigger_type_and_skips_restore(session_factory):
    manager = AlarmManager(FakeWS(), session_factory)

    _dispatch(manager, {"type": AlarmEvent.ALARM_PANICKED, "partition_id": 1, "panic_type": "fire", "panicked": True})
    _dispatch(manager, {"type": AlarmEvent.ALARM_PANICKED, "partition_id": 1, "panic_type": "fire", "panicked": False})
    _dispatch(manager, {"type": AlarmEvent.ALARM_TRIGGERED, "partition_id": 1})

    with session_factory() as db:
        rows = db.query(AlarmStateEvent).order_by(AlarmStateEvent.id).all()
    assert [(r.event_type, r.trigger_type) for r in rows] == [
        ("alarm_panicked", "fire"),
        ("alarm_triggered", None),
    ]


def test_non_history_events_are_only_broadcast(session_factory):
    ws = FakeWS()
    manager = AlarmManager(ws, session_factory)

    _dispatch(manager, {"type": AlarmEvent.ZONE_OPEN, "zone_id": 3})
    _dispatch(manager, {"type": AlarmEvent.TROUBLE, "trouble_type": "ac_power", "restored": False})

    with session_factory() as db:
        assert db.query(ArmingEvent).count() == 0
        assert db.query(AlarmStateEvent).count() == 0
    assert len(ws.sent) == 2


def test_troubles_are_tracked_and_served_with_state(session_factory):
    manager = AlarmManager(FakeWS(), session_factory)

    _dispatch(manager, {"type": AlarmEvent.TROUBLE, "trouble_type": "ac_power", "restored": False})
    _dispatch(manager, {"type": AlarmEvent.TROUBLE, "trouble_type": "battery", "restored": False})
    _dispatch(manager, {"type": AlarmEvent.TROUBLE, "trouble_type": "ac_power", "restored": True})
    # A plugin snapshot replaces partitions/zones but must not wipe troubles.
    _dispatch(manager, {"type": AlarmEvent.STATE_SNAPSHOT, "partitions": {}, "zones": {}})

    assert manager.state_snapshot.troubles == ["battery"]


def test_history_merges_tables_newest_first_and_pages(session_factory):
    t0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
    with session_factory() as db:
        db.add_all([
            ArmingEvent(partition_id=1, event_type="armed_stay", created_at=t0),
            AlarmStateEvent(partition_id=1, event_type="alarm_triggered", created_at=t0 + timedelta(minutes=1)),
            ArmingEvent(partition_id=1, event_type="disarmed", created_at=t0 + timedelta(minutes=2)),
        ])
        db.commit()

        rows = list_alarm_history(db, limit=2)
        assert [r["event_type"] for r in rows] == ["disarmed", "alarm_triggered"]

        older = list_alarm_history(db, limit=2, before=rows[-1]["created_at"])
        assert [r["event_type"] for r in older] == ["armed_stay"]
