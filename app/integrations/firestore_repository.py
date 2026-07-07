from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Protocol

from app.models.jobs import JobRecord, JobStatus
from app.utils.timestamps import utc_now_iso


class JobRepository(Protocol):
    def get(self, job_id: str) -> JobRecord | None: ...

    def save(self, job: JobRecord) -> None: ...

    def claim(self, job_id: str) -> JobRecord | None: ...

    def update(self, job_id: str, **changes: object) -> JobRecord: ...


class LocalJsonJobRepository:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _locked_data(self) -> Iterator[dict[str, dict[str, object]]]:
        import fcntl

        self.path.touch(exist_ok=True)
        with self.path.open("r+", encoding="utf-8") as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX)
            try:
                file.seek(0)
                raw = file.read().strip()
                data: dict[str, dict[str, object]] = json.loads(raw) if raw else {}
                yield data
                file.seek(0)
                file.truncate()
                json.dump(data, file, indent=2, sort_keys=True)
            finally:
                fcntl.flock(file.fileno(), fcntl.LOCK_UN)

    def get(self, job_id: str) -> JobRecord | None:
        if not self.path.exists():
            return None
        raw = json.loads(self.path.read_text(encoding="utf-8") or "{}")
        record = raw.get(job_id)
        return JobRecord.model_validate(record) if record else None

    def save(self, job: JobRecord) -> None:
        with self._locked_data() as data:
            data[job.job_id] = job.model_dump(mode="json")

    def claim(self, job_id: str) -> JobRecord | None:
        with self._locked_data() as data:
            record = data.get(job_id)
            if not record:
                return None
            job = JobRecord.model_validate(record)
            if job.status != JobStatus.QUEUED:
                return None
            job.status = JobStatus.PROCESSING
            job.started_at = utc_now_iso()
            job.attempt_count += 1
            job.audit_events.append({"event": "JOB_PROCESSING_STARTED", "timestamp": utc_now_iso()})
            data[job_id] = job.model_dump(mode="json")
            return job

    def update(self, job_id: str, **changes: object) -> JobRecord:
        with self._locked_data() as data:
            record = data.get(job_id)
            if not record:
                raise KeyError(f"job not found: {job_id}")
            job_data = {**record, **changes}
            job = JobRecord.model_validate(job_data)
            data[job_id] = job.model_dump(mode="json")
            return job


class FirestoreJobRepository:
    def __init__(self, project: str, collection_name: str = "meeting_jobs"):
        from google.cloud import firestore

        self.client = firestore.Client(project=project)
        self.collection = self.client.collection(collection_name)

    def get(self, job_id: str) -> JobRecord | None:
        snapshot = self.collection.document(job_id).get()
        return JobRecord.model_validate(snapshot.to_dict()) if snapshot.exists else None

    def save(self, job: JobRecord) -> None:
        self.collection.document(job.job_id).set(job.model_dump(mode="json"))

    def claim(self, job_id: str) -> JobRecord | None:
        from google.cloud import firestore

        document = self.collection.document(job_id)
        transaction = self.client.transaction()

        @firestore.transactional
        def _claim(transaction: Any) -> JobRecord | None:
            snapshot = document.get(transaction=transaction)
            if not snapshot.exists:
                return None
            job = JobRecord.model_validate(snapshot.to_dict())
            if job.status != JobStatus.QUEUED:
                return None
            job.status = JobStatus.PROCESSING
            job.started_at = utc_now_iso()
            job.attempt_count += 1
            job.audit_events.append({"event": "JOB_PROCESSING_STARTED", "timestamp": utc_now_iso()})
            transaction.set(document, job.model_dump(mode="json"))
            return job

        return _claim(transaction)

    def update(self, job_id: str, **changes: object) -> JobRecord:
        document = self.collection.document(job_id)
        document.update(changes)
        updated = document.get()
        if not updated.exists:
            raise KeyError(f"job not found: {job_id}")
        return JobRecord.model_validate(updated.to_dict())
