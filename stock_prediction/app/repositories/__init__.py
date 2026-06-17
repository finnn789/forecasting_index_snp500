from __future__ import annotations
from pathlib import Path
from .base import FileBasedRepository
from .news_repository import NewsRepository
from .sentiment_repository import SentimentRepository
from .stock_repository import StockRepository
from .artifact_repository import ArtifactRepository

# Lazy imports: repos konkret dibuat di Wave 2. Factory pakai lazy import.
from typing import TypedDict

class Repositories(TypedDict):
    stock: StockRepository
    news: NewsRepository
    sentiment: SentimentRepository
    artifact: ArtifactRepository

def get_default_repositories() -> dict:
    """Factory: return dict of configured repositories.

    Lazy import supaya module ini bisa di-load meski repo konkret belum ada.
    """
    from app.core.settings import settings

    base = Path(".")
    return {
        "stock": StockRepository(
            raw_dir=base / "data/raw/stocks",
            processed_dir=base / "data/processed/stocks",
        ),
        "news": NewsRepository(
            raw_dir=base / "data/raw/news",
            processed_dir=base / "data/processed/sentiment",
        ),
        "sentiment": SentimentRepository(
            raw_dir=base / "data/raw/news",
            processed_dir=base / "data/processed/sentiment",
        ),
        "artifact": ArtifactRepository(
            lstm_dir=base / settings.lstm_model_path,
            finbert_dir=base / settings.finbert_local_path,
        ),
    }


__all__ = [
    "FileBasedRepository",
    "NewsRepository",
    "SentimentRepository",
    "StockRepository",
    "ArtifactRepository",
    "get_default_repositories",
]
