from __future__ import annotations

import time

from app.config import get_settings
from app.services.job_service import build_job_queue, build_job_repository
from app.utils.logging import configure_logging
from app.worker.processor import MeetingWorker


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    worker = MeetingWorker(settings, build_job_repository(settings), build_job_queue(settings))
    while True:
        processed = worker.process_next_message()
        if not processed:
            time.sleep(2)


if __name__ == "__main__":
    main()

