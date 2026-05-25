"""Tests untuk SentimentRepository menggunakan tmp_path fixture."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from app.core.exceptions import NotFoundError
from app.domain.value_objects import DateRange
from app.repositories.sentiment_repository import SentimentRepository


def _make_sentiment_csv(path: Path, rows: list[dict]) -> None:
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)


@pytest.fixture()
def processed_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def repo_with_data(processed_dir: Path) -> SentimentRepository:
    csv_path = processed_dir / "headlines_daily_sentiment.csv"
    _make_sentiment_csv(csv_path, [
        {"Date": "2020-01-02", "sentiment_mean": 0.2, "headline_count": 10},
        {"Date": "2021-05-15", "sentiment_mean": -0.1, "headline_count": 5},
        {"Date": "2023-08-20", "sentiment_mean": 0.5, "headline_count": 20},
    ])
    return SentimentRepository(raw_dir=processed_dir, processed_dir=processed_dir)


class TestSentimentRepository:
    def test_load_daily_sentiment_all_rows(self, repo_with_data: SentimentRepository):
        df = repo_with_data.load_daily_sentiment()
        assert len(df) == 3

    def test_load_daily_sentiment_with_date_range(self, repo_with_data: SentimentRepository):
        dr = DateRange(start=date(2020, 1, 1), end=date(2021, 12, 31))
        df = repo_with_data.load_daily_sentiment(date_range=dr)
        assert len(df) == 2

    def test_load_daily_sentiment_not_found(self, tmp_path: Path):
        repo = SentimentRepository(raw_dir=tmp_path, processed_dir=tmp_path / "empty")
        with pytest.raises(NotFoundError):
            repo.load_daily_sentiment()

    def test_save_and_reload_daily_sentiment(self, processed_dir: Path):
        repo = SentimentRepository(raw_dir=processed_dir, processed_dir=processed_dir)
        df_in = pd.DataFrame([
            {"Date": "2022-01-03", "sentiment_mean": 0.3, "headline_count": 7},
        ])
        saved_path = repo.save_daily_sentiment(df_in)
        assert saved_path.exists()

        df_out = repo.load_daily_sentiment()
        assert len(df_out) == 1

    def test_load_daily_count_not_found(self, tmp_path: Path):
        repo = SentimentRepository(raw_dir=tmp_path, processed_dir=tmp_path / "empty")
        with pytest.raises(NotFoundError):
            repo.load_daily_count()

    def test_save_and_load_daily_count(self, processed_dir: Path):
        repo = SentimentRepository(raw_dir=processed_dir, processed_dir=processed_dir)
        df_in = pd.DataFrame([
            {"Date": "2022-01-03", "count": 15},
            {"Date": "2022-01-04", "count": 8},
        ])
        repo.save_daily_count(df_in)
        df_out = repo.load_daily_count()
        assert len(df_out) == 2
