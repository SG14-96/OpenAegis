from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from db.database import Base


class ArmingEvent(Base):
    """
    One row per partition arm/disarm transition (AlarmEvent.ARMED_STAY,
    ARMED_AWAY, DISARMED), as reported by the active plugin.
    """
    __tablename__ = "arming_events"

    id = Column(Integer, primary_key=True, index=True)
    partition_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    # Panel-reported user code responsible for the change (mirrors
    # PartitionState.last_user), not a foreign key to our own users table —
    # the panel's user numbering is independent of app accounts.
    last_user = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class AlarmStateEvent(Base):
    """
    One row per change in the alarm's actual trigger state
    (AlarmEvent.ALARM_TRIGGERED, ALARM_RESTORED, ALARM_PANICKED), as
    reported by the active plugin.
    """
    __tablename__ = "alarm_state_events"

    id = Column(Integer, primary_key=True, index=True)
    partition_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    # Populated for ALARM_PANICKED events ("panic_type": panic/fire/auxiliary).
    trigger_type = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
