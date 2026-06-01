from __future__ import annotations
from enum import Enum
from pydantic import BaseModel

class PanicState(str, Enum):
    FIRE    = "fire"
    MEDICAL = "medical"
    POLICE  = "police"

class ArmState(str, Enum):
    DISARMED    = "disarmed"
    ARMED_STAY  = "armed_stay"
    ARMED_AWAY  = "armed_away"
    TRIGGERED   = "triggered"


class ZoneState(BaseModel):
    id: int
    label: str
    partition_id: int | None = None
    open: bool = False
    bypassed: bool = False


class PartitionState(BaseModel):
    id: int
    label: str
    arm_state: ArmState = ArmState.DISARMED
    panic_state: PanicState | None = None
    # Zone IDs assigned to this partition
    zone_ids: list[int] = []


class AlarmState(BaseModel):
    # Partitions are the primary unit of arm/disarm state.
    # Zones are stored flat here and referenced by zone_ids in each partition.
    partitions: dict[int, PartitionState] = {}
    zones: dict[int, ZoneState] = {}
    active_plugin: str | None = None
    last_event: str | None = None
