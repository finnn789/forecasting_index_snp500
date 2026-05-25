from __future__ import annotations
from pathlib import Path
from app.core.exceptions import NotFoundError


class FileBasedRepository:
    """Base class untuk repository yang backed by filesystem."""

    def __init__(self, raw_dir: Path | str | None = None,
                 processed_dir: Path | str | None = None):
        self.raw_dir = Path(raw_dir) if raw_dir is not None else None
        self.processed_dir = Path(processed_dir) if processed_dir is not None else None

    def _resolve(self, base: Path | None, *parts: str) -> Path:
        if base is None:
            raise NotFoundError("repository base path not configured", code="REPO_NOT_CONFIGURED")
        return base.joinpath(*parts)

    def _ensure_exists(self, path: Path) -> Path:
        if not path.exists():
            raise NotFoundError(
                f"file not found: {path}",
                code="FILE_NOT_FOUND",
                detail=str(path),
            )
        return path
