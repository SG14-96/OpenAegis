from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AlarmHistoryEvent(BaseModel):
    """One row of GET /api/v1/alarm/events — see crud/events.py."""
    id: str
    category: Literal["arming", "alarm"]
    event_type: str
    partition_id: int
    last_user: int | None = None
    trigger_type: str | None = None
    created_at: datetime
