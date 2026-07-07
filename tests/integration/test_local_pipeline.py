from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.integrations.firestore_repository import LocalJsonJobRepository
from app.integrations.pubsub_client import LocalFileJobQueue
from app.models.events import DriveFileEvent
from app.models.jobs import JobStatus
from app.services.ingestion_service import IngestionService
from app.worker.processor import MeetingWorker


def test_worker_processes_test_transcript_and_duplicate_does_not_create_second_deck(
    tmp_path: Path,
) -> None:
    intake = tmp_path / "intake"
    intake.mkdir()
    source = intake / "synthetic_retail_ai_transcript.txt"
    source.write_text(
        "BrightLane wants a pilot with human review and evidence-backed action items.",
        encoding="utf-8",
    )
    settings = Settings(
        local_storage_path=tmp_path,
        llm_provider="fake",
        transcription_provider="fake",
        transcription_api_key="",
    )
    repository = LocalJsonJobRepository(tmp_path / "jobs.json")
    queue = LocalFileJobQueue(tmp_path / "queue.jsonl")
    ingestion = IngestionService(settings, repository, queue)
    event = DriveFileEvent(
        file_id="brightlane-transcript-001",
        file_name=source.name,
        file_version="1",
        mime_type="text/plain",
        local_path=str(source),
    )

    response = ingestion.ingest_drive_event(event)
    assert repository.get(response.job_id).status == JobStatus.QUEUED  # type: ignore[union-attr]

    worker = MeetingWorker(settings, repository, queue)
    assert worker.process_next_message() is True
    job = repository.get(response.job_id)
    assert job is not None
    assert job.status == JobStatus.NEEDS_REVIEW
    assert job.summary_path is not None and Path(job.summary_path).exists()
    assert job.deck_path is not None and Path(job.deck_path).exists()

    second = ingestion.ingest_drive_event(event)
    assert second.status == "duplicate"
    decks = list((tmp_path / "needs_review" / response.job_id).glob("*.pptx"))
    assert len(decks) == 1
