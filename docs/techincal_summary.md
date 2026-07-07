# Technical Runbook: Meeting Intelligence POC

## Purpose

This document explains how the local POC is structured, how to run it, where secrets live, and how to troubleshoot failures.

The POC processes a meeting transcript, audio file, or video file into:

* Structured meeting JSON
* Editable PowerPoint deck
* Review-ready artifacts
* A Firestore job record with processing history

## Architecture

```text
Meeting file or transcript
  ->
Ingestion API
  ->
Firestore job record
  ->
Pub/Sub job message
  ->
Worker
  ->
Transcript processing
  ->
LLM structured JSON
  ->
PPTX generation
  ->
Needs Review output folder
```

The ingestion API handles events quickly.

The worker handles slow tasks such as transcription, LLM processing, and PowerPoint generation.

## Local components

| Component     | Local implementation                            |
| ------------- | ----------------------------------------------- |
| Ingestion API | FastAPI running on localhost                    |
| Job queue     | Pub/Sub emulator                                |
| Job database  | Firestore emulator                              |
| Worker        | Python process consuming Pub/Sub messages       |
| Storage       | `local_storage/` folders                        |
| LLM           | OpenAI API or fake test adapter                 |
| Transcription | Configurable provider or local transcript input |

## Folder structure

```text
meeting-intelligence-poc/
├── app/
│   ├── api/
│   ├── services/
│   ├── integrations/
│   ├── worker/
│   ├── models/
│   └── config.py
├── scripts/
├── samples/
├── local_storage/
│   ├── intake/
│   ├── needs_review/
│   ├── approved_outputs/
│   ├── failed/
│   └── archive/
├── docs/
├── tests/
├── .env.example
├── firebase.json
├── requirements.txt
└── README.md
```

## Environment setup

Required local tools:

```text
Python 3.12
Google Cloud CLI
Firebase CLI
ffmpeg
```

Create and activate a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Copy the environment template:

```bash
cp .env.example .env
```

Required local environment variables:

```text
APP_ENV=local
LOG_LEVEL=INFO

GOOGLE_CLOUD_PROJECT=meeting-intelligence-local
PUBSUB_EMULATOR_HOST=localhost:8085
FIRESTORE_EMULATOR_HOST=127.0.0.1:8080

PUBSUB_JOB_TOPIC=meeting-jobs
PUBSUB_WORKER_SUBSCRIPTION=meeting-worker-sub

LOCAL_STORAGE_PATH=./local_storage

LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=

TRANSCRIPTION_PROVIDER=openai
TRANSCRIPTION_API_KEY=
```

Do not commit `.env`.

## API keys and secrets

For local development, API keys are stored only in `.env`.

For production, secrets must be stored in Google Secret Manager.

Do not store secrets in:

* GitHub
* Source code
* Firestore
* Logs
* Slide decks
* Shared Drive folders

The application must fail clearly when a required key is missing.

## Starting local services

Start the Pub/Sub emulator:

```bash
gcloud beta emulators pubsub start --project=meeting-intelligence-local
```

In a second terminal, configure the emulator variables:

```bash
$(gcloud beta emulators pubsub env-init)
```

Create the local topic and subscription:

```bash
gcloud pubsub topics create meeting-jobs
gcloud pubsub subscriptions create meeting-worker-sub \
  --topic=meeting-jobs
```

Start the Firestore emulator:

```bash
firebase emulators:start --only firestore
```

Start the FastAPI ingestion service:

```bash
uvicorn app.api.main:app --reload --port 8000
```

Start the worker:

```bash
python -m app.worker.main
```

Send a local test event:

```bash
python scripts/send_fake_drive_event.py
```

## Expected local flow

1. Place `synthetic_retail_ai_transcript.txt` in `local_storage/intake/`.
2. Run the fake Drive event script.
3. The ingestion API creates a Firestore job with status `QUEUED`.
4. The API publishes the job ID to Pub/Sub.
5. The worker receives the job.
6. The worker creates a normalized transcript, JSON summary, and PowerPoint deck.
7. Output files appear in `local_storage/needs_review/{job_id}/`.
8. The Firestore job status becomes `NEEDS_REVIEW`.

