from __future__ import annotations

import logging

from app.integrations.llm_client import FakeLlmClient, LlmClient, OpenAiLlmClient
from app.models.meeting_summary import MeetingSummary
from app.utils.logging import log_event

logger = logging.getLogger(__name__)


class SummarizationService:
    def __init__(self, client: LlmClient, prompt_version: str):
        self.client = client
        self.prompt_version = prompt_version

    @property
    def model_name(self) -> str:
        return self.client.model_name

    def summarize(self, transcript: str, job_id: str) -> MeetingSummary:
        log_event(logger, "LLM_REQUEST_STARTED", job_id=job_id, model_name=self.model_name)
        summary = self.client.summarize(transcript, self.prompt_version)
        log_event(logger, "LLM_RESPONSE_VALIDATED", job_id=job_id, model_name=self.model_name)
        return summary


def build_llm_client(provider: str, api_key: str, model_name: str) -> LlmClient:
    if provider == "openai":
        return OpenAiLlmClient(api_key=api_key, model_name=model_name)
    return FakeLlmClient()

