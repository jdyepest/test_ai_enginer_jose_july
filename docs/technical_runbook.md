# Technical Runbook

## Environment

Install Python 3.12, then run:

```bash
make setup
cp .env.example .env
```

Use fake providers for local tests. Add API keys only to `.env`.

Real OpenAI test settings:

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
TRANSCRIPTION_PROVIDER=openai
TRANSCRIPTION_API_KEY=
TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
```

When `TRANSCRIPTION_API_KEY` is blank, the app reuses `OPENAI_API_KEY`.

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

The main real-OpenAI TXT validation used:

```text
job_35aade648cbcaefbc11f590b
status: NEEDS_REVIEW
model: gpt-4.1-mini
input: local_storage/intake/synthetic_retail_ai_transcript_downloads.txt
summary: local_storage/needs_review/job_35aade648cbcaefbc11f590b/retail_ai_automation_discovery_call_20260707_summary.json
deck: local_storage/needs_review/job_35aade648cbcaefbc11f590b/retail_ai_automation_discovery_call_20260707_deck.pptx
```

Failed jobs write:

```text
local_storage/failed/{job_id}/error.json
local_storage/failed/{job_id}/original_input_reference.txt
```

## Rerunning a Job

Duplicate events intentionally do not create another deck. To rerun locally, remove the job entry from `local_storage/jobs.json` and clear the job artifact folder, or change the source file content so the local content hash changes.

For the same local file, another option is to submit a simulated Google Drive event with a new
`file_version`. That creates a new deterministic job ID while preserving duplicate protection for
same-version events.

## Troubleshooting

- `FILE_NOT_FOUND`: confirm the file exists under `local_storage/intake`.
- `UNSUPPORTED_FILE_TYPE`: confirm the extension is one of `txt`, `mp3`, `m4a`, `wav`, or `mp4`.
- OpenAI authentication errors: confirm `OPENAI_API_KEY` is set in `.env` and restart the worker.
- Invalid AI JSON: check `local_storage/failed/{job_id}/error.json`; the OpenAI adapter now sends
  the Pydantic JSON schema to reduce this risk.
- `.mp4` transcription failures: confirm `ffmpeg` is installed and available on `PATH`.
- Duplicate output missing: check whether the event was intentionally ignored as a duplicate.

## Logging and Monitoring Recommendation

For production, send structured logs to Cloud Logging with `job_id`, event name, status, provider,
model name, duration, and error code. Alert on repeated `JOB_FAILED` events, high processing
latency, transcription failures, and schema validation failures. Track cost drivers per job:
meeting duration, transcription model, LLM model, token usage where available, and artifact size.

## Production Mapping

- Local fake Drive event becomes Google Workspace Events API.
- FastAPI local server becomes Cloud Run ingestion service.
- Local queue becomes Pub/Sub.
- Local JSON or Firestore emulator becomes Firestore.
- Local worker process becomes Cloud Run Job.
- Local folders become Google Drive folders or Cloud Storage.
- Console logs become Cloud Logging.
