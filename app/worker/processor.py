from __future__ import annotations

import json
import logging
from pathlib import Path

from app.config import Settings
from app.integrations.firestore_repository import JobRepository
from app.integrations.pubsub_client import JobQueue, QueueMessage
from app.integrations.storage_client import LocalStorageClient
from app.integrations.transcription_client import FakeTranscriptionClient, OpenAiTranscriptionClient
from app.models.jobs import JobStatus
from app.services.presentation_service import PresentationService
from app.services.summarization_service import SummarizationService, build_llm_client
from app.services.transcription_service import TranscriptionService
from app.utils.logging import log_event
from app.utils.timestamps import utc_now_iso, yyyymmdd

logger = logging.getLogger(__name__)


class MeetingWorker:
    def __init__(self, settings: Settings, repository: JobRepository, queue: JobQueue):
        self.settings = settings
        self.repository = repository
        self.queue = queue
        self.storage = LocalStorageClient(settings.local_storage_path)
        transcription_client = (
            OpenAiTranscriptionClient(settings.transcription_api_key, settings.transcription_model)
            if settings.transcription_provider == "openai"
            else FakeTranscriptionClient()
        )
        self.transcription = TranscriptionService(transcription_client)
        self.summarization = SummarizationService(
            build_llm_client(settings.llm_provider, settings.openai_api_key, settings.openai_model),
            settings.prompt_version,
        )
        self.presentation = PresentationService()

    def process_next_message(self) -> bool:
        message = self.queue.pull_one()
        if message is None:
            return False
        self.process_message(message)
        return True

    def process_message(self, message: QueueMessage) -> None:
        self.process_job_id(message.job_id)
        self.queue.ack(message)

    def process_job_id(self, job_id: str) -> None:
        job = self.repository.claim(job_id)
        if job is None:
            existing = self.repository.get(job_id)
            log_event(
                logger,
                "DUPLICATE_EVENT_IGNORED",
                job_id=job_id,
                status=existing.status.value if existing else "missing",
            )
            return

        paths = self.storage.paths_for_job(job_id)
        source_path = Path(job.source_path)
        try:
            self.storage.archive_original(source_path, paths.archive_dir)
            transcript = self.transcription.transcript_for(source_path, job_id)
            transcript_path = paths.archive_dir / "normalized_transcript.txt"
            transcript_path.write_text(transcript, encoding="utf-8")

            summary = self.summarization.summarize(transcript, job_id)
            summary_name = f"{_meeting_slug(summary.meeting_title)}_{yyyymmdd()}_summary.json"
            summary_path = paths.review_dir / summary_name
            summary_path.write_text(summary.model_dump_json(indent=2), encoding="utf-8")

            deck_name = f"{_meeting_slug(summary.meeting_title)}_{yyyymmdd()}_deck.pptx"
            deck_path = paths.review_dir / deck_name
            self.presentation.create_deck(summary, deck_path, self.settings.prompt_version, job_id)

            self.repository.update(
                job_id,
                status=JobStatus.NEEDS_REVIEW.value,
                completed_at=utc_now_iso(),
                transcript_path=str(transcript_path),
                summary_path=str(summary_path),
                deck_path=str(deck_path),
                model_name=self.summarization.model_name,
                error_code=None,
                error_message=None,
                audit_events=[
                    *job.audit_events,
                    {"event": "TRANSCRIPT_READY", "timestamp": utc_now_iso()},
                    {"event": "LLM_RESPONSE_VALIDATED", "timestamp": utc_now_iso()},
                    {"event": "PRESENTATION_CREATED", "timestamp": utc_now_iso()},
                    {"event": "JOB_NEEDS_REVIEW", "timestamp": utc_now_iso()},
                ],
            )
            log_event(logger, "JOB_NEEDS_REVIEW", job_id=job_id, deck_path=str(deck_path))
        except Exception as exc:
            self._mark_failed(job_id, source_path, str(exc), exc.__class__.__name__)

    def _mark_failed(self, job_id: str, source_path: Path, message: str, code: str) -> None:
        paths = self.storage.paths_for_job(job_id)
        error = {
            "job_id": job_id,
            "stage": "worker_processing",
            "error_code": code,
            "error_message": message,
            "timestamp": utc_now_iso(),
        }
        (paths.failed_dir / "error.json").write_text(json.dumps(error, indent=2), encoding="utf-8")
        (paths.failed_dir / "original_input_reference.txt").write_text(
            str(source_path),
            encoding="utf-8",
        )
        current = self.repository.get(job_id)
        self.repository.update(
            job_id,
            status=JobStatus.FAILED.value,
            completed_at=utc_now_iso(),
            error_code=code,
            error_message=message,
            audit_events=[
                *(current.audit_events if current else []),
                {"event": "JOB_FAILED", "timestamp": utc_now_iso(), "code": code},
            ],
        )
        log_event(logger, "JOB_FAILED", job_id=job_id, error_code=code, error_message=message)


def _meeting_slug(value: str) -> str:
    from app.integrations.storage_client import slugify

    return slugify(value)
