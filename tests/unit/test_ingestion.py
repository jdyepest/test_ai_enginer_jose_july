from __future__ import annotations

from pathlib import Path

from app.config import Settings
from app.integrations.firestore_repository import LocalJsonJobRepository
from app.integrations.pubsub_client import LocalFileJobQueue
from app.models.events import DriveFileEvent
from app.models.jobs import JobStatus
from app.services.ingestion_service import IngestionService


def _settings(tmp_path: Path) -> Settings:
    return Settings(local_storage_path=tmp_path)


def test_unsupported_input_is_rejected(tmp_path: Path) -> None:
    source = tmp_path / "intake" / "meeting.pdf"
    source.parent.mkdir()
    source.write_text("not supported", encoding="utf-8")
    settings = _settings(tmp_path)
    repository = LocalJsonJobRepository(tmp_path / "jobs.json")
    queue = LocalFileJobQueue(tmp_path / "queue.jsonl")

    response = IngestionService(settings, repository, queue).ingest_drive_event(
        DriveFileEvent(
            file_id="file-1",
            file_name=source.name,
            file_version="1",
            mime_type="application/pdf",
            local_path=str(source),
        )
    )

    job = repository.get(response.job_id)
    assert response.status == "rejected"
    assert job is not None
    assert job.status == JobStatus.REJECTED
    assert job.error_code == "UNSUPPORTED_FILE_TYPE"


def test_duplicate_event_does_not_publish_second_message(tmp_path: Path) -> None:
    source = tmp_path / "intake" / "meeting.txt"
    source.parent.mkdir()
    source.write_text("BrightLane transcript", encoding="utf-8")
    settings = _settings(tmp_path)
    repository = LocalJsonJobRepository(tmp_path / "jobs.json")
    queue_path = tmp_path / "queue.jsonl"
    queue = LocalFileJobQueue(queue_path)
    service = IngestionService(settings, repository, queue)
    event = DriveFileEvent(
        file_id="file-1",
        file_name=source.name,
        file_version="1",
        mime_type="text/plain",
        local_path=str(source),
    )

    first = service.ingest_drive_event(event)
    second = service.ingest_drive_event(event)

    assert first.status == "queued"
    assert second.status == "duplicate"
    assert queue_path.read_text(encoding="utf-8").count(first.job_id) == 1

