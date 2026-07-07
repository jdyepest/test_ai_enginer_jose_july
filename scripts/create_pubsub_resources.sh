#!/usr/bin/env bash
set -euo pipefail

gcloud pubsub topics create "${PUBSUB_JOB_TOPIC:-meeting-jobs}" \
  --project="${GOOGLE_CLOUD_PROJECT:-meeting-intelligence-local}" || true

gcloud pubsub subscriptions create "${PUBSUB_WORKER_SUBSCRIPTION:-meeting-worker-sub}" \
  --topic="${PUBSUB_JOB_TOPIC:-meeting-jobs}" \
  --project="${GOOGLE_CLOUD_PROJECT:-meeting-intelligence-local}" || true

