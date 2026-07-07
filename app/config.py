from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _csv(name: str, default: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "local")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "meeting-intelligence-local")
    pubsub_job_topic: str = os.getenv("PUBSUB_JOB_TOPIC", "meeting-jobs")
    pubsub_worker_subscription: str = os.getenv(
        "PUBSUB_WORKER_SUBSCRIPTION", "meeting-worker-sub"
    )
    local_storage_path: Path = Path(os.getenv("LOCAL_STORAGE_PATH", "./local_storage"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "fake")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    transcription_provider: str = os.getenv("TRANSCRIPTION_PROVIDER", "fake")
    transcription_api_key: str = os.getenv("TRANSCRIPTION_API_KEY", "")
    max_file_size_mb: int = int(os.getenv("MAX_FILE_SIZE_MB", "500"))
    supported_file_types: tuple[str, ...] = tuple(
        _csv("SUPPORTED_FILE_TYPES", "txt,mp3,m4a,wav,mp4")
    )
    prompt_version: str = os.getenv("PROMPT_VERSION", "v1")
    job_repository_backend: str = os.getenv("JOB_REPOSITORY_BACKEND", "local_json")
    queue_backend: str = os.getenv("QUEUE_BACKEND", "local_file")

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def local_db_path(self) -> Path:
        return self.local_storage_path / "jobs.json"

    @property
    def local_queue_path(self) -> Path:
        return self.local_storage_path / "queue" / f"{self.pubsub_worker_subscription}.jsonl"


def get_settings() -> Settings:
    return Settings()
