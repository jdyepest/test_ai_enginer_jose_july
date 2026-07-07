#!/usr/bin/env bash
set -euo pipefail

cat <<'MSG'
Start the emulators in separate terminals:

1. Pub/Sub:
   gcloud beta emulators pubsub start --project=meeting-intelligence-local
   $(gcloud beta emulators pubsub env-init)

2. Firestore:
   firebase emulators:start --only firestore

Then create Pub/Sub resources:
   bash scripts/create_pubsub_resources.sh
MSG

