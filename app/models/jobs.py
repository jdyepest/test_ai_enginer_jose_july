from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    RECEIVED = "RECEIVED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class JobRecord(BaseModel):
    job_id: str
    source_type: str
    source_file_id: str
    source_file_name: str
    source_file_version: str
    source_path: str
    mime_type: str
    content_hash: str
    status: JobStatus = JobStatus.RECEIVED
    attempt_count: int = 0
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    transcript_path: str | None = None
    summary_path: str | None = None
    deck_path: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    prompt_version: str
    model_name: str | None = None
    audit_events: list[dict[str, str]] = Field(default_factory=list)


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    deck_path: str | None
    summary_path: str | None
    error_message: str | None

