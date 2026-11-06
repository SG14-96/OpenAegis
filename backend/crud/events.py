from datetime import datetime

from sqlalchemy.orm import Session

from models.events import AlarmStateEvent, ArmingEvent


def list_alarm_history(db: Session, limit: int, before: datetime | None = None) -> list[dict]:
    """
    Newest-first merge of arming and alarm-state events. Each table is
    capped at `limit` before merging, which is enough to produce the
    `limit` newest rows overall; `before` pages further back in time.
    """
    arming_query = db.query(ArmingEvent)
    alarm_query = db.query(AlarmStateEvent)
    if before is not None:
        arming_query = arming_query.filter(ArmingEvent.created_at < before)
        alarm_query = alarm_query.filter(AlarmStateEvent.created_at < before)

    arming = arming_query.order_by(ArmingEvent.created_at.desc()).limit(limit).all()
    alarms = alarm_query.order_by(AlarmStateEvent.created_at.desc()).limit(limit).all()

    rows = [
        {
            "id": f"arming-{e.id}",
            "category": "arming",
            "event_type": e.event_type,
            "partition_id": e.partition_id,
            "last_user": e.last_user,
            "trigger_type": None,
            "created_at": e.created_at,
        }
        for e in arming
    ] + [
        {
            "id": f"alarm-{e.id}",
            "category": "alarm",
            "event_type": e.event_type,
            "partition_id": e.partition_id,
            "last_user": None,
            "trigger_type": e.trigger_type,
            "created_at": e.created_at,
        }
        for e in alarms
    ]
    rows.sort(key=lambda r: r["created_at"], reverse=True)
    return rows[:limit]
