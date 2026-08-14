# Class Diagram — Backend, Dikelompokkan per Halaman FE

Versi paling ringkas — hanya kelas BE yang benar-benar dipanggil dari 3
halaman FE yang bisa dinavigasi (`ui-stock-prediction`): **Prediksi**,
**Model Training**, **Alur Kerja**. Kelas BE yang tidak dipakai halaman
manapun (mis. alur early-fusion lama, `ArtifactRepository`, `DataInformationService`)
dihilangkan total — lihat [`class_diagram.md`](./class_diagram.md) untuk
gambaran lengkap.

Karena `TrainingService` dan `Notebook07Pipeline` dipakai lebih dari satu
halaman, keduanya ditaruh di namespace halaman yang paling relevan lalu
diberi **note** menandai halaman lain yang juga memakainya — bukan diduplikasi.

```mermaid
classDiagram
    namespace HalamanPrediksi {
        class LiveService {
          <<service>>
          +fetch_live_ohlcv() DataFrame
          +get_live_stock_latest(n) dict
          +run_live_predict_stream(emit)
        }
        class LiveDataRepository {
          +upsert_ohlcv(df, fetched_at)
          +load_ohlcv() DataFrame
        }
    }

    namespace HalamanModelTraining {
        class TrainingService {
          <<service>>
          +run_skripsi_baseline/finbert_stream(req, emit)
          +run_skripsi_..._manual_stream(req, emit)
          +predict_notebook07(variant) dict
          +backtest_notebook07(variant, split) dict
        }
        class Notebook07Pipeline {
          <<module>>
          +run_notebook07_training(emit, ...)
          +run_notebook07_manual_training(emit, ...)
          +predict_latest_notebook07(...) dict
          +predict_live_notebook07(...) dict
          +backtest_notebook07(split, ...) dict
        }
        class FlexibleLSTMClassifier {
          <<nn.Module>>
          +forward(x) Tensor
        }
        class DatasetBundle {
          <<dataclass>>
          X_train, y_train, scaler, feature_cols
        }
    }

    namespace HalamanAlurKerja {
        class DataAnalysisService {
          <<service>>
          +get_combined_pipeline_steps() dict
          +build_combined_dataset(variant) dict
          +get_dataset_status(variant) dict
        }
        class SentimentService {
          <<service>>
          +run_preprocessing_pipeline_stream(emit)
          +get_pipeline_status() dict
        }
        class StockRepository {
          +load_raw(ticker) DataFrame
        }
        class NewsRepository {
          +load_clean_headlines() DataFrame
        }
        class SentimentRepository {
          +load_daily_sentiment() DataFrame
        }
    }

    LiveService ..> LiveDataRepository
    LiveService ..> Notebook07Pipeline : prediksi live

    DataAnalysisService ..> Notebook07Pipeline : bangun artefak dataset
    DataAnalysisService ..> StockRepository
    DataAnalysisService ..> NewsRepository
    DataAnalysisService ..> SentimentRepository
    SentimentService ..> NewsRepository
    SentimentService ..> SentimentRepository

    TrainingService ..> Notebook07Pipeline
    Notebook07Pipeline ..> FlexibleLSTMClassifier
    Notebook07Pipeline ..> DatasetBundle

    note for TrainingService "predict_notebook07()/backtest_notebook07()\njuga dipanggil dari Halaman Prediksi"
    note for DataAnalysisService "artefak dataset dibaca TrainingService\nsaat training di Halaman Model Training"
```
