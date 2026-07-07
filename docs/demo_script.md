# Demo Script

1. Show `samples/synthetic_retail_ai_transcript.txt` and explain that it represents a BrightLane Retail leadership operations meeting.
2. Run `make run-demo` or run API, worker, and `make send-test-event` in separate terminals.
3. Show the created job in `local_storage/jobs.json` or through `GET /jobs/{job_id}`.
4. Point out worker log events: `JOB_PROCESSING_STARTED`, `TRANSCRIPT_READY`, `LLM_RESPONSE_VALIDATED`, `PRESENTATION_CREATED`, and `JOB_NEEDS_REVIEW`.
5. Open the generated JSON summary in `local_storage/needs_review/{job_id}`.
6. Open the generated editable PowerPoint deck and show the five required slides.
7. Explain that the materials stop at `NEEDS_REVIEW`; human approval is still required.
8. Explain that production replaces the fake event with Google Drive events and the local worker with a Cloud Run Job.

