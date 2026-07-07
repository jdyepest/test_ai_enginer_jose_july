# Architecture

## Target Production Architecture

```text
Google Drive "Meeting Intake" folder
  -> Google Workspace Events API
  -> Google Pub/Sub topic: drive-events
  -> Cloud Run service: ingestion-api
  -> Firestore job record and audit trail
  -> Cloud Run Job: meeting-worker
  -> Google Drive "Needs Review" folder
  -> Slack notification
  -> Human review and approval
```

## Local Architecture

```text
Fake Drive event script
  -> FastAPI ingestion service
  -> local JSON or Firestore emulator job repository
  -> local file queue or Pub/Sub emulator
  -> local Python worker
  -> local_storage/needs_review
```

The local adapters keep the demo runnable on a clean laptop. The same ingestion and worker services can also use Firestore and Pub/Sub emulators by changing environment variables.

## Data Flow

1. A transcript or recording appears in `local_storage/intake`.
2. A fake Drive event posts normalized metadata to `/events/drive`.
3. The ingestion API validates the file, creates a deterministic job, and publishes only the job ID.
4. The worker claims the queued job.
5. The worker reads or transcribes the input, normalizes the transcript, asks the LLM adapter for structured output, validates it with Pydantic, and creates an editable PowerPoint.
6. Artifacts are written under `archive/{job_id}` and `needs_review/{job_id}`.
7. The job record becomes `NEEDS_REVIEW` or `FAILED`.

## Component Responsibilities

- FastAPI ingestion: validate events, enforce idempotency, create durable job records, publish queue messages.
- Job repository: store status, source references, output paths, timestamps, errors, and audit events.
- Queue: decouple event receipt from long-running processing.
- Worker: perform transcript, summary, and deck generation.
- Local storage: keep original inputs, normalized transcripts, review artifacts, and failure files.

## Architecture Decisions

Pub/Sub is used because the target production event transport already fits the workflow and avoids database polling. Firestore is used for durable job state and audit history, not as a queue. Cloud Run Job is the production fit for longer-running AI work. Redis, BullMQ, Celery, and polling are intentionally excluded to keep the Python implementation aligned with Google Cloud eventing.

