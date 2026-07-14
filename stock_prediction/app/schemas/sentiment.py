"""
app/schemas/sentiment.py — Pydantic schemas untuk endpoint sentiment pipeline.
"""

from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sentiment Pipeline
# ---------------------------------------------------------------------------

class PreviewResponse(BaseModel):
    """N baris pertama / halaman dari sebuah file CSV hasil sentiment pipeline."""
    source: str
    filename: str
    total_rows: int
    columns: list[str]
    rows: list[dict[str, Any]] = Field(description="Baris data dalam format list-of-dict")


class PipelineStatusResponse(BaseModel):
    clean_file_exists: bool
    daily_file_exists: bool
    total_headlines: int | None
    total_days: int | None
    date_range: dict[str, str | None]


class ModelStatusResponse(BaseModel):
    is_available: bool
    model_path: str
    source: str                          # "local_snapshot" | "local_dir" | "huggingface_hub"
    snapshot_path: str | None            # path snapshot aktif (jika HF cache format)
    required_files: dict[str, bool]      # config.json, pytorch_model.bin, tokenizer_config.json, vocab.txt
    model_size_mb: float | None          # total ukuran file di snapshot dir
