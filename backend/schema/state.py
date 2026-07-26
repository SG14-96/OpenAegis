from pydantic import BaseModel


class ZoneState(BaseModel):
    zone_id: int
    partition_id: int | None = None
    is_open: bool | None = None
    in_alarm: bool = False
    tampered: bool = False
    faulted: bool = False
    label: str | None = None


class PartitionState(BaseModel):
    partition_id: int
    state: str = "unknown"
    is_armed: bool = False
    arm_mode: str | None = None
    trouble: bool = False
    label: str | None = None
    last_user: int | None = None


class AlarmStateSnapshot(BaseModel):
    partitions: dict[str, PartitionState] = {}
    zones: dict[str, ZoneState] = {}
