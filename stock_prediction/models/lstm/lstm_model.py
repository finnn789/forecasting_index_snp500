"""LSTM Direction Classifier — PyTorch.

Arsitektur:
    LSTM(n_features, hidden, num_layers, batch_first=True, dropout)
    -> ambil output timestep TERAKHIR
    -> Linear(hidden, 16) -> ReLU -> Dropout(dropout) -> Linear(16, 1)

forward(x: (B, W, F)) -> logits shape (B,)  [TANPA sigmoid]
Gunakan BCEWithLogitsLoss saat training.
"""

import torch
import torch.nn as nn


class LSTMDirectionClassifier(nn.Module):
    """Binary direction classifier menggunakan LSTM.

    Args:
        n_features: Jumlah fitur input per timestep (default 6: OHLCV + sentiment_mean).
        hidden: Ukuran hidden state LSTM.
        num_layers: Jumlah layer LSTM yang di-stack.
        dropout: Dropout rate — diterapkan di antara LSTM layers dan di head.
    """

    def __init__(
        self,
        n_features: int,
        hidden: int = 64,
        num_layers: int = 2,
        dropout: float = 0.3,
    ) -> None:
        super().__init__()
        self.hidden = hidden
        self.num_layers = num_layers

        # LSTM: dropout hanya aktif jika num_layers > 1 (PyTorch requirement)
        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.lstm = nn.LSTM(
            input_size=n_features,
            hidden_size=hidden,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
        )

        # Classification head
        self.head = nn.Sequential(
            nn.Linear(hidden, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor shape (B, W, F) — batch, window, features.

        Returns:
            logits: Tensor shape (B,) — raw logit per sampel, TANPA sigmoid.
        """
        # lstm_out: (B, W, hidden)
        lstm_out, _ = self.lstm(x)
        # Ambil timestep terakhir: (B, hidden)
        last_hidden = lstm_out[:, -1, :]
        # head: (B, 1) -> squeeze ke (B,)
        logits = self.head(last_hidden).squeeze(-1)
        return logits


def build_classifier(
    n_features: int,
    hidden: int = 64,
    num_layers: int = 2,
    dropout: float = 0.3,
) -> LSTMDirectionClassifier:
    """Factory function untuk membuat LSTMDirectionClassifier.

    Args:
        n_features: Jumlah fitur input.
        hidden: Ukuran hidden state LSTM.
        num_layers: Jumlah layer LSTM.
        dropout: Dropout rate.

    Returns:
        Instance LSTMDirectionClassifier yang belum di-train.
    """
    return LSTMDirectionClassifier(
        n_features=n_features,
        hidden=hidden,
        num_layers=num_layers,
        dropout=dropout,
    )


# ---------------------------------------------------------------------------
# FlexibleLSTMClassifier — TERISOLASI dari produksi, dipakai
# oleh "Random Search Skripsi-Scoped" (notebook 07 / models/lstm/notebook07_common.py).
#
# BEDA dari LSTMDirectionClassifier di atas:
#   - Output 2-class softmax (via CrossEntropyLoss), BUKAN logit biner tunggal.
#   - Aktivasi FC-head BISA DIKONFIGURASI (ReLU/Tanh/Sigmoid) — salah satu dimensi
#     Random Search sesuai Batasan Masalah BAB I skripsi.
#   - Head: Linear(hidden,16) -> activation -> Dropout -> Linear(16, num_classes),
#     bukan langsung Linear(hidden, num_classes).
#   - JANGAN dipakai untuk produksi.
# ---------------------------------------------------------------------------

ACTIVATION_MAP = {
    "relu": nn.ReLU,
    "tanh": nn.Tanh,
    "sigmoid": nn.Sigmoid,
}


class FlexibleLSTMClassifier(nn.Module):
    """LSTM classifier dgn arsitektur bisa dikonfigurasi untuk Random Search
    (replikasi notebook 07 — skripsi-scoped, Batasan Masalah BAB I).

    Args:
        input_size: Jumlah fitur input per timestep (5 OHLCV atau 6 OHLCV+sentiment_mean).
        hidden_size: Ukuran hidden state LSTM.
        num_layers: Jumlah layer LSTM yang di-stack.
        dropout: Dropout rate.
        activation: Aktivasi FC-head — salah satu dari {"relu", "tanh", "sigmoid"}.
        num_classes: Jumlah kelas output (default 2: down/up).
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 32,
        num_layers: int = 1,
        dropout: float = 0.3,
        activation: str = "relu",
        num_classes: int = 2,
    ) -> None:
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        lstm_dropout = dropout if num_layers > 1 else 0.0
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
        )
        act_cls = ACTIVATION_MAP[activation]
        self.head = nn.Sequential(
            nn.Linear(hidden_size, 16),
            act_cls(),
            nn.Dropout(dropout),
            nn.Linear(16, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor shape (B, W, F) — batch, window, features.

        Returns:
            logits: Tensor shape (B, num_classes) — raw logits, TANPA softmax
            (gunakan CrossEntropyLoss saat training, argmax(dim=1) saat prediksi).
        """
        lstm_out, _ = self.lstm(x)          # (B, W, hidden)
        last_hidden = lstm_out[:, -1, :]    # (B, hidden) — last-timestep
        logits = self.head(last_hidden)     # (B, num_classes)
        return logits
