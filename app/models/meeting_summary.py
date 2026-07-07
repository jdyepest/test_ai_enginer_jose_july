from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Evidence(BaseModel):
    timestamp: str | None = None
    speaker: str | None = None
    source_text: str = Field(min_length=1)


class Objective(BaseModel):
    objective: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class ActionItem(BaseModel):
    action: str = Field(min_length=1)
    owner: str | None = None
    due_date: str | None = None
    priority: Literal["high", "medium", "low"]
    business_rationale: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class NextStep(BaseModel):
    step: str = Field(min_length=1)
    owner: str | None = None
    timeframe: str | None = None


class MeetingSummary(BaseModel):
    meeting_title: str = Field(min_length=1)
    meeting_date: str | None = None
    company: str | None = None
    executive_summary: str = Field(min_length=1)
    objectives: list[Objective]
    action_items: list[ActionItem]
    next_steps: list[NextStep]
    risks_and_uncertainties: list[str]

    @field_validator("objectives")
    @classmethod
    def require_three_objectives(cls, value: list[Objective]) -> list[Objective]:
        if len(value) != 3:
            raise ValueError("summary must contain exactly three objectives")
        return value

    @field_validator("action_items")
    @classmethod
    def require_three_action_items(cls, value: list[ActionItem]) -> list[ActionItem]:
        if len(value) != 3:
            raise ValueError("summary must contain exactly three action items")
        return value

