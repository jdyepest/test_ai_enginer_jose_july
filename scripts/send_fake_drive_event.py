from __future__ import annotations

import argparse
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send a local fake Drive event to the FastAPI service."
    )
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--path",
        default="local_storage/intake/synthetic_retail_ai_transcript.txt",
        help="Local intake file path.",
    )
    args = parser.parse_args()

    path = Path(args.path)
    payload = {
        "source_type": "local",
        "file_id": path.stem,
        "file_name": path.name,
        "file_version": "1",
        "mime_type": "text/plain",
        "local_path": str(path),
    }
    response = httpx.post(f"{args.api_url.rstrip('/')}/events/drive", json=payload, timeout=30)
    response.raise_for_status()
    print(response.text)


if __name__ == "__main__":
    main()
