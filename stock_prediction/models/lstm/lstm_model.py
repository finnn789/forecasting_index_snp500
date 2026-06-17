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
