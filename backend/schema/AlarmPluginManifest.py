from pydantic import BaseModel
from typing import Literal, Optional

class AlarmPluginManifest(BaseModel):
    name: str
    version: str
    author: str
    description: Optional[str] = None
    connectionType: Literal["mqtt", "http", "websocket", "serial", "other"] = "other"
    connectionSetupSteps: Optional[list[dict]] = None
    capabilities: Optional[dict] = None
    dependencies: list[str] = []   # pip requirement specifiers, e.g. ["pyserial>=3.5"]