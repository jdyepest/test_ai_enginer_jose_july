from __future__ import annotations

from app.config import Settings
from app.integrations.firestore_repository import (
    FirestoreJobRepository,
    JobRepository,
    LocalJsonJobRepository,
)
from app.integrations.pubsub_client import JobQueue, LocalFileJobQueue, PubSubJobQueue


def build_job_repository(settings: Settings) -> JobRepository:
    if settings.job_repository_backend == "google":
        return FirestoreJobRepository(project=settings.google_cloud_project)
    return LocalJsonJobRepository(settings.local_db_path)


def build_job_queue(settings: Settings) -> JobQueue:
    if settings.queue_backend == "google":
        return PubSubJobQueue(
            project=settings.google_cloud_project,
            topic=settings.pubsub_job_topic,
            subscription=settings.pubsub_worker_subscription,
        )
    return LocalFileJobQueue(settings.local_queue_path)

