"""Tests untuk StockRepository menggunakan tmp_path fixture."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from app.core.exceptions import NotFoundError
from app.domain.value_objects import DateRange, TickerSymbol
from app.repositories.stock_repository import StockRepository


def _make_ohlcv_csv(path: Path, rows: list[dict]) -> None:
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)


@pytest.fixture()
def gspc_raw(tmp_path: Path) -> Path:
    csv_path = tmp_path / "GSPC_2018_2024.csv"
    _make_ohlcv_csv(csv_path, [
        {"Date": "2020-01-02", "Open": 3230.0, "High": 3250.0, "Low": 3220.0, "Close": 3244.0, "Volume": 1_000_000},
        {"Date": "2020-06-15", "Open": 3100.0, "High": 3120.0, "Low": 3090.0, "Close": 3113.0, "Volume": 900_000},
        {"Date": "2023-03-10", "Open": 4000.0, "High": 4020.0, "Low": 3990.0, "Close": 4010.0, "Volume": 1_200_000},
    ])
    return tmp_path


@pytest.fixture()
def repo(gspc_raw: Path) -> StockRepository:
    return StockRepository(raw_dir=gspc_raw, processed_dir=gspc_raw)


class TestStockRepository:
    def test_load_raw_returns_all_rows(self, repo: StockRepository):
        ticker = TickerSymbol(symbol="GSPC")
        df = repo.load_raw(ticker)
        assert len(df) == 3

    def test_load_raw_with_date_range_filters(self, repo: StockRepository):
        ticker = TickerSymbol(symbol="GSPC")
        dr = DateRange(start=date(2020, 1, 1), end=date(2021, 1, 1))
        df = repo.load_raw(ticker, date_range=dr)
        assert len(df) == 2  # 2020-01-02 dan 2020-06-15

    def test_load_raw_date_range_no_match(self, repo: StockRepository):
        ticker = TickerSymbol(symbol="GSPC")
        dr = DateRange(start=date(2015, 1, 1), end=date(2016, 1, 1))
        df = repo.load_raw(ticker, date_range=dr)
        assert len(df) == 0

    def test_load_raw_file_not_found(self, tmp_path: Path):
        repo = StockRepository(raw_dir=tmp_path / "empty", processed_dir=tmp_path)
        ticker = TickerSymbol(symbol="AAPL")
        with pytest.raises(NotFoundError):
            repo.load_raw(ticker)

    def test_save_and_load_processed(self, repo: StockRepository, tmp_path: Path):
        ticker = TickerSymbol(symbol="GSPC")
        df_in = repo.load_raw(ticker)
        saved_path = repo.save_processed(ticker, df_in)
        assert saved_path.exists()

        df_out = repo.load_processed(ticker)
        assert len(df_out) == len(df_in)

    def test_exists_processed_false(self, repo: StockRepository):
        ticker = TickerSymbol(symbol="AAPL")
        assert repo.exists_processed(ticker) is False

    def test_exists_processed_true(self, repo: StockRepository):
        ticker = TickerSymbol(symbol="GSPC")
        df = repo.load_raw(ticker)
        repo.save_processed(ticker, df)
        assert repo.exists_processed(ticker) is True

    def test_load_processed_not_found(self, tmp_path: Path):
        repo = StockRepository(raw_dir=tmp_path, processed_dir=tmp_path / "proc")
        ticker = TickerSymbol(symbol="GSPC")
        with pytest.raises(NotFoundError):
            repo.load_processed(ticker)
