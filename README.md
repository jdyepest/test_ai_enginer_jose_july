# Meeting Intelligence Automation POC

Local FastAPI proof of concept for turning a meeting transcript or recording into a structured summary, editable PowerPoint deck, and auditable job record.

```text
Meeting input
  -> transcript extraction or transcription
  -> structured AI analysis
  -> editable PPTX deck
  -> review-ready output package
```

## Architecture

```text
Fake Drive event script
  -> FastAPI ingestion service
  -> job repository
  -> job queue
  -> local Python worker
  -> local_storage/needs_review/{job_id}
```

The POC keeps the production boundary intact: ingestion validates and queues quickly, while long-running transcript, LLM, and PowerPoint work happens in the worker.

Production mapping:

```text
Google Drive folder
  -> Google Workspace Events API
  -> Pub/Sub
  -> Cloud Run ingestion API
  -> Firestore job audit record
  -> Cloud Run Job worker
  -> Drive or Cloud Storage review folder
```

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

The default `.env.example` uses local JSON and local file queue adapters so the demo can run without emulator processes. To use Google emulators, set:

```text
JOB_REPOSITORY_BACKEND=google
QUEUE_BACKEND=google
```

Required variables are documented in `.env.example`. Do not commit `.env`.

## Commands

```bash
make setup
make lint
make test
make emulators
make api
make worker
make send-test-event
make run-demo
```

## Run the Sample Flow

One-command local path:

```bash
make run-demo
```

Separate API and worker path:

```bash
make api
make worker
make send-test-event
```

The sample transcript is copied into `local_storage/intake`, ingested as a fake Drive event, queued, processed by the worker, and written to:

```text
local_storage/archive/{job_id}/normalized_transcript.txt
local_storage/needs_review/{job_id}/*_summary.json
local_storage/needs_review/{job_id}/*_deck.pptx
```

Inspect a job through the API:

```bash
curl http://127.0.0.1:8000/jobs/{job_id}
```

## Emulator Notes

Start Pub/Sub:

```bash
gcloud beta emulators pubsub start --project=meeting-intelligence-local
$(gcloud beta emulators pubsub env-init)
bash scripts/create_pubsub_resources.sh
```

Start Firestore:

```bash
firebase emulators:start --only firestore
```

Then run the API and worker with `JOB_REPOSITORY_BACKEND=google` and `QUEUE_BACKEND=google`.

## Known Limitations

- The default LLM and transcription providers are fake adapters for deterministic local tests.
- OpenAI adapters are present but require API keys and provider configuration.
- `.mp4` transcription with the OpenAI adapter requires `ffmpeg`.
- Google Drive subscriptions, Slack notifications, OAuth, and production Cloud Run deployment are documented future wiring, not part of the local POC.
- Human review is required before distribution.

