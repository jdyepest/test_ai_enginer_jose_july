# Cost Estimate

Assumptions:

```text
20 meetings per month
45 minutes average per meeting
900 transcription minutes per month
20 LLM summarization calls
20 deck-generation jobs
30 days of archive retention for POC
```

## Fixed Costs

- Cloud Run ingestion service: usually near zero at low volume if scaled to zero.
- Firestore storage for job records: low fixed cost for small metadata records.
- Pub/Sub topics and subscriptions: low fixed cost at this volume.
- Archive storage: low for 30-day retention unless video files are large.

## Variable Costs

- Transcription: roughly proportional to 900 audio/video minutes per month.
- LLM summarization: proportional to transcript length and response size for 20 calls.
- Cloud Run Job execution: proportional to processing time and memory allocation.
- Storage egress or Drive operations: expected to be minimal for the POC volume.

## Cost Controls

- Keep human review before distribution.
- Retain POC artifacts for 30 days.
- Track tokens, model name, meeting duration, and output size per job before scaling.
- Pilot with transcripts first when possible to avoid unnecessary transcription spend.

