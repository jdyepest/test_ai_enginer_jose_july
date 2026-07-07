from __future__ import annotations

import json
from typing import Protocol

from app.models.meeting_summary import MeetingSummary


class LlmClient(Protocol):
    model_name: str

    def summarize(self, transcript: str, prompt_version: str) -> MeetingSummary: ...


class FakeLlmClient:
    model_name = "fake-local-summary"

    def summarize(self, transcript: str, prompt_version: str) -> MeetingSummary:
        lines = [line.strip() for line in transcript.splitlines() if line.strip()]
        evidence = _first_evidence(lines)
        text_lower = transcript.lower()
        company = "BrightLane Retail" if "brightlane" in text_lower else None
        return MeetingSummary.model_validate(
            {
                "meeting_title": "Meeting Intelligence Pilot Review",
                "meeting_date": None,
                "company": company,
                "executive_summary": (
                    "The team discussed using meeting intelligence to turn leadership "
                    "conversations into review-ready materials while keeping people in the "
                    "approval loop. The pilot should focus on measurable time savings, better "
                    "operational prioritization, and traceable recommendations."
                ),
                "objectives": [
                    {
                        "objective": (
                            "Reduce manual effort spent converting meetings into "
                            "leadership materials."
                        ),
                        "evidence": [evidence[0]],
                    },
                    {
                        "objective": (
                            "Improve prioritization by grounding operational insights "
                            "in source evidence."
                        ),
                        "evidence": [evidence[1]],
                    },
                    {
                        "objective": (
                            "Pilot meeting intelligence before expanding into "
                            "customer-facing automation."
                        ),
                        "evidence": [evidence[2]],
                    },
                ],
                "action_items": [
                    {
                        "action": (
                            "Run a pilot using recent leadership and operations "
                            "meeting transcripts."
                        ),
                        "owner": None,
                        "due_date": None,
                        "priority": "high",
                        "business_rationale": (
                            "Historical meetings can validate summary quality and review effort "
                            "before production use."
                        ),
                        "evidence": [evidence[0]],
                    },
                    {
                        "action": (
                            "Define review criteria for accuracy, evidence quality, cost, and time "
                            "savings."
                        ),
                        "owner": None,
                        "due_date": None,
                        "priority": "high",
                        "business_rationale": (
                            "The pilot needs measurable acceptance criteria before broader "
                            "distribution."
                        ),
                        "evidence": [evidence[1]],
                    },
                    {
                        "action": (
                            "Keep human approval mandatory before any generated material is shared."
                        ),
                        "owner": None,
                        "due_date": None,
                        "priority": "medium",
                        "business_rationale": (
                            "Human review controls risk when recommendations are generated from "
                            "imperfect transcripts."
                        ),
                        "evidence": [evidence[2]],
                    },
                ],
                "next_steps": [
                    {
                        "step": "Collect candidate meeting transcripts for the pilot batch.",
                        "owner": None,
                        "timeframe": "Pilot setup",
                    },
                    {
                        "step": (
                            "Review generated summaries and decks with leadership stakeholders."
                        ),
                        "owner": None,
                        "timeframe": "After each pilot run",
                    },
                    {
                        "step": (
                            "Compare manual prep time against automated output and revision time."
                        ),
                        "owner": None,
                        "timeframe": "Pilot closeout",
                    },
                ],
                "risks_and_uncertainties": [
                    "Transcript quality may limit the accuracy of extracted decisions and owners.",
                    (
                        "Owners and due dates should remain null unless stated clearly in the "
                        "source meeting."
                    ),
                    "Broader automation should wait until reviewers trust the evidence trail.",
                ],
            }
        )


class OpenAiLlmClient:
    def __init__(self, api_key: str, model_name: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name

    def summarize(self, transcript: str, prompt_version: str) -> MeetingSummary:
        instructions = f"""
Use only information supported by the transcript.
Avoid inventing names, deadlines, data, or commitments.
Mark unknown owners and due dates as null.
Generate exactly three objectives and exactly three action items.
Make actions specific and business-oriented.
Include evidence for all major recommendations.
Distinguish confirmed decisions from suggested next steps.
Mention uncertainty when evidence is incomplete.
Every evidence value must be an array of objects with timestamp, speaker, and source_text.
Do not use alternate keys such as action_item, rationale, or evidence_text.
Prompt version: {prompt_version}
"""
        prompt = f"""
Analyze this meeting transcript and return a structured meeting summary.

Transcript:
{transcript}
"""
        response = self.client.responses.create(
            model=self.model_name,
            instructions=instructions,
            input=prompt,
            temperature=0.2,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "meeting_summary",
                    "schema": MeetingSummary.model_json_schema(),
                    "strict": False,
                }
            },
        )
        return MeetingSummary.model_validate(json.loads(response.output_text))


def _first_evidence(lines: list[str]) -> list[dict[str, str | None]]:
    fallback = lines or ["Transcript content was provided for analysis."]
    selected = (fallback + fallback + fallback)[:3]
    return [
        {"timestamp": None, "speaker": None, "source_text": selected[0][:400]},
        {"timestamp": None, "speaker": None, "source_text": selected[1][:400]},
        {"timestamp": None, "speaker": None, "source_text": selected[2][:400]},
    ]
