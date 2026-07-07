from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.models.events import DriveFileEvent  # noqa: E402
from app.services.ingestion_service import IngestionService  # noqa: E402
from app.services.job_service import build_job_queue, build_job_repository  # noqa: E402
from app.utils.logging import configure_logging  # noqa: E402
from app.worker.processor import MeetingWorker  # noqa: E402


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    settings.local_storage_path.mkdir(parents=True, exist_ok=True)
    intake = settings.local_storage_path / "intake"
    intake.mkdir(parents=True, exist_ok=True)
    sample = Path("samples/synthetic_retail_ai_transcript.txt")
    target = intake / sample.name
    shutil.copy2(sample, target)

    repository = build_job_repository(settings)
    queue = build_job_queue(settings)
    ingestion = IngestionService(settings, repository, queue)
    response = ingestion.ingest_drive_event(
        DriveFileEvent(
            source_type="local",
            file_id="brightlane-transcript-001",
            file_name=target.name,
            file_version="1",
            mime_type="text/plain",
            local_path=str(target),
        )
    )
    print(response.model_dump_json())

    worker = MeetingWorker(settings, repository, queue)
    worker.process_next_message()
    job = repository.get(response.job_id)
    if job:
        print(job.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
