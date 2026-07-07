from __future__ import annotations

from functools import lru_cache

from app.config import Settings, get_settings
from app.integrations.firestore_repository import JobRepository
from app.integrations.pubsub_client import JobQueue
from app.services.ingestion_service import IngestionService
from app.services.job_service import build_job_queue, build_job_repository


@lru_cache
def settings() -> Settings:
    return get_settings()


def job_repository() -> JobRepository:
    return build_job_repository(settings())


def job_queue() -> JobQueue:
    return build_job_queue(settings())


def ingestion_service() -> IngestionService:
    current_settings = settings()
    return IngestionService(current_settings, job_repository(), job_queue())

