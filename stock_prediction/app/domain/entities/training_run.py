from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict

TrainingStatus = Literal["pending", "running", "completed", "failed"]


class TrainingRun(BaseModel):
    model_config = ConfigDict(frozen=False)  # mutable supaya bisa update progres
    id: str
    started_at: datetime
    finished_at: datetime | None = None
    status: TrainingStatus = "pending"
    epochs_completed: int = 0
    total_epochs: int
    best_metric: float | None = None
    metric_name: str = "val_rmse"
    error_message: str | None = None
