# Class Diagram — Alur Halaman → Service → Model (Gaya Sederhana)

Gaya diagram: tiap kelas cuma tampilkan nama + method (tanpa atribut, tanpa
stereotype), panah asosiasi diberi label aksi — mengikuti gaya referensi
(`ModelTrainingPage`/`PredictionsPage` → `Controller` → `Trainer`/`Model`).
Dipetakan ke arsitektur nyata backend `stock_prediction` (3 halaman FE yang
bisa dinavigasi: Model Training, Prediksi, Alur Kerja).

```mermaid
classDiagram
    class ModelTrainingPage {
        +mulaiRandomSearch()
        +mulaiTrainingManual()
    }

    class PredictionsPage {
        +lihatHasilTersimpan()
        +jalankanPrediksi()
        +jalankanBacktest()
    }

    class YahooFinanceService {
        +ambilHargaSahamLive()
        +ambilBeritaTerkini()
    }

    class WorkflowPage {
        +jalankanSentimentScoring()
        +bangunDatasetLatih()
    }

    class TrainingService {
        +terimaPermintaanTraining()
        +terimaPermintaanPrediksi()
    }

    class DataAnalysisService {
        +terimaPermintaanDataset()
    }

    class FinBERTSentimentAnalyzer {
        +analisisSentimenHeadline()
    }

    class LSTMModelPipeline {
        +latihModel()
        +prediksi()
        +backtest()
    }

    class FlexibleLSTMClassifier {
        +forward()
    }

    class ArtefakPenyimpanan {
        +simpanModel()
        +muatModel()
        +simpanDataset()
        +muatDataset()
    }

    ModelTrainingPage --> TrainingService : memanggil
    PredictionsPage --> TrainingService : memanggil
    PredictionsPage --> YahooFinanceService : mengambil data
    WorkflowPage --> DataAnalysisService : memanggil
    WorkflowPage --> FinBERTSentimentAnalyzer : menjalankan

    YahooFinanceService --> FinBERTSentimentAnalyzer : skor berita live

    TrainingService --> LSTMModelPipeline : menjalankan
    DataAnalysisService --> LSTMModelPipeline : menjalankan

    LSTMModelPipeline --> FlexibleLSTMClassifier : melatih & mengevaluasi
    LSTMModelPipeline --> ArtefakPenyimpanan : memuat & menyimpan
```
