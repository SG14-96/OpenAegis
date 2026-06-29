from pydantic import BaseModel
from typing import Optional

class SettingsModel(BaseModel):
    scope: str
    data: dict

class SettingsUpdate(BaseModel):
    scope: Optional[str] = None
    data: Optional[dict] = None

class AlarmZone(BaseModel):
    zone_id: int
    name: str
    partition_id: int
    is_bypassed: bool
    is_faulted: bool
    is_tampered: bool
    is_armed: bool

class AlarmPartition(BaseModel):
    partition_id: int
    name: str
    code: int
    is_armed: bool
    partitions: list[AlarmZone] = []

class AlarmSettingsModel(BaseModel):
    data: dict

class AlarmSettingsUpdate(BaseModel):
    data: Optional[dict] = None

class PluginSettingsModel(BaseModel):
    plugin_name: str
    is_currently_used: bool
    data: dict

class PluginSettingsUpdate(BaseModel):
    plugin_name: Optional[str] = None
    is_currently_used: Optional[bool] = None
    data: Optional[dict] = None

class AlarmCreateRequestBody(BaseModel):
    alarm_name: str
    module_path: str
    setup_values: dict | None = None


class AlarmUpdateRequestBody(BaseModel):
    alarm_name: str | None = None
    module_path: str | None = None
    setup_values: dict | None = None
