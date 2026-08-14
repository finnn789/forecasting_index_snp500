from pathlib import Path

import pandas as pd

from app.core.exceptions import NotFoundError
from app.domain.value_objects import DateRange
from .base import FileBasedRepository

_CLEAN_FILENAME = "headlines_clean.csv"


class NewsRepository(FileBasedRepository):
    def __init__(self, raw_dir: Path, processed_dir: Path, date_suffix: str = "2018_2024") -> None:
        super().__init__(raw_dir)
        self._raw_dir = Path(raw_dir)
        self._processed_dir = Path(processed_dir)
        self._raw_filename = f"sp500_headlines_{date_suffix}.csv"

    def raw_headlines_path(self) -> Path:
        return self._raw_dir / self._raw_filename

    def clean_headlines_path(self) -> Path:
        return self._processed_dir / _CLEAN_FILENAME

    def load_raw_headlines(self, date_range: DateRange | None = None) -> pd.DataFrame:
        path = self._raw_dir / self._raw_filename
        if not path.exists():
            raise NotFoundError(
                f"File headlines mentah tidak ditemukan: {path}",
                code="NEWS_DATA_NOT_FOUND",
            )
        df = pd.read_csv(path, parse_dates=["Date"])
        if "CP" in df.columns:
            df = df.drop(columns=["CP"])
        if date_range is not None:
            start, end = date_range.to_pandas_query()
            df = df[(df["Date"] >= start) & (df["Date"] <= end)]
        return df.reset_index(drop=True)

    def load_clean_headlines(self) -> pd.DataFrame:
        path = self._processed_dir / _CLEAN_FILENAME
        if not path.exists():
            raise NotFoundError(
                f"File headlines bersih tidak ditemukan: {path}. Jalankan pipeline preprocessing.",
                code="CLEAN_DATA_NOT_FOUND",
            )
        return pd.read_csv(path, parse_dates=["Date"])

    def save_clean_headlines(self, df: pd.DataFrame) -> Path:
        self._processed_dir.mkdir(parents=True, exist_ok=True)
        path = self._processed_dir / _CLEAN_FILENAME
        df.to_csv(path, index=False)
        return path
