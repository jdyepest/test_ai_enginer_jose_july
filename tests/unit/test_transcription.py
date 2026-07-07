from __future__ import annotations

from app.services.transcription_service import normalize_transcript


def test_transcript_normalization_removes_empty_lines_and_repeated_headers() -> None:
    transcript = "\nMeeting Transcript\n\n[00:00] Maya: Hello\nMeeting Transcript\n\n"

    assert normalize_transcript(transcript) == "Meeting Transcript\n[00:00] Maya: Hello\n"

