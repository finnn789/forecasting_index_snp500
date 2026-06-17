"""
tests/tests_service/test_feature_engineering_helpers.py

Unit tests for the functions called inside run_feature_engineering():
1. pipeline.feature_engineering.sentiment_aggregator.load_daily_sentiment
2. pipeline.feature_engineering.sentiment_aggregator.extract_features
3. pipeline.feature_engineering.sentiment_aggregator.get_feature_summary
4. app.helpers.serialization.to_json_safe_records
"""

import json
import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from pipeline.feature_engineering.sentiment_aggregator import (
    load_daily_sentiment,
    extract_features,
    get_feature_summary,
)
from app.helpers.serialization import to_json_safe_records


@pytest.fixture
def temp_sentiment_csv(tmp_path: Path) -> Path:
    """Fixture to create a temporary daily sentiment CSV file with 15 rows of data."""
    np.random.seed(42)
    dates = pd.date_range("2026-05-01", periods=15)
    df = pd.DataFrame({
        "Date": dates,
        "headline_count": np.random.randint(1, 20, 15),
        "sentiment_mean": np.random.uniform(-1, 1, 15),
        "sentiment_pos": np.random.uniform(0, 1, 15),
        "sentiment_neg": np.random.uniform(0, 1, 15),
        "sentiment_neu": np.random.uniform(0, 1, 15),
        "sentiment_label": np.random.choice(["positive", "neutral", "negative"], 15),
        "CP": 4500.0 + np.cumsum(np.random.randn(15) * 10),
    })
    csv_path = tmp_path / "mock_headlines_daily_sentiment.csv"
    df.to_csv(csv_path, index=False)
    return csv_path




def test_load_daily_sentiment_output(temp_sentiment_csv):
    """Test and show output of load_daily_sentiment()."""
    print("\n" + "="*50)
    print("TEST: load_daily_sentiment")
    print("="*50)
    
    # Run the function
    df = load_daily_sentiment(temp_sentiment_csv)
    
    # Display the output
    print(f"Loaded DataFrame shape: {df.shape}")
    print("\nDataFrame columns and types:")
    print(df.dtypes)
    print("\nDataFrame sample (first 5 rows):")
    print(df.head())
    print("="*50)
    
    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 15
    assert "Date" in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["Date"])
    assert "sentiment_mean" in df.columns
    assert "sentiment_label" in df.columns
    assert "CP" in df.columns


def test_extract_features_output(temp_sentiment_csv):
    """Test and show output of extract_features()."""
    print("\n" + "="*50)
    print("TEST: extract_features")
    print("="*50)
    
    # Load raw daily sentiment first
    df_sentiment = load_daily_sentiment(temp_sentiment_csv)
    
    # Rename CP to Close and run extract_features with the exact parameters from the service
    df_feat = extract_features(
        df_sentiment.rename(columns={"CP": "Close"}),
        lag_cols=["Close", "sentiment_mean"],
        lags=[1, 3, 5],
        roll_windows=[3, 7],
        target_horizon=1,
        target_mode="return",
    )
    
    # Display the output
    print(f"Engineered DataFrame shape: {df_feat.shape}")
    print("\nEngineered DataFrame columns:")
    print(list(df_feat.columns))
    print("\nEngineered DataFrame sample (first 3 rows):")
    print(df_feat.head(3))
    print("="*50)
    
    # Assertions
    assert isinstance(df_feat, pd.DataFrame)
    # 15 input rows:
    # - Lags of [1, 3, 5] introduce NaNs in the first 5 rows.
    # - Target horizon of 1 introduces NaN in the last row.
    # - total rows dropped = 5 (lag) + 1 (target) = 6 rows.
    # - Remaining rows: 15 - 6 = 9 rows.
    assert len(df_feat) == 9
    
    # Check generated features
    expected_cols = [
        "Close_lag1", "Close_lag3", "Close_lag5",
        "sentiment_mean_lag1", "sentiment_mean_lag3", "sentiment_mean_lag5",
        "sentiment_mean_roll3", "sentiment_mean_roll7",
        "sentiment_std_roll3", "sentiment_std_roll7",
        "target"
    ]
    for col in expected_cols:
        assert col in df_feat.columns, f"Feature column '{col}' is missing"


def test_get_feature_summary_output(temp_sentiment_csv):
    """Test and show output of get_feature_summary()."""
    print("\n" + "="*50)
    print("TEST: get_feature_summary")
    print("="*50)
    
    # Prepare engineered DataFrame
    df_sentiment = load_daily_sentiment(temp_sentiment_csv)
    df_feat = extract_features(
        df_sentiment.rename(columns={"CP": "Close"}),
        lag_cols=["Close", "sentiment_mean"],
        lags=[1, 3, 5],
        roll_windows=[3, 7],
        target_horizon=1,
        target_mode="return",
    )
    
    # Run the function
    summary = get_feature_summary(df_feat)
    
    # Display the output (pretty printed JSON style)
    print("Feature Summary output dictionary:")
    print(json.dumps(summary, indent=2, default=str))
    print("="*50)
    
    # Assertions
    assert isinstance(summary, dict)
    assert summary["total_rows"] == 9
    assert summary["total_columns"] == len(df_feat.columns)
    assert "date_range" in summary
    assert "start" in summary["date_range"] and "end" in summary["date_range"]
    assert "missing_values" in summary
    assert "statistics" in summary
    assert "sentiment_distribution" in summary


def test_to_json_safe_records_output(temp_sentiment_csv):
    """Test and show output of to_json_safe_records()."""
    print("\n" + "="*50)
    print("TEST: to_json_safe_records")
    print("="*50)
    
    # Prepare engineered DataFrame
    df_sentiment = load_daily_sentiment(temp_sentiment_csv)
    df_feat = extract_features(
        df_sentiment.rename(columns={"CP": "Close"}),
        lag_cols=["Close", "sentiment_mean"],
        lags=[1, 3, 5],
        roll_windows=[3, 7],
        target_horizon=1,
        target_mode="return",
    )
    
    # Let's add a row with numpy/datetime types and a NaN to verify JSON serialization robustness
    # The dataframe already has pandas Timestamp, float64 and int64. Let's explicitly inject a NaN
    df_with_nan = df_feat.copy()
    df_with_nan.loc[0, "Close"] = float("nan")
    
    # Run the function with limit n=5
    records = to_json_safe_records(df_with_nan, 5)
    
    # Display the output
    print(f"Serialized records count: {len(records)}")
    print("\nFirst serialized record (with injected NaN close value):")
    print(json.dumps(records[0], indent=2, default=str))
    print("\nSecond serialized record:")
    print(json.dumps(records[1], indent=2, default=str))
    print("="*50)
    
    # Assertions
    assert isinstance(records, list)
    assert len(records) == 5
    
    # Ensure types are native python types and JSON serializable
    # Check NaN conversion
    assert records[0]["Close"] is None
    
    # Verify date is formatted as string/datetime
    assert isinstance(records[0]["Date"], str)
    
    # Verify that we can dump it to valid JSON without error
    serialized_str = json.dumps(records)
    loaded_back = json.loads(serialized_str)
    assert len(loaded_back) == 5
