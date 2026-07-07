# Technical Runbook

## Environment

Install Python 3.12, then run:

```bash
make setup
cp .env.example .env
```

Use fake providers for local tests. Add API keys only to `.env`.

## Local Services

Run separately:

```bash
make api
make worker
make send-test-event
```

Or run the direct local pipeline:

```bash
make run-demo
```

## Emulator Usage

Use `make emulators` for startup instructions. Set `JOB_REPOSITORY_BACKEND=google` and `QUEUE_BACKEND=google` after Pub/Sub and Firestore emulators are running.

## Inspecting Jobs

Local adapter jobs live in:

```text
local_storage/jobs.json
```

API status:

```bash
curl http://127.0.0.1:8000/jobs/{job_id}
```

Failed jobs write:

```text
local_storage/failed/{job_id}/error.json
local_storage/failed/{job_id}/original_input_reference.txt
```

## Rerunning a Job

Duplicate events intentionally do not create another deck. To rerun locally, remove the job entry from `local_storage/jobs.json` and clear the job artifact folder, or change the source file content so the local content hash changes.

## Production Mapping

- Local fake Drive event becomes Google Workspace Events API.
- FastAPI local server becomes Cloud Run ingestion service.
- Local queue becomes Pub/Sub.
- Local JSON or Firestore emulator becomes Firestore.
- Local worker process becomes Cloud Run Job.
- Local folders become Google Drive folders or Cloud Storage.
- Console logs become Cloud Logging.

