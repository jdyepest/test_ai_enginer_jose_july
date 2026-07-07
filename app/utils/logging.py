from __future__ import annotations

import logging
import sys


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )


def log_event(
    logger: logging.Logger,
    event: str,
    job_id: str | None = None,
    **fields: object,
) -> None:
    payload = {"event": event, **fields}
    if job_id:
        payload["job_id"] = job_id
    logger.info(payload)
