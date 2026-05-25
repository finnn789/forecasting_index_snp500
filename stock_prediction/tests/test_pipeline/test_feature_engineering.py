"""
tests/test_pipeline/test_feature_engineering.py

Unit test untuk:
  - pipeline.feature_engineering.technical_indicators
  - pipeline.feature_engineering.sentiment_aggregator (feature extraction)
"""

import numpy as np
import pandas as pd
import pytest

from pipeline.feature_engineering.technical_indicators import compute_technical_indicators
from pipeline.feature_engineering.sentiment_aggregator import (
    add_lag_features,
    add_rolling_sentiment,
    build_lstm_sequences,
    create_target,
    encode_sentiment_label,
    extract_features,
    merge_sentiment,
    save_features,
    split_dataset,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ohlcv_df() -> pd.DataFrame:
    """DataFrame OHLCV sintetis 60 hari."""
    np.random.seed(0)
    n = 60
    close = 4000 + np.cumsum(np.random.randn(n) * 15)
    return pd.DataFrame({
        "Date"  : pd.date_range("2022-01-01", periods=n),
        "Open"  : close - np.random.uniform(0, 10, n),
        "High"  : close + np.random.uniform(0, 15, n),
        "Low"   : close - np.random.uniform(0, 15, n),
        "Close" : close,
        "Volume": np.random.randint(1_000_000, 10_000_000, n),
    })


@pytest.fixture
def sentiment_df() -> pd.DataFrame:
    """DataFrame sentimen harian sintetis 60 hari."""
    np.random.seed(1)
    n = 60
    return pd.DataFrame({
        "Date"           : pd.date_range("2022-01-01", periods=n),
        "headline_count" : np.random.randint(1, 20, n),
        "sentiment_mean" : np.random.uniform(-1, 1, n),
        "sentiment_pos"  : np.random.uniform(0, 1, n),
        "sentiment_neg"  : np.random.uniform(0, 1, n),
        "sentiment_neu"  : np.random.uniform(0, 1, n),
        "sentiment_label": np.random.choice(["positive", "negative", "neutral"], n),
        "CP"             : 4000 + np.cumsum(np.random.randn(n) * 15),
    })


@pytest.fixture
def merged_df(ohlcv_df, sentiment_df) -> pd.DataFrame:
    """DataFrame hasil merge OHLCV + sentimen."""
    df = ohlcv_df.copy()
    df = merge_sentiment(df, df_sentiment=sentiment_df)
    return df


@pytest.fixture
def full_df(merged_df) -> pd.DataFrame:
    """DataFrame merged + indikator teknikal."""
    df = compute_technical_indicators(merged_df)
    return df


# ---------------------------------------------------------------------------
# technical_indicators
# ---------------------------------------------------------------------------

class TestComputeTechnicalIndicators:

    def test_returns_dataframe(self, ohlcv_df):
        result = compute_technical_indicators(ohlcv_df)
        assert isinstance(result, pd.DataFrame)

    def test_adds_expected_columns(self, ohlcv_df):
        result = compute_technical_indicators(ohlcv_df)
        expected = [
            "ema_20", "ema_50", "rsi_14",
            "macd", "macd_signal", "macd_hist",
            "bb_mid", "bb_upper", "bb_lower", "bb_bandwidth",
            "daily_return", "volatility_20",
        ]
        for col in expected:
            assert col in result.columns, f"Kolom '{col}' tidak ditemukan"

    def test_row_count_unchanged(self, ohlcv_df):
        result = compute_technical_indicators(ohlcv_df)
        assert len(result) == len(ohlcv_df)

    def test_rsi_range(self, ohlcv_df):
        result = compute_technical_indicators(ohlcv_df)
        valid = result["rsi_14"].dropna()
        assert (valid >= 0).all() and (valid <= 100).all(), "RSI harus berada di [0, 100]"

    def test_bb_upper_gte_lower(self, ohlcv_df):
        result = compute_technical_indicators(ohlcv_df)
        valid = result.dropna(subset=["bb_upper", "bb_lower"])
        assert (valid["bb_upper"] >= valid["bb_lower"]).all()

    def test_raises_on_missing_columns(self):
        df = pd.DataFrame({"Date": pd.date_range("2022-01-01", periods=5), "Close": [1, 2, 3, 4, 5]})
        with pytest.raises(ValueError, match="Kolom OHLCV tidak lengkap"):
            compute_technical_indicators(df)

    def test_sorted_by_date(self, ohlcv_df):
        shuffled = ohlcv_df.sample(frac=1, random_state=42)
        result = compute_technical_indicators(shuffled)
        assert result["Date"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# encode_sentiment_label
# ---------------------------------------------------------------------------

class TestEncodeSentimentLabel:

    def test_encoding_values(self, merged_df):
        result = encode_sentiment_label(merged_df)
        mapping = {"positive": 1, "neutral": 0, "negative": -1}
        for label, val in mapping.items():
            rows = result[result["sentiment_label"].str.lower() == label]
            assert (rows["sentiment_label_enc"] == val).all()

    def test_new_column_added(self, merged_df):
        result = encode_sentiment_label(merged_df)
        assert "sentiment_label_enc" in result.columns

    def test_no_nan_in_encoded(self, merged_df):
        result = encode_sentiment_label(merged_df)
        assert result["sentiment_label_enc"].isnull().sum() == 0

    def test_skip_if_no_label_column(self, ohlcv_df):
        result = encode_sentiment_label(ohlcv_df)
        assert "sentiment_label_enc" not in result.columns


# ---------------------------------------------------------------------------
# add_lag_features
# ---------------------------------------------------------------------------

class TestAddLagFeatures:

    def test_lag_columns_created(self, merged_df):
        result = add_lag_features(merged_df, cols=["Close"], lags=[1, 3])
        assert "Close_lag1" in result.columns
        assert "Close_lag3" in result.columns

    def test_lag1_values_correct(self, merged_df):
        result = add_lag_features(merged_df, cols=["Close"], lags=[1])
        # Close_lag1[i] harus sama dengan Close[i-1]
        assert result["Close_lag1"].iloc[1] == pytest.approx(result["Close"].iloc[0])

    def test_first_row_nan(self, merged_df):
        result = add_lag_features(merged_df, cols=["Close"], lags=[1])
        assert pd.isna(result["Close_lag1"].iloc[0])

    def test_row_count_unchanged(self, merged_df):
        result = add_lag_features(merged_df, cols=["Close"], lags=[1, 3])
        assert len(result) == len(merged_df)

    def test_skip_missing_column(self, merged_df):
        result = add_lag_features(merged_df, cols=["nonexistent_col"], lags=[1])
        assert "nonexistent_col_lag1" not in result.columns


# ---------------------------------------------------------------------------
# add_rolling_sentiment
# ---------------------------------------------------------------------------

class TestAddRollingSentiment:

    def test_rolling_columns_created(self, merged_df):
        result = add_rolling_sentiment(merged_df, windows=[3, 7])
        for col in ["sentiment_mean_roll3", "sentiment_mean_roll7",
                    "sentiment_std_roll3",  "sentiment_std_roll7"]:
            assert col in result.columns

    def test_no_nan_due_to_min_periods(self, merged_df):
        result = add_rolling_sentiment(merged_df, windows=[3])
        assert result["sentiment_mean_roll3"].isnull().sum() == 0

    def test_row_count_unchanged(self, merged_df):
        result = add_rolling_sentiment(merged_df, windows=[3])
        assert len(result) == len(merged_df)


# ---------------------------------------------------------------------------
# create_target
# ---------------------------------------------------------------------------

class TestCreateTarget:

    def test_target_column_exists(self, merged_df):
        result = create_target(merged_df, horizon=1, mode="return")
        assert "target" in result.columns

    def test_return_mode_no_nan(self, merged_df):
        result = create_target(merged_df, horizon=1, mode="return")
        assert result["target"].isnull().sum() == 0

    def test_direction_mode_binary(self, merged_df):
        result = create_target(merged_df, horizon=1, mode="direction")
        unique = set(result["target"].unique())
        assert unique.issubset({0, 1})

    def test_last_rows_dropped(self, merged_df):
        result = create_target(merged_df, horizon=3, mode="return")
        assert len(result) == len(merged_df) - 3

    def test_raises_without_close(self, ohlcv_df):
        df_no_close = ohlcv_df.drop(columns=["Close"])
        with pytest.raises(ValueError, match="Kolom 'Close' diperlukan"):
            create_target(df_no_close)


# ---------------------------------------------------------------------------
# extract_features
# ---------------------------------------------------------------------------

class TestExtractFeatures:

    def test_returns_dataframe(self, full_df):
        result = extract_features(full_df)
        assert isinstance(result, pd.DataFrame)

    def test_target_column_present(self, full_df):
        result = extract_features(full_df)
        assert "target" in result.columns

    def test_no_nan_after_extraction(self, full_df):
        result = extract_features(full_df)
        assert result.isnull().sum().sum() == 0

    def test_row_count_reduced(self, full_df):
        result = extract_features(full_df)
        assert len(result) < len(full_df)

    def test_lag_and_rolling_cols_present(self, full_df):
        result = extract_features(full_df)
        cols = result.columns.tolist()
        assert any("lag" in c for c in cols)
        assert any("roll" in c for c in cols)


# ---------------------------------------------------------------------------
# build_lstm_sequences
# ---------------------------------------------------------------------------

class TestBuildLstmSequences:

    def test_output_shapes(self, full_df):
        df = extract_features(full_df)
        feat_cols = [c for c in df.columns if c not in ("Date", "sentiment_label", "target")]
        X, y = build_lstm_sequences(df, feature_cols=feat_cols, window_size=5)
        assert X.ndim == 3
        assert y.ndim == 1
        assert X.shape[0] == y.shape[0]
        assert X.shape[1] == 5
        assert X.shape[2] == len(feat_cols)

    def test_sample_count(self, full_df):
        df = extract_features(full_df)
        feat_cols = [c for c in df.columns if c not in ("Date", "sentiment_label", "target")]
        window = 5
        X, y = build_lstm_sequences(df, feature_cols=feat_cols, window_size=window)
        assert X.shape[0] == len(df) - window

    def test_dtype_float32(self, full_df):
        df = extract_features(full_df)
        feat_cols = [c for c in df.columns if c not in ("Date", "sentiment_label", "target")]
        X, y = build_lstm_sequences(df, feature_cols=feat_cols, window_size=5)
        assert X.dtype == np.float32
        assert y.dtype == np.float32

    def test_raises_on_missing_feature_col(self, full_df):
        df = extract_features(full_df)
        with pytest.raises(ValueError, match="Kolom tidak ditemukan"):
            build_lstm_sequences(df, feature_cols=["col_tidak_ada"], window_size=5)


# ---------------------------------------------------------------------------
# split_dataset
# ---------------------------------------------------------------------------

class TestSplitDataset:

    def test_total_rows_preserved(self, full_df):
        df = extract_features(full_df)
        tr, va, te = split_dataset(df, train_ratio=0.7, val_ratio=0.15)
        assert len(tr) + len(va) + len(te) == len(df)

    def test_time_order_maintained(self, full_df):
        df = extract_features(full_df)
        tr, va, te = split_dataset(df)
        if "Date" in df.columns:
            assert tr["Date"].max() <= va["Date"].min()
            assert va["Date"].max() <= te["Date"].min()

    def test_split_ratios_approximate(self, full_df):
        df = extract_features(full_df)
        n = len(df)
        tr, va, te = split_dataset(df, train_ratio=0.7, val_ratio=0.15)
        assert abs(len(tr) / n - 0.7) < 0.02
        assert abs(len(va) / n - 0.15) < 0.02


# ---------------------------------------------------------------------------
# save_features
# ---------------------------------------------------------------------------

class TestSaveFeatures:

    def test_file_created(self, full_df, tmp_path):
        df = extract_features(full_df)
        out = tmp_path / "features.csv"
        result_path = save_features(df, path=out)
        assert result_path.exists()

    def test_saved_content_matches(self, full_df, tmp_path):
        df = extract_features(full_df)
        out = tmp_path / "features.csv"
        save_features(df, path=out)
        loaded = pd.read_csv(out)
        assert len(loaded) == len(df)
        assert list(loaded.columns) == list(df.columns)

    def test_creates_parent_dir(self, full_df, tmp_path):
        df = extract_features(full_df)
        out = tmp_path / "nested" / "dir" / "features.csv"
        save_features(df, path=out)
        assert out.exists()
