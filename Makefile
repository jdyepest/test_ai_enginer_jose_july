PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: setup lint test emulators api worker send-test-event run-demo

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m mypy app

test:
	$(PYTHON) -m pytest

emulators:
	bash scripts/bootstrap_emulators.sh

api:
	$(PYTHON) -m uvicorn app.api.main:app --reload --port 8000

worker:
	$(PYTHON) -m app.worker.main

send-test-event:
	cp samples/synthetic_retail_ai_transcript.txt local_storage/intake/synthetic_retail_ai_transcript.txt
	$(PYTHON) scripts/send_fake_drive_event.py

run-demo:
	$(PYTHON) scripts/run_local_pipeline.py

