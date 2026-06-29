from __future__ import annotations
from enum import Enum
from pydantic import BaseModel


class AlarmCommand(str, Enum):
    ARM_STAY    = "arm_stay"
    ARM_AWAY    = "arm_away"
    DISARM      = "disarm"
    BYPASS_ZONE = "bypass_zone"
    PANIC       = "panic"
    STATUS      = "status"


class CommandPayload(BaseModel):
    command: AlarmCommand
    partition_id: int = 1
    zone_id: int | None = None
    user_code: str | None = None
    panic_type: str | None = None
    bypassed: bool = True
