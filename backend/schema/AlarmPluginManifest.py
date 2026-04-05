from pydantic import BaseModel
from typing import Optional

class AlarmPluginManifest(BaseModel):
    name: str
    version: str
    author: str
    description: Optional[str] = None
    connectionType: str = "mqtt" | "http" | "websocket" | "serial" | "other"
    connectionSetupSteps: Optional[dict] = None
    capabilities: Optional[dict] = None