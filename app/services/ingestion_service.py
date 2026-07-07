from __future__ import annotations

import logging
from pathlib import Path

from app.config import Settings
from app.integrations.firestore_repository import JobRepository
from app.integrations.pubsub_client import JobQueue
from app.models.events import DriveFileEvent, IngestionResponse
from app.models.jobs import JobRecord, JobStatus
from app.utils.file_hash import sha256_file, sha256_text
from app.utils.logging import log_event
from app.utils.timestamps import utc_now_iso

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, settings: Settings, repository: JobRepository, queue: JobQueue):
        self.settings = settings
        self.repository = repository
        self.queue = queue

    def ingest_drive_event(self, event: DriveFileEvent) -> IngestionResponse:
        source_path = Path(event.local_path or "")
        job_id, content_hash = self._job_identity(event, source_path)

        existing = self.repository.get(job_id)
        if existing:
            log_event(
                logger,
                "DUPLICATE_EVENT_IGNORED",
                job_id=job_id,
                status=existing.status.value,
                file_id=event.file_id,
            )
            return IngestionResponse(status="duplicate", job_id=job_id)

        job = self._new_job(event, source_path, job_id, content_hash)
        log_event(
            logger,
            "JOB_RECEIVED",
            job_id=job_id,
            file_id=event.file_id,
            source=str(source_path),
        )

        validation_error = self._validation_error(event, source_path)
        if validation_error:
            code, message, status = validation_error
            job.status = status
            job.completed_at = utc_now_iso()
            job.error_code = code
            job.error_message = message
            job.audit_events.append(
                {"event": "JOB_FAILED", "timestamp": utc_now_iso(), "code": code}
            )
            self.repository.save(job)
            log_event(logger, "JOB_FAILED", job_id=job_id, error_code=code, error_message=message)
            return IngestionResponse(status="rejected", job_id=job_id)

        job.status = JobStatus.QUEUED
        job.audit_events.append({"event": "JOB_QUEUED", "timestamp": utc_now_iso()})
        self.repository.save(job)
        self.queue.publish_job(job_id)
        log_event(
            logger,
            "JOB_QUEUED",
            job_id=job_id,
            file_id=event.file_id,
            source=str(source_path),
        )
        return IngestionResponse(status="queued", job_id=job_id)

    def _job_identity(self, event: DriveFileEvent, source_path: Path) -> tuple[str, str]:
        if event.source_type == "google_drive":
            key = f"{event.file_id}:{event.file_version}"
            digest = sha256_text(key)
            return f"job_{digest[:24]}", digest
        if source_path.exists():
            digest = sha256_file(source_path)
        else:
            digest = sha256_text(f"{event.file_id}:{event.file_version}:{event.file_name}")
        return f"job_{digest[:24]}", digest

    def _new_job(
        self,
        event: DriveFileEvent,
        source_path: Path,
        job_id: str,
        content_hash: str,
    ) -> JobRecord:
        return JobRecord(
            job_id=job_id,
            source_type=event.source_type,
            source_file_id=event.file_id,
            source_file_name=event.file_name,
            source_file_version=event.file_version,
            source_path=str(source_path),
            mime_type=event.mime_type,
            content_hash=content_hash,
            created_at=utc_now_iso(),
            prompt_version=self.settings.prompt_version,
        )

    def _validation_error(
        self, event: DriveFileEvent, source_path: Path
    ) -> tuple[str, str, JobStatus] | None:
        extension = Path(event.file_name).suffix.lower().lstrip(".")
        if extension not in self.settings.supported_file_types:
            return (
                "UNSUPPORTED_FILE_TYPE",
                f"Unsupported file extension: .{extension or 'none'}",
                JobStatus.REJECTED,
            )
        if event.source_type == "local" and not source_path.exists():
            return (
                "FILE_NOT_FOUND",
                f"Local source file does not exist: {source_path}",
                JobStatus.FAILED,
            )
        if source_path.exists() and source_path.stat().st_size > self.settings.max_file_size_bytes:
            return (
                "FILE_TOO_LARGE",
                f"File exceeds {self.settings.max_file_size_mb} MB limit: {source_path}",
                JobStatus.REJECTED,
            )
        return None