## Job states

```text
RECEIVED
QUEUED
PROCESSING
NEEDS_REVIEW
APPROVED
REJECTED
FAILED
```

The worker must update Firestore at every meaningful stage.

## Idempotency

Events may arrive more than once.

The job ID must be deterministic:

```text
sha256(source_file_id + ":" + source_file_version)
```

For local files without a Drive ID, use the file hash.

Rules:

* Ignore jobs already in `PROCESSING`.
* Ignore jobs already in `NEEDS_REVIEW` or `APPROVED`.
* Reprocess only when the source file version changes or a reviewer explicitly requests a revision.
* Never generate a duplicate deck from the same file version.

## Logging

Every log entry should include:

```text
job_id
source_file_id
status
processing_stage
timestamp
error_code
```

Required log events:

```text
JOB_RECEIVED
JOB_QUEUED
JOB_PROCESSING_STARTED
TRANSCRIPT_READY
LLM_REQUEST_STARTED
LLM_RESPONSE_VALIDATED
PRESENTATION_CREATED
JOB_NEEDS_REVIEW
JOB_FAILED
DUPLICATE_EVENT_IGNORED
```

Do not log raw transcripts or API keys at INFO level.

## Monitoring recommendations

For the POC:

* Review FastAPI logs in the terminal.
* Use the Firestore emulator UI to inspect job documents.
* Check output folders after each run.
* Save failure details in `local_storage/failed/{job_id}/`.

For production:

* Use Cloud Logging for API and worker logs.
* Create alerts for repeated worker failures.
* Monitor failed jobs by status in Firestore.
* Alert when processing time exceeds a configured threshold.
* Track transcription cost, LLM token usage, and revision rate.
* Review dead-letter queue messages if enabled.

## Troubleshooting

| Problem                    | Likely cause                                                     | Action                                                   |
| -------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------- |
| API cannot publish a job   | Pub/Sub emulator is not running                                  | Start emulator and recreate topic/subscription           |
| Worker receives no jobs    | Wrong subscription name or emulator environment variable missing | Check `.env`, terminal environment, and subscription     |
| Firestore connection fails | Firestore emulator is not running                                | Start Firebase emulator and check port 8080              |
| File not found             | Incorrect local file path                                        | Verify file is inside `local_storage/intake/`            |
| Audio extraction fails     | `ffmpeg` is missing or media file is invalid                     | Install `ffmpeg` and test file manually                  |
| LLM request fails          | Missing API key, quota issue, or invalid model name              | Check `.env`, provider dashboard, and logs               |
| AI JSON validation fails   | Model returned malformed output                                  | Retry once using a repair prompt, then mark job `FAILED` |
| PPTX generation fails      | Invalid summary data or formatting issue                         | Preserve JSON, log error, and inspect generator          |
| Duplicate deck created     | Idempotency check missing                                        | Verify deterministic job ID and atomic job claim         |

## Production mapping

| Local POC                  | Production service                              |
| -------------------------- | ----------------------------------------------- |
| Fake Drive event script    | Google Meet event, Zoom webhook, or Drive event |
| FastAPI localhost server   | Cloud Run ingestion API                         |
| Pub/Sub emulator           | Google Pub/Sub                                  |
| Firestore emulator         | Firestore                                       |
| Local worker process       | Cloud Run Job                                   |
| Local folders              | Google Drive and Cloud Storage                  |
| Terminal logs              | Cloud Logging                                   |
| Manual review notification | Slack notification                              |

## Recommended production monitoring

Track these metrics:

* Meetings processed per week
* Average processing time
* Transcription minutes
* LLM input and output tokens
* Cost per meeting
* Revision rate
* Failed jobs
* Duplicate events ignored
* Percentage of outputs approved without edits
* Percentage of action items with assigned owners

These metrics show whether the workflow is saving time and producing reliable leadership material.
