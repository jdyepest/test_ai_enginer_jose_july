from __future__ import annotations

import logging
import re
from pathlib import Path

from app.integrations.transcription_client import TranscriptionClient
from app.utils.logging import log_event

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, client: TranscriptionClient):
        self.client = client

    def transcript_for(self, path: Path, job_id: str) -> str:
        suffix = path.suffix.lower()
        if suffix == ".txt":
            transcript = path.read_text(encoding="utf-8")
        else:
            transcript = self.client.transcribe(path)
        normalized = normalize_transcript(transcript)
        log_event(
            logger,
            "TRANSCRIPT_READY",
            job_id=job_id,
            source=str(path),
            characters=len(normalized),
        )
        return normalized


def normalize_transcript(transcript: str) -> str:
    lines = []
    seen_headers: set[str] = set()
    for raw_line in transcript.splitlines():
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line:
            continue
        if line.lower() in {"transcript", "meeting transcript"}:
            if line.lower() in seen_headers:
                continue
            seen_headers.add(line.lower())
        lines.append(line)
    return "\n".join(lines) + "\n"

