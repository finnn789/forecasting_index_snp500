from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pipeline.preprocessing.text_preprocessor import TextPreprocessor


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Title": [
                "Stock market hits record high",
                "Company files for bankruptcy",
                "Market remains flat today",
            ],
            "Date": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "CP": [1500.0, 1480.0, 1490.0],
        }
    )


@pytest.fixture
def preprocessor() -> TextPreprocessor:
    return TextPreprocessor(model_path="/fake/model/path")


@pytest.fixture
def mock_pipeline_output() -> list[dict]:
    return [
        {"label": "positive", "score": 0.98},
        {"label": "negative", "score": 0.85},
        {"label": "neutral", "score": 0.75},
    ]


class TestDropCpColumn:
    def test_drops_cp_column_when_present(self, preprocessor, sample_df):
        result = preprocessor.drop_cp_column(sample_df)
        assert "CP" not in result.columns

    def test_preserves_other_columns(self, preprocessor, sample_df):
        result = preprocessor.drop_cp_column(sample_df)
        assert "Title" in result.columns
        assert "Date" in result.columns

    def test_no_error_when_cp_absent(self, preprocessor):
        df = pd.DataFrame({"Title": ["foo"], "Date": ["2024-01-01"]})
        result = preprocessor.drop_cp_column(df)
        assert list(result.columns) == ["Title", "Date"]

    def test_does_not_mutate_original_dataframe(self, preprocessor, sample_df):
        original_columns = list(sample_df.columns)
        preprocessor.drop_cp_column(sample_df)
        assert list(sample_df.columns) == original_columns

    def test_row_count_unchanged_after_drop(self, preprocessor, sample_df):
        result = preprocessor.drop_cp_column(sample_df)
        assert len(result) == len(sample_df)


class TestExtractSentimentScores:
    def test_adds_required_sentiment_columns(
        self, preprocessor, sample_df, mock_pipeline_output
    ):
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_pipeline_output)
            df_no_cp = preprocessor.drop_cp_column(sample_df)
            result = preprocessor.extract_sentiment_scores(df_no_cp)

        assert "sentiment_label" in result.columns
        assert "sentiment_score" in result.columns
        assert "sentiment_numeric" in result.columns

    def test_sentiment_label_values_are_lowercase(
        self, preprocessor, sample_df, mock_pipeline_output
    ):
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_pipeline_output)
            df_no_cp = preprocessor.drop_cp_column(sample_df)
            result = preprocessor.extract_sentiment_scores(df_no_cp)

        assert result["sentiment_label"].tolist() == ["positive", "negative", "neutral"]

    def test_sentiment_numeric_mapping(
        self, preprocessor, sample_df, mock_pipeline_output
    ):
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_pipeline_output)
            df_no_cp = preprocessor.drop_cp_column(sample_df)
            result = preprocessor.extract_sentiment_scores(df_no_cp)

        assert result["sentiment_numeric"].tolist() == [1, -1, 0]

    def test_sentiment_score_is_within_valid_range(
        self, preprocessor, sample_df, mock_pipeline_output
    ):
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_pipeline_output)
            df_no_cp = preprocessor.drop_cp_column(sample_df)
            result = preprocessor.extract_sentiment_scores(df_no_cp)

        assert all(0.0 <= score <= 1.0 for score in result["sentiment_score"])

    def test_row_count_unchanged_after_sentiment_extraction(
        self, preprocessor, sample_df, mock_pipeline_output
    ):
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_pipeline_output)
            df_no_cp = preprocessor.drop_cp_column(sample_df)
            result = preprocessor.extract_sentiment_scores(df_no_cp)

        assert len(result) == len(df_no_cp)

    def test_handles_null_and_empty_title(self, preprocessor):
        df = pd.DataFrame({"Title": [None, ""], "Date": ["2024-01-01", "2024-01-02"]})
        mock_output = [
            {"label": "neutral", "score": 0.6},
            {"label": "neutral", "score": 0.6},
        ]
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_output)
            result = preprocessor.extract_sentiment_scores(df)

        assert len(result) == 2
        assert result["sentiment_label"].tolist() == ["neutral", "neutral"]

    def test_does_not_mutate_original_dataframe(
        self, preprocessor, sample_df, mock_pipeline_output
    ):
        original_columns = list(sample_df.columns)
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_pipeline_output)
            preprocessor.extract_sentiment_scores(sample_df)

        assert list(sample_df.columns) == original_columns


class TestProcess:
    def test_process_removes_cp_and_adds_sentiment_columns(
        self, preprocessor, sample_df
    ):
        mock_output = [
            {"label": "positive", "score": 0.9},
            {"label": "negative", "score": 0.8},
            {"label": "neutral", "score": 0.7},
        ]
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_output)
            result = preprocessor.process(sample_df)

        assert "CP" not in result.columns
        assert "sentiment_label" in result.columns
        assert "sentiment_score" in result.columns
        assert "sentiment_numeric" in result.columns

    def test_process_preserves_row_count(self, preprocessor, sample_df):
        mock_output = [
            {"label": "positive", "score": 0.9},
            {"label": "negative", "score": 0.8},
            {"label": "neutral", "score": 0.7},
        ]
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_output)
            result = preprocessor.process(sample_df)

        assert len(result) == len(sample_df)

    def test_process_preserves_title_and_date_columns(self, preprocessor, sample_df):
        mock_output = [
            {"label": "positive", "score": 0.9},
            {"label": "negative", "score": 0.8},
            {"label": "neutral", "score": 0.7},
        ]
        with patch.object(preprocessor, "_load_pipeline") as mock_load:
            mock_load.return_value = MagicMock(return_value=mock_output)
            result = preprocessor.process(sample_df)

        assert "Title" in result.columns
        assert "Date" in result.columns
