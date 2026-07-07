from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class JobPaths:
    archive_dir: Path
    review_dir: Path
    failed_dir: Path


class LocalStorageClient:
    def __init__(self, root: Path):
        self.root = root
        for name in ("intake", "archive", "needs_review", "failed"):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def paths_for_job(self, job_id: str) -> JobPaths:
        paths = JobPaths(
            archive_dir=self.root / "archive" / job_id,
            review_dir=self.root / "needs_review" / job_id,
            failed_dir=self.root / "failed" / job_id,
        )
        paths.archive_dir.mkdir(parents=True, exist_ok=True)
        paths.review_dir.mkdir(parents=True, exist_ok=True)
        paths.failed_dir.mkdir(parents=True, exist_ok=True)
        return paths

    def archive_original(self, source_path: Path, archive_dir: Path) -> Path:
        target = archive_dir / "original_input"
        if source_path.is_file():
            shutil.copy2(source_path, target)
        else:
            target.write_text(f"Source path not found: {source_path}\n", encoding="utf-8")
        return target


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return slug or "meeting"

