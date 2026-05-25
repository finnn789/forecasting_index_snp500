from pathlib import Path

import pandas as pd

from app.core.exceptions import NotFoundError
from app.domain.value_objects import DateRange, TickerSymbol
from .base import FileBasedRepository


class StockRepository(FileBasedRepository):
    def __init__(self, raw_dir: Path, processed_dir: Path) -> None:
        super().__init__(raw_dir)
        self._raw_dir = Path(raw_dir)
        self._processed_dir = Path(processed_dir)

    def _raw_path(self, ticker: TickerSymbol) -> Path:
        sym = ticker.symbol
        candidate = self._raw_dir / f"{sym}_2018_2024.csv"
        if not candidate.exists():
            candidate = self._raw_dir / f"GSPC_2018_2024.csv"
        return candidate

    def load_raw(
        self,
        ticker: TickerSymbol,
        date_range: DateRange | None = None,
    ) -> pd.DataFrame:
        path = self._raw_path(ticker)
        if not path.exists():
            raise NotFoundError(
                f"Data saham mentah tidak ditemukan: {path}",
                code="STOCK_DATA_NOT_FOUND",
            )
        df = pd.read_csv(path, parse_dates=["Date"])
        if date_range is not None:
            start, end = date_range.to_pandas_query()
            df = df[(df["Date"] >= start) & (df["Date"] <= end)]
        return df.reset_index(drop=True)

    def load_processed(
        self,
        ticker: TickerSymbol,
        date_range: DateRange | None = None,
    ) -> pd.DataFrame:
        path = self._processed_dir / f"{ticker.symbol}_2018_2024.csv"
        if not path.exists():
            raise NotFoundError(
                f"Data saham processed tidak ditemukan: {path}",
                code="STOCK_DATA_NOT_FOUND",
            )
        df = pd.read_csv(path, parse_dates=["Date"])
        if date_range is not None:
            start, end = date_range.to_pandas_query()
            df = df[(df["Date"] >= start) & (df["Date"] <= end)]
        return df.reset_index(drop=True)

    def save_processed(self, ticker: TickerSymbol, df: pd.DataFrame) -> Path:
        self._processed_dir.mkdir(parents=True, exist_ok=True)
        path = self._processed_dir / f"{ticker.symbol}_2018_2024.csv"
        df.to_csv(path, index=False)
        return path

    def exists_processed(self, ticker: TickerSymbol) -> bool:
        return (self._processed_dir / f"{ticker.symbol}_2018_2024.csv").exists()
