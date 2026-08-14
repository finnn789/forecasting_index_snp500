"""
app/services/live_prediction_service.py — Orkestrasi SSE fitur "Prediksi Live"
di Dashboard: fetch OHLCV+berita live -> preprocessing (FinBERT scoring,
agregasi sentimen harian, return features) -> inference model FinBERT-LSTM
terlatih (`finbert_lstm_skripsi.pt`) -> prediksi arah 5 hari ke depan.

Event SSE (flat, 2 level — pola sama `sentiment_service.run_preprocessing_pipeline_stream`):
    start -> fetching_ohlcv -> fetching_news -> preprocessing -> inferring -> done
    atau -> error (kapan saja, termasuk kalau data live tidak cukup utk window).
"""

from __future__ import annotations

from collections.abc import Callable

from app.services import live_data_service
from app.services.training_service import _notebook07_variant_params


def run_live_predict_stream(emit: Callable[[dict], None]) -> None:
    from models.lstm.notebook07_common import load_trained_notebook07, predict_live_notebook07  # noqa: PLC0415

    emit({"type": "start"})

    try:
        params = _notebook07_variant_params("finbert")

        loaded = load_trained_notebook07(
            artifact_dir=params["artifact_dir"],
            model_filename=params["model_filename"],
            scaler_filename=params["scaler_filename"],
            metadata_filename=params["metadata_filename"],
        )
        if loaded is None:
            emit({
                "type": "error",
                "message": "Model FinBERT-LSTM belum pernah dilatih. Latih model di halaman Model Training terlebih dahulu.",
            })
            return
        window = loaded["window"]

        emit({"type": "fetching_ohlcv"})
        # fetch_live_ohlcv() upsert ke LiveDataRepository (SQLite) & return
        # SELURUH histori akumulasi, bukan cuma batch fetch ini — histori live
        # tumbuh tiap kali dipanggil (keputusan user).
        df_ohlcv = live_data_service.fetch_live_ohlcv()
        emit({
            "type": "fetching_ohlcv_done",
            "rows_fetched": len(df_ohlcv),
            "date_start": df_ohlcv["Date"].min().strftime("%Y-%m-%d"),
            "date_end": df_ohlcv["Date"].max().strftime("%Y-%m-%d"),
        })

        emit({"type": "fetching_news"})
        # fetch_score_and_accumulate_headlines() upsert headline BARU (yang
        # belum pernah di-score) ke LiveDataRepository & return SELURUH
        # histori akumulasi headline — sama prinsipnya dengan OHLCV di atas.
        df_scored = live_data_service.fetch_score_and_accumulate_headlines()
        emit({"type": "fetching_news_done", "headlines_accumulated": len(df_scored)})

        emit({"type": "preprocessing"})
        df_daily = live_data_service.aggregate_daily_live(df_scored)
        df_live = live_data_service.build_live_return_features(df_ohlcv, df_daily)
        rows_available = len(df_live)
        live_days = int(df_live["sentiment_is_live"].sum()) if rows_available else 0
        emit({
            "type": "preprocessing_done",
            "days_joined": len(df_daily),
            "rows_available": rows_available,
            "live_sentiment_days": live_days,
            "window_required": window,
        })

        if rows_available < window:
            emit({
                "type": "error",
                "message": (
                    f"Data live tidak cukup: hanya {rows_available} baris gabungan "
                    f"OHLCV+sentimen tersedia, butuh minimal {window} baris untuk "
                    "membentuk 1 window prediksi. Coba lagi nanti."
                ),
            })
            return

        emit({"type": "inferring"})
        result = predict_live_notebook07(
            feature_cols=params["feature_cols"],
            capping_cols=params["capping_cols"],
            artifact_dir=params["artifact_dir"],
            model_filename=params["model_filename"],
            scaler_filename=params["scaler_filename"],
            metadata_filename=params["metadata_filename"],
            historical_load_data_fn=params["load_data_fn"],
            live_df=df_live,
            horizon=params["horizon"],
        )

        emit({
            "type": "done",
            **{k: v for k, v in result.items() if k != "trained"},
            "headlines_accumulated": len(df_scored),
            "live_sentiment_days": live_days,
        })

    except Exception as e:  # noqa: BLE001 — proses live, wajib emit error apa adanya
        emit({"type": "error", "message": str(e)})
