from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.dependencies import ingestion_service, job_repository, settings
from app.models.events import DriveFileEvent, HealthResponse, IngestionResponse, PubSubPushEnvelope
from app.models.jobs import JobStatusResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", environment=settings().app_env)


@router.post("/events/drive", response_model=IngestionResponse)
def local_drive_event(event: DriveFileEvent) -> IngestionResponse:
    return ingestion_service().ingest_drive_event(event)


@router.post("/events/pubsub/drive", response_model=IngestionResponse)
def pubsub_drive_event(envelope: PubSubPushEnvelope) -> IngestionResponse:
    return ingestion_service().ingest_drive_event(envelope.to_drive_event())


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str) -> JobStatusResponse:
    job = job_repository().get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatusResponse(
        job_id=job.job_id,
        status=job.status,
        deck_path=job.deck_path,
        summary_path=job.summary_path,
        error_message=job.error_message,
    )

