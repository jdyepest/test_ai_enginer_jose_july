from __future__ import annotations

import logging
from pathlib import Path

from app.models.meeting_summary import MeetingSummary
from app.utils.logging import log_event
from app.utils.timestamps import yyyymmdd

logger = logging.getLogger(__name__)


class PresentationService:
    def create_deck(
        self,
        summary: MeetingSummary,
        output_path: Path,
        prompt_version: str,
        job_id: str,
    ) -> Path:
        from pptx import Presentation
        from pptx.enum.text import PP_ALIGN
        from pptx.util import Inches, Pt

        prs = Presentation()

        def add_footer(slide) -> None:
            box = slide.shapes.add_textbox(Inches(0.45), Inches(7.05), Inches(12.4), Inches(0.22))
            frame = box.text_frame
            frame.text = f"Generated {yyyymmdd()} | Prompt {prompt_version} | Human review required"
            p = frame.paragraphs[0]
            p.alignment = PP_ALIGN.RIGHT
            p.font.size = Pt(8)

        def add_title(slide, title: str) -> None:
            box = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12.0), Inches(0.6))
            frame = box.text_frame
            frame.text = title
            frame.paragraphs[0].font.size = Pt(28)
            frame.paragraphs[0].font.bold = True

        def add_bullets(
            slide,
            left: float,
            top: float,
            width: float,
            height: float,
            items: list[str],
        ) -> None:
            box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
            frame = box.text_frame
            frame.word_wrap = True
            frame.clear()
            for index, item in enumerate(items):
                paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
                paragraph.text = item
                paragraph.level = 0
                paragraph.font.size = Pt(16)

        blank = prs.slide_layouts[6]

        slide = prs.slides.add_slide(blank)
        add_title(slide, summary.meeting_title)
        subtitle = summary.company or "Meeting Intelligence"
        add_bullets(
            slide,
            0.75,
            1.25,
            11.5,
            4.8,
            [subtitle, f"Executive summary: {summary.executive_summary}"],
        )
        add_footer(slide)

        slide = prs.slides.add_slide(blank)
        add_title(slide, "Objectives")
        add_bullets(slide, 0.75, 1.25, 11.5, 4.8, [item.objective for item in summary.objectives])
        add_footer(slide)

        slide = prs.slides.add_slide(blank)
        add_title(slide, "Action Items")
        action_text = [
            (
                f"{item.action} | Owner: {item.owner or 'Unknown'} | "
                f"Priority: {item.priority} | Rationale: {item.business_rationale}"
            )
            for item in summary.action_items
        ]
        add_bullets(slide, 0.75, 1.15, 11.7, 5.4, action_text)
        add_footer(slide)

        slide = prs.slides.add_slide(blank)
        add_title(slide, "Next Steps and Review")
        steps = [
            (
                f"{item.step} | Owner: {item.owner or 'Unknown'} | "
                f"Timeframe: {item.timeframe or 'Unknown'}"
            )
            for item in summary.next_steps
        ]
        steps.append("Reviewer confirms accuracy, evidence, and distribution readiness.")
        add_bullets(slide, 0.75, 1.25, 11.5, 4.8, steps)
        add_footer(slide)

        slide = prs.slides.add_slide(blank)
        add_title(slide, "Audit Evidence and Risks")
        evidence = []
        for objective in summary.objectives:
            first = objective.evidence[0]
            prefix = f"{first.timestamp} " if first.timestamp else ""
            speaker = f"{first.speaker}: " if first.speaker else ""
            evidence.append(f"{objective.objective}: {prefix}{speaker}{first.source_text}")
        evidence.extend([f"Risk: {risk}" for risk in summary.risks_and_uncertainties])
        add_bullets(slide, 0.75, 1.1, 11.7, 5.7, evidence)
        add_footer(slide)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))
        log_event(logger, "PRESENTATION_CREATED", job_id=job_id, deck_path=str(output_path))
        return output_path
