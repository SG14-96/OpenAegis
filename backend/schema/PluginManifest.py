from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, Union

from pydantic import BaseModel


class StepOption(BaseModel):
    label: str
    value: Union[str, int]


class StepInput(BaseModel):
    type: str
    placeholder: str


class ConnectionSetupStep(BaseModel):
    step: str
    details: str
    options: list[StepOption] | None = None
    input: StepInput | None = None


class PluginManifest(BaseModel):
    name: str
    version: str
    description: str | None = None
    author: str
    connectionType: Literal["mqtt", "http", "websocket", "serial", "other"] = "other"
    connectionSetupSteps: list[ConnectionSetupStep] | None = None
    dependencies: list[str] = []

    @classmethod
    def from_file(cls, path: Path) -> "PluginManifest":
        return cls.model_validate(json.loads(path.read_text()))
