from __future__ import annotations

import base64
import json
from typing import Literal

from pydantic import BaseModel, Field


class DriveFileEvent(BaseModel):
    source_type: Literal["local", "google_drive"] = "local"
    file_id: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    file_version: str = Field(min_length=1)
    mime_type: str = Field(min_length=1)
    local_path: str | None = None


class PubSubMessage(BaseModel):
    data: str
    messageId: str | None = None
    publishTime: str | None = None
    attributes: dict[str, str] | None = None


class PubSubPushEnvelope(BaseModel):
    message: PubSubMessage
    subscription: str | None = None

    def to_drive_event(self) -> DriveFileEvent:
        payload = base64.b64decode(self.message.data).decode("utf-8")
        return DriveFileEvent.model_validate(json.loads(payload))


class IngestionResponse(BaseModel):
    status: Literal["queued", "duplicate", "rejected"]
    job_id: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    environment: str

