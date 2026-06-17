import logging
import math
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import pandas as pd
from transformers import AutoModelForSequenceClassification, BertTokenizer, pipeline

logger = logging.getLogger(__name__)

SENTIMENT_NUMERIC: dict[str, int] = {"positive": 1, "neutral": 0, "negative": -1}


def _resolve_snapshot_path(model_path: str) -> str:
    """
    Resolve a HuggingFace cache directory (models--org--name format) to its
    latest snapshot subdirectory. Returns the path unchanged if it is already
    a direct model directory (contains config.json or vocab.txt at top level).
    """
    p = Path(model_path)
    snapshots_dir = p / "snapshots"
    if snapshots_dir.is_dir():
        candidates = sorted(snapshots_dir.iterdir())
        if candidates:
            resolved = str(candidates[-1])
            logger.info("Resolved HF cache path %s -> %s", model_path, resolved)
            return resolved
    return model_path


class TextPreprocessor:
    def __init__(
        self,
        model_path: str,
        batch_size: int = 32,
        device: int = -1,
    ) -> None:
        """
        model_path: path to local FinBERT snapshot directory (or HF cache dir).
        device: -1 for CPU, 0+ for GPU index.
        """
        self._model_path = _resolve_snapshot_path(model_path)
        self._batch_size = batch_size
        self._device = device
        self._pipeline: Optional[object] = None

    def _load_pipeline(self):
        if self._pipeline is None:
            logger.info("Loading FinBERT model from %s", self._model_path)
            # BertTokenizer (slow) used directly — avoids AutoTokenizer fast-conversion
            # which requires tokenizer.json or sentencepiece when absent from snapshot.
            tokenizer = BertTokenizer.from_pretrained(self._model_path)
            model = AutoModelForSequenceClassification.from_pretrained(self._model_path)
            self._pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                device=self._device,
                truncation=True,
                max_length=512,
            )
        return self._pipeline

    def drop_cp_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove the CP column from the dataframe if present."""
        if "CP" in df.columns:
            df = df.drop(columns=["CP"])
            logger.info("Dropped CP column")
        return df

    def extract_sentiment_scores(
        self,
        df: pd.DataFrame,
        text_column: str = "Title",
        on_batch: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """
        Run FinBERT inference on text_column.
        Adds columns: sentiment_label, sentiment_score, sentiment_numeric.

        on_batch(batch_num, total_batches, processed_so_far) — called after each batch.
        """
        pipe = self._load_pipeline()
        texts = df[text_column].fillna("").tolist()
        total_batches = max(1, math.ceil(len(texts) / self._batch_size))

        results: list = []
        for batch_idx in range(0, len(texts), self._batch_size):
            batch = texts[batch_idx : batch_idx + self._batch_size]
            batch_results = pipe(batch, batch_size=len(batch))
            results.extend(batch_results)
            if on_batch:
                batch_num = batch_idx // self._batch_size + 1
                on_batch(batch_num, total_batches, len(results))

        df = df.copy()
        df["sentiment_label"] = [r["label"].lower() for r in results]
        df["sentiment_score"] = [round(r["score"], 6) for r in results]
        df["sentiment_numeric"] = (
            df["sentiment_label"].map(SENTIMENT_NUMERIC).fillna(0).astype(int)
        )

        logger.info("Extracted sentiment scores for %d records", len(df))
        return df

    def process(
        self,
        df: pd.DataFrame,
        text_column: str = "Title",
        on_batch: Callable[[int, int, int], None] | None = None,
    ) -> pd.DataFrame:
        """Full preprocessing pipeline: drop CP column then extract sentiment scores."""
        df = self.drop_cp_column(df)
        df = self.extract_sentiment_scores(df, text_column=text_column, on_batch=on_batch)
        return df

    def export_to_file(
        self, df: pd.DataFrame, output_path: str, fmt: str = "csv"
    ) -> str:
        """Export DataFrame to CSV or Excel file.

        fmt: 'csv' → .csv, 'excel' → .xlsx
        Returns output_path.
        """
        if fmt == "excel":
            df.to_excel(output_path, index=False)
        else:
            df.to_csv(output_path, index=False)

        logger.info("Exported %d records to %s (format=%s)", len(df), output_path, fmt)
        return output_path
