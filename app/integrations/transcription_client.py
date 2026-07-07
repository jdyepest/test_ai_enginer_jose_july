from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path
from typing import Protocol


class TranscriptionClient(Protocol):
    def transcribe(self, path: Path) -> str: ...


class FakeTranscriptionClient:
    def transcribe(self, path: Path) -> str:
        return (
            f"[00:00] Unknown: Audio transcription was requested for {path.name}. "
            "Configure a real transcription provider to process recorded meetings."
        )


class OpenAiTranscriptionClient:
    def __init__(self, api_key: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key)

    def transcribe(self, path: Path) -> str:
        audio_path = path
        with tempfile.TemporaryDirectory() as tmpdir:
            if path.suffix.lower() == ".mp4":
                audio_path = Path(tmpdir) / "audio.wav"
                subprocess.run(
                    ["ffmpeg", "-y", "-i", str(path), "-vn", str(audio_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            with audio_path.open("rb") as file:
                result = self.client.audio.transcriptions.create(model="whisper-1", file=file)
            return result.text

