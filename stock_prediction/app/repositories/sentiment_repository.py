from pathlib import Path

import pandas as pd

from app.core.exceptions import NotFoundError
from app.domain.value_objects import DateRange
from .base import FileBasedRepository

_DAILY_SENTIMENT_FILENAME = "headlines_daily_sentiment.csv"
_DAILY_COUNT_FILENAME = "headlines_daily_count.csv"


class SentimentRepository(FileBasedRepository):
    def __init__(self, raw_dir: Path, processed_dir: Path) -> None:
        super().__init__(raw_dir)
        self._processed_dir = Path(processed_dir)

    def load_daily_sentiment(self, date_range: DateRange | None = None) -> pd.DataFrame:
        path = self._processed_dir / _DAILY_SENTIMENT_FILENAME
        if not path.exists():
            raise NotFoundError(
                f"File sentimen harian tidak ditemukan: {path}. Jalankan pipeline.",
                code="SENTIMENT_DATA_NOT_FOUND",
            )
        df = pd.read_csv(path, parse_dates=["Date"])
        if date_range is not None:
            start, end = date_range.to_pandas_query()
            df = df[(df["Date"] >= start) & (df["Date"] <= end)]
        return df.reset_index(drop=True)

    def save_daily_sentiment(self, df: pd.DataFrame) -> Path:
        self._processed_dir.mkdir(parents=True, exist_ok=True)
        path = self._processed_dir / _DAILY_SENTIMENT_FILENAME
        df.to_csv(path, index=False)
        return path

    def load_daily_count(self) -> pd.DataFrame:
        path = self._processed_dir / _DAILY_COUNT_FILENAME
        if not path.exists():
            raise NotFoundError(
                f"File daily count tidak ditemukan: {path}.",
                code="COUNT_DATA_NOT_FOUND",
            )
        return pd.read_csv(path, parse_dates=["Date"])

    def save_daily_count(self, df: pd.DataFrame) -> Path:
        self._processed_dir.mkdir(parents=True, exist_ok=True)
        path = self._processed_dir / _DAILY_COUNT_FILENAME
        df.to_csv(path, index=False)
        return path
