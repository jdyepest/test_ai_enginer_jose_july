# Meeting Intelligence Automation POC

Local FastAPI proof of concept for turning a meeting transcript or recording into a structured summary, editable PowerPoint deck, and auditable job record.

## Deliverables

Start here when reviewing the submission:

```text
docs/architecture.md
docs/cost_estimate.md
docs/client_overview.md
docs/technical_runbook.md
local_storage/intake/synthetic_retail_ai_transcript_downloads.txt
local_storage/needs_review/job_35aade648cbcaefbc11f590b/
```

The required documentation is split into four files:

- Architecture: `docs/architecture.md`
- Cost preview: `docs/cost_estimate.md`
- Client documentation, non-technical: `docs/client_overview.md`
- Team documentation, technical: `docs/technical_runbook.md`

Supporting docs are also included:

- Assumptions: `docs/assumptions.md`
- Demo walkthrough: `docs/demo_script.md`

The verified local POC output is:

```text
job_id: job_35aade648cbcaefbc11f590b
status: NEEDS_REVIEW
input: local_storage/intake/synthetic_retail_ai_transcript_downloads.txt
summary: local_storage/needs_review/job_35aade648cbcaefbc11f590b/retail_ai_automation_discovery_call_20260707_summary.json
deck: local_storage/needs_review/job_35aade648cbcaefbc11f590b/retail_ai_automation_discovery_call_20260707_deck.pptx
```

That run used the real OpenAI LLM on the supplied sample TXT transcript. The `.m4a` flow is implemented in code but has not yet been tested in this submission.

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

For real OpenAI testing, set these values in `.env`:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini

TRANSCRIPTION_PROVIDER=openai
TRANSCRIPTION_API_KEY=
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
```

If `TRANSCRIPTION_API_KEY` is blank, the app reuses `OPENAI_API_KEY`.

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

## Test Flows

### 1. Offline Smoke Test

```bash
make run-demo
```

This uses fake LLM/transcription adapters and verifies the full local pipeline without API keys.

### 2. Verified Real OpenAI TXT Test

This is the main test used during development with
`local_storage/intake/synthetic_retail_ai_transcript_downloads.txt`.

Start the API:

```bash
make api
```

Start the worker in another terminal:

```bash
make worker
```

Send a fake Drive event for a transcript:

```bash
python scripts/send_fake_drive_event.py \
  --path local_storage/intake/synthetic_retail_ai_transcript_downloads.txt
```

If the same file content was already processed, idempotency will return the old job. To force a
new test against the same local file, simulate a Google Drive version:

```bash
curl -s -X POST http://127.0.0.1:8000/events/drive \
  -H 'Content-Type: application/json' \
  -d '{
    "source_type": "google_drive",
    "file_id": "synthetic-retail-ai-transcript-downloads",
    "file_name": "synthetic_retail_ai_transcript_downloads.txt",
    "file_version": "openai-test-4-readable-deck",
    "mime_type": "text/plain",
    "local_path": "local_storage/intake/synthetic_retail_ai_transcript_downloads.txt"
  }'
```

The latest verified OpenAI TXT test produced:

```text
job_35aade648cbcaefbc11f590b
status: NEEDS_REVIEW
summary: local_storage/needs_review/job_35aade648cbcaefbc11f590b/retail_ai_automation_discovery_call_20260707_summary.json
deck: local_storage/needs_review/job_35aade648cbcaefbc11f590b/retail_ai_automation_discovery_call_20260707_deck.pptx
```

### 3. Create Another TXT Example

Use another transcript by copying it into intake:

```bash
cp /path/to/another_transcript.txt local_storage/intake/another_transcript.txt
python scripts/send_fake_drive_event.py --path local_storage/intake/another_transcript.txt
```

Then inspect the returned `job_id`:

```bash
curl http://127.0.0.1:8000/jobs/{job_id}
```

If you want to rerun the same TXT file content, local idempotency will prevent a duplicate deck.
Use a new simulated Drive version instead:

```bash
curl -s -X POST http://127.0.0.1:8000/events/drive \
  -H 'Content-Type: application/json' \
  -d '{
    "source_type": "google_drive",
    "file_id": "synthetic-retail-ai-transcript-downloads",
    "file_name": "synthetic_retail_ai_transcript_downloads.txt",
    "file_version": "your-new-version-name",
    "mime_type": "text/plain",
    "local_path": "local_storage/intake/synthetic_retail_ai_transcript_downloads.txt"
  }'
```

### 4. Audio Flow, Implemented But Not Yet Tested

Copy an audio file into intake:

```bash
cp /path/to/meeting.m4a local_storage/intake/meeting.m4a
```

Then send the fake event:

```bash
python scripts/send_fake_drive_event.py --path local_storage/intake/meeting.m4a
```

The `.m4a`, `.mp3`, `.wav`, and `.mp4` branches are wired to the transcription provider, but this
submission has only verified the TXT transcript flow. `.mp4` also requires `ffmpeg`.

Supported input types:

```text
txt, mp3, m4a, wav, mp4
```

### 5. Separate API and Worker Sample

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
- OpenAI adapters are present but require API keys and provider configuration. For transcription,
  start with `TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe` for low-cost testing, or use
  `gpt-4o-transcribe` for higher-quality tests.
- Audio transcription inputs are implemented but not yet tested end to end in this submission.
- `.mp4` transcription with the OpenAI adapter requires `ffmpeg`.
- Google Drive subscriptions, Slack notifications, OAuth, and production Cloud Run deployment are documented future wiring, not part of the local POC.
- Human review is required before distribution.
