from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class QueueMessage:
    job_id: str
    ack_id: str | None = None


class JobQueue(Protocol):
    def publish_job(self, job_id: str) -> None: ...

    def pull_one(self) -> QueueMessage | None: ...

    def ack(self, message: QueueMessage) -> None: ...


class LocalFileJobQueue:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def publish_job(self, job_id: str) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps({"job_id": job_id}) + "\n")

    def pull_one(self) -> QueueMessage | None:
        import fcntl

        self.path.touch(exist_ok=True)
        with self.path.open("r+", encoding="utf-8") as file:
            fcntl.flock(file.fileno(), fcntl.LOCK_EX)
            try:
                lines = file.readlines()
                if not lines:
                    return None
                first, rest = lines[0], lines[1:]
                file.seek(0)
                file.truncate()
                file.writelines(rest)
                payload = json.loads(first)
                return QueueMessage(job_id=payload["job_id"])
            finally:
                fcntl.flock(file.fileno(), fcntl.LOCK_UN)

    def ack(self, message: QueueMessage) -> None:
        return None


class PubSubJobQueue:
    def __init__(self, project: str, topic: str, subscription: str):
        from google.cloud import pubsub_v1  # type: ignore[attr-defined]

        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
        self.topic_path = self.publisher.topic_path(project, topic)
        self.subscription_path = self.subscriber.subscription_path(project, subscription)

    def publish_job(self, job_id: str) -> None:
        payload = json.dumps({"job_id": job_id}).encode("utf-8")
        self.publisher.publish(self.topic_path, payload).result(timeout=30)

    def pull_one(self) -> QueueMessage | None:
        response = self.subscriber.pull(
            request={"subscription": self.subscription_path, "max_messages": 1},
            timeout=5,
        )
        if not response.received_messages:
            return None
        received = response.received_messages[0]
        payload = json.loads(received.message.data.decode("utf-8"))
        return QueueMessage(job_id=payload["job_id"], ack_id=received.ack_id)

    def ack(self, message: QueueMessage) -> None:
        if message.ack_id:
            self.subscriber.acknowledge(
                request={"subscription": self.subscription_path, "ack_ids": [message.ack_id]}
            )
