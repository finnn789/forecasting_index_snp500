"""
app/services/data_information_service.py — Business logic untuk routes_data_information.py.

Menghitung ULANG (bukan angka statis) temuan diagnostik
notebooks/11_diagnostic_data_analysis_horizon.ipynb — kenapa model prediksi arah
(Model A: OHLCV, Model B: FinBERT-LSTM) collapse/bias — memakai logic yang PERSIS
sama: models/lstm/notebook07_common.py::load_split_capped() untuk split
kronologis 70/15/15 + capping outlier (IQR, fit-train-only), dan
pipeline/feature_engineering/dataset_builder.py untuk loader data mentah.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import MinMaxScaler

from app.core.exceptions import ValidationError
from app.helpers.serialization import format_iso_date
from app.schemas.data_analysis import Histogram
from app.schemas.data_information import (
    BaselineComparisonResponse,
    BaselineComparisonRow,
    ClosePoint,
    DistributionDriftResponse,
    FeatureCorrelationRow,
    FeatureDriftRow,
    FeatureHistogramPair,
    FeatureLabelCorrelationResponse,
    FeatureScalingInfo,
    Horizon,
    LabelBalanceResponse,
    LagCorrelationPoint,
    ModelKey,
    ModelLabelBalance,
    RegimeOverviewResponse,
    RollingUpPoint,
    ScaledClosePoint,
    ScalingRangeResponse,
    SentimentLagCorrelationResponse,
    SplitLabelBalance,
    SplitPeriodSummary,
)
from models.lstm.notebook07_common import load_split_capped
from models.lstm.notebook07_trainer import ARTIFACT_DIR, BASELINE_FILES, FINBERT_FILES
from pipeline.feature_engineering.dataset_builder import (
    FEATURE_COLS,
    OHLCV_FEATURE_COLS,
    load_joined,
    load_ohlcv_only,
)

_MAX_LAG = 10
_ROLLING_WINDOW = 60

_MODEL_CONFIG: dict[ModelKey, dict] = {
    "ohlcv": {
        "label": "Model A (OHLCV)",
        "load_fn": load_ohlcv_only,
        "capping_cols": ["Volume"],
        "feature_cols": OHLCV_FEATURE_COLS,
    },
    "joined": {
        "label": "Model B (FinBERT-LSTM)",
        "load_fn": load_joined,
        "capping_cols": ["Volume", "sentiment_mean"],
        "feature_cols": FEATURE_COLS,
    },
}

# Artefak horizon-5 (analisis sensitivitas, notebooks/10) — nama file SAMA PERSIS
# dengan yang disimpan notebook 10 sendiri, tidak ada konstanta bersama lain.
_H5_FILES: dict[ModelKey, dict[str, str]] = {
    "ohlcv": {
        "model": "lstm_baseline_skripsi_h5.pt",
        "scaler": "lstm_baseline_skripsi_h5_scaler.joblib",
        "metadata": "lstm_baseline_skripsi_h5_metadata.json",
    },
    "joined": {
        "model": "finbert_lstm_skripsi_h5.pt",
        "scaler": "finbert_lstm_skripsi_h5_scaler.joblib",
        "metadata": "finbert_lstm_skripsi_h5_metadata.json",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _r(x: float, nd: int = 6) -> float:
    return round(float(x), nd)


def _validate_horizon(horizon: int) -> Horizon:
    """Query param `horizon` diterima sebagai int biasa (lihat komentar di
    routes_data_information.py) — divalidasi eksplisit di sini, satu-satunya
    horizon yang punya artefak/logic terdefinisi adalah 1 dan 5."""
    if horizon not in (1, 5):
        raise ValidationError(f"horizon harus 1 atau 5, diterima: {horizon}")
    return horizon  # type: ignore[return-value]


def _histogram(values: pd.Series, bins: int = 30) -> Histogram:
    counts, edges = np.histogram(values.dropna(), bins=bins)
    return Histogram(bin_edges=[round(float(e), 6) for e in edges], counts=[int(c) for c in counts])


def _artifact_files(model: ModelKey, horizon: Horizon) -> dict[str, str]:
    if horizon == 1:
        return BASELINE_FILES if model == "ohlcv" else FINBERT_FILES
    return _H5_FILES[model]


def _load_metadata(model: ModelKey, horizon: Horizon) -> dict:
    files = _artifact_files(model, horizon)
    path = Path(ARTIFACT_DIR) / files["metadata"]
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. Regime overview
# ---------------------------------------------------------------------------

def get_regime_overview(model: ModelKey, horizon: Horizon) -> RegimeOverviewResponse:
    horizon = _validate_horizon(horizon)
    cfg = _MODEL_CONFIG[model]
    df_train, df_val, df_test, _, _ = load_split_capped(cfg["load_fn"], cfg["capping_cols"], horizon)
    splits = [("train", df_train), ("val", df_val), ("test", df_test)]

    full = pd.concat([df_train, df_val, df_test], ignore_index=True)
    points = [
        ClosePoint(date=format_iso_date(date), close=_r(close))
        for date, close in zip(full["Date"], full["Close"])
    ]

    summaries = []
    for name, d in splits:
        price_start = float(d["Close"].iloc[0])
        price_end = float(d["Close"].iloc[-1])
        summaries.append(
            SplitPeriodSummary(
                split=name,
                date_start=format_iso_date(d["Date"].min()),
                date_end=format_iso_date(d["Date"].max()),
                price_start=_r(price_start),
                price_end=_r(price_end),
                change_pct=_r((price_end / price_start - 1) * 100),
                price_min=_r(float(d["Close"].min())),
                price_max=_r(float(d["Close"].max())),
                up_pct=_r(float(d["label"].mean()) * 100),
                n_rows=len(d),
            )
        )

    return RegimeOverviewResponse(model=model, horizon=horizon, points=points, splits=summaries)


# ---------------------------------------------------------------------------
# 2. Label balance
# ---------------------------------------------------------------------------

def get_label_balance(horizon: Horizon) -> LabelBalanceResponse:
    horizon = _validate_horizon(horizon)
    models = []
    for key, cfg in _MODEL_CONFIG.items():
        df_train, df_val, df_test, _, _ = load_split_capped(cfg["load_fn"], cfg["capping_cols"], horizon)
        splits = []
        for name, d in [("train", df_train), ("val", df_val), ("test", df_test)]:
            up_pct = float(d["label"].mean()) * 100
            splits.append(SplitLabelBalance(split=name, n=len(d), up_pct=_r(up_pct), down_pct=_r(100 - up_pct)))
        models.append(ModelLabelBalance(model=key, model_label=cfg["label"], splits=splits))

    df_roll = load_joined().copy()
    df_roll["label"] = (df_roll["Close"].shift(-horizon) > df_roll["Close"]).astype(float)
    df_roll = df_roll.iloc[:-horizon].copy().reset_index(drop=True)
    roll = df_roll["label"].rolling(_ROLLING_WINDOW, min_periods=20).mean() * 100
    rolling = [
        RollingUpPoint(date=format_iso_date(date), rolling_up_pct=(_r(float(v)) if pd.notna(v) else None))
        for date, v in zip(df_roll["Date"], roll)
    ]

    return LabelBalanceResponse(horizon=horizon, models=models, rolling=rolling, rolling_window=_ROLLING_WINDOW)


# ---------------------------------------------------------------------------
# 3. Scaling range
# ---------------------------------------------------------------------------

def get_scaling_range(model: ModelKey, horizon: Horizon) -> ScalingRangeResponse:
    horizon = _validate_horizon(horizon)
    cfg = _MODEL_CONFIG[model]
    feat_cols = cfg["feature_cols"]
    df_train, df_val, df_test, _, _ = load_split_capped(cfg["load_fn"], cfg["capping_cols"], horizon)

    scaler = MinMaxScaler()
    scaler.fit(df_train[feat_cols].values.astype(float))
    val_scaled_all = scaler.transform(df_val[feat_cols].values.astype(float))
    test_scaled_all = scaler.transform(df_test[feat_cols].values.astype(float))

    features = []
    for i, col in enumerate(feat_cols):
        val_scaled = val_scaled_all[:, i]
        test_scaled = test_scaled_all[:, i]
        val_out = float(((val_scaled < 0) | (val_scaled > 1)).mean()) * 100
        test_out = float(((test_scaled < 0) | (test_scaled > 1)).mean()) * 100
        features.append(
            FeatureScalingInfo(
                feature=col,
                train_min=_r(float(df_train[col].min())),
                train_max=_r(float(df_train[col].max())),
                val_pct_out_of_range=_r(val_out),
                test_pct_out_of_range=_r(test_out),
                val_scaled_min=_r(float(val_scaled.min())),
                val_scaled_max=_r(float(val_scaled.max())),
                test_scaled_min=_r(float(test_scaled.min())),
                test_scaled_max=_r(float(test_scaled.max())),
            )
        )

    close_scaler = MinMaxScaler()
    close_scaler.fit(df_train[["Close"]].values.astype(float))
    close_series: list[ScaledClosePoint] = []
    for name, d in [("train", df_train), ("val", df_val), ("test", df_test)]:
        scaled = close_scaler.transform(d[["Close"]].values.astype(float)).ravel()
        for date, val in zip(d["Date"], scaled):
            close_series.append(ScaledClosePoint(date=format_iso_date(date), close_scaled=_r(float(val)), split=name))

    return ScalingRangeResponse(model=model, horizon=horizon, features=features, close_series=close_series)


# ---------------------------------------------------------------------------
# 4. Feature-label correlation
# ---------------------------------------------------------------------------

def get_feature_label_correlation(model: ModelKey, horizon: Horizon) -> FeatureLabelCorrelationResponse:
    horizon = _validate_horizon(horizon)
    cfg = _MODEL_CONFIG[model]
    feat_cols = cfg["feature_cols"]
    df_train, df_val, df_test, _, _ = load_split_capped(cfg["load_fn"], cfg["capping_cols"], horizon)
    splits = {"train": df_train, "val": df_val, "test": df_test}

    rows = []
    for col in feat_cols:
        r_vals: dict[str, float] = {}
        for name, d in splits.items():
            r, _p = stats.pointbiserialr(d["label"], d[col])
            r_vals[name] = float(r)
        reversed_direction = (
            np.sign(r_vals["train"]) != np.sign(r_vals["test"])
            and r_vals["train"] != 0
            and r_vals["test"] != 0
        )
        rows.append(
            FeatureCorrelationRow(
                feature=col,
                train_r=_r(r_vals["train"]),
                val_r=_r(r_vals["val"]),
                test_r=_r(r_vals["test"]),
                reversed_direction=bool(reversed_direction),
            )
        )

    return FeatureLabelCorrelationResponse(model=model, horizon=horizon, rows=rows)


# ---------------------------------------------------------------------------
# 5. Sentiment lag correlation
# ---------------------------------------------------------------------------

def _lag_series(df: pd.DataFrame) -> list[LagCorrelationPoint]:
    points = []
    for k in range(0, _MAX_LAG + 1):
        fwd = df["Close"].pct_change(1).shift(-k)
        valid = df["sentiment_mean"].notna() & fwd.notna()
        if int(valid.sum()) < 10:
            continue
        r, p = stats.pearsonr(df.loc[valid, "sentiment_mean"], fwd[valid])
        points.append(LagCorrelationPoint(lag_days=k, r=_r(float(r)), p_value=_r(float(p))))
    return points


def get_sentiment_lag_correlation() -> SentimentLagCorrelationResponse:
    df = load_joined().copy()
    overall = _lag_series(df)

    cfg = _MODEL_CONFIG["joined"]
    df_train, df_val, df_test, _, _ = load_split_capped(cfg["load_fn"], cfg["capping_cols"], 1)

    return SentimentLagCorrelationResponse(
        overall=overall,
        train=_lag_series(df_train.reset_index(drop=True)),
        val=_lag_series(df_val.reset_index(drop=True)),
        test=_lag_series(df_test.reset_index(drop=True)),
    )


# ---------------------------------------------------------------------------
# 6. Baseline comparison
# ---------------------------------------------------------------------------

def get_baseline_comparison() -> BaselineComparisonResponse:
    rows: list[BaselineComparisonRow] = []
    for model_key, cfg in _MODEL_CONFIG.items():
        for horizon in (1, 5):
            df_train, df_val, df_test, _, _ = load_split_capped(cfg["load_fn"], cfg["capping_cols"], horizon)
            splits = [("train", df_train), ("val", df_val), ("test", df_test)]
            metadata = _load_metadata(model_key, horizon)
            model_trained = bool(metadata)
            metrics = metadata.get("metrics") if metadata else None

            for split_name, d in splits:
                up = float(d["label"].mean())
                majority = max(up, 1 - up)
                persistence = float((d["label"] == d["label"].shift(1)).mean())
                is_test = split_name == "test"
                rows.append(
                    BaselineComparisonRow(
                        model=model_key,
                        model_label=cfg["label"],
                        horizon=horizon,
                        split=split_name,
                        n=len(d),
                        majority_baseline_acc=_r(majority),
                        persistence_baseline_acc=_r(persistence),
                        model_trained=model_trained,
                        model_accuracy=_r(metrics["accuracy"]) if (is_test and metrics) else None,
                        model_precision=_r(metrics["precision"]) if (is_test and metrics) else None,
                        model_recall=_r(metrics["recall"]) if (is_test and metrics) else None,
                        model_f1=_r(metrics["f1"]) if (is_test and metrics) else None,
                    )
                )

    return BaselineComparisonResponse(rows=rows)


# ---------------------------------------------------------------------------
# 7. (opsional) Distribution drift
# ---------------------------------------------------------------------------

def get_distribution_drift(model: ModelKey, horizon: Horizon) -> DistributionDriftResponse:
    horizon = _validate_horizon(horizon)
    cfg = _MODEL_CONFIG[model]
    feat_cols = cfg["feature_cols"]
    df_train, _df_val, df_test, _, _ = load_split_capped(cfg["load_fn"], cfg["capping_cols"], horizon)

    rows = []
    histograms = []
    for col in feat_cols:
        stat_ks, p = stats.ks_2samp(df_train[col], df_test[col])
        rows.append(
            FeatureDriftRow(
                feature=col,
                ks_statistic=_r(float(stat_ks)),
                p_value=_r(float(p)),
                significant=bool(p < 0.01),
            )
        )
        histograms.append(
            FeatureHistogramPair(feature=col, train=_histogram(df_train[col]), test=_histogram(df_test[col]))
        )

    return DistributionDriftResponse(model=model, horizon=horizon, rows=rows, histograms=histograms)
