"""Tests untuk domain entities."""

from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.domain.entities import (
    StockBar,
    Headline,
    SentimentScore,
    DailySentiment,
    TrainingRun,
    PredictionResult,
)


class TestStockBar:
    def test_valid_stock_bar(self):
        bar = StockBar(
            date=date(2023, 1, 2),
            open=100.0,
            high=110.0,
            low=95.0,
            close=105.0,
            volume=1_000_000.0,
        )
        assert bar.close == 105.0

    def test_stock_bar_invalid_high(self):
        with pytest.raises(ValidationError):
            StockBar(
                date=date(2023, 1, 2),
                open=100.0,
                high=90.0,  # lebih rendah dari open/close/low
                low=85.0,
                close=95.0,
                volume=1000.0,
            )

    def test_stock_bar_invalid_low(self):
        with pytest.raises(ValidationError):
            StockBar(
                date=date(2023, 1, 2),
                open=100.0,
                high=110.0,
                low=108.0,  # lebih tinggi dari open dan close
                close=102.0,
                volume=1000.0,
            )

    def test_stock_bar_negative_volume(self):
        with pytest.raises(ValidationError):
            StockBar(
                date=date(2023, 1, 2),
                open=100.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=-1.0,
            )


class TestHeadline:
    def test_valid_headline(self):
        h = Headline(date=date(2023, 5, 10), title="Markets rally on Fed news")
        assert h.title == "Markets rally on Fed news"

    def test_headline_empty_title(self):
        with pytest.raises(ValidationError):
            Headline(date=date(2023, 5, 10), title="")

    def test_headline_whitespace_only_title(self):
        with pytest.raises(ValidationError):
            Headline(date=date(2023, 5, 10), title="   ")

    def test_headline_optional_source(self):
        h = Headline(date=date(2023, 5, 10), title="Some news", source="Reuters")
        assert h.source == "Reuters"
        h2 = Headline(date=date(2023, 5, 10), title="Some news")
        assert h2.source is None


class TestSentimentScore:
    def test_valid_sentiment_score(self):
        s = SentimentScore(
            positive=0.7,
            negative=0.1,
            neutral=0.2,
            label="positive",
            score=0.6,
        )
        assert s.label == "positive"

    def test_sentiment_score_probs_not_sum_to_one(self):
        with pytest.raises(ValidationError):
            SentimentScore(
                positive=0.5,
                negative=0.5,
                neutral=0.5,  # total = 1.5
                label="positive",
                score=0.0,
            )

    def test_sentiment_score_label_literal(self):
        with pytest.raises(ValidationError):
            SentimentScore(
                positive=0.34,
                negative=0.33,
                neutral=0.33,
                label="unknown",  # bukan literal yang valid
                score=0.01,
            )

    def test_daily_sentiment(self):
        ds = DailySentiment(
            date=date(2023, 1, 10),
            score_mean=0.3,
            score_positive=0.6,
            score_negative=0.1,
            label="positive",
        )
        assert ds.score_mean == 0.3


class TestTrainingRun:
    def test_training_run_default_status(self):
        run = TrainingRun(
            id="run-001",
            started_at=datetime(2024, 1, 1, 8, 0, 0),
            status="pending",
            total_epochs=50,
        )
        assert run.status == "pending"
        assert run.epochs_completed == 0
        assert run.metric_name == "val_rmse"

    def test_training_run_completed(self):
        run = TrainingRun(
            id="run-002",
            started_at=datetime(2024, 1, 1, 8, 0, 0),
            finished_at=datetime(2024, 1, 1, 10, 0, 0),
            status="completed",
            total_epochs=100,
            epochs_completed=100,
            best_metric=0.0142,
        )
        assert run.status == "completed"
        assert run.best_metric == 0.0142


class TestPredictionResult:
    def test_valid_prediction(self):
        p = PredictionResult(
            ticker="GSPC",
            target_date=date(2024, 3, 1),
            predicted_close=5100.0,
            sentiment_score=0.3,
            confidence=0.75,
            lstm_weight=0.7,
            sentiment_weight=0.3,
        )
        assert p.confidence == 0.75

    def test_prediction_confidence_out_of_range(self):
        with pytest.raises(ValidationError):
            PredictionResult(
                ticker="GSPC",
                target_date=date(2024, 3, 1),
                predicted_close=5100.0,
                sentiment_score=0.3,
                confidence=1.5,  # > 1.0
                lstm_weight=0.7,
                sentiment_weight=0.3,
            )
