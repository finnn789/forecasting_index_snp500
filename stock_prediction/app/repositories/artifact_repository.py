from pathlib import Path

from app.core.exceptions import NotFoundError
from .base import FileBasedRepository


class ArtifactRepository(FileBasedRepository):
    def __init__(self, lstm_dir: Path, finbert_dir: Path) -> None:
        super().__init__(lstm_dir)
        self._lstm_dir = Path(lstm_dir)
        self._finbert_dir = Path(finbert_dir)

    def lstm_checkpoint_path(self, run_id: str) -> Path:
        return self._lstm_dir / f"{run_id}.pt"

    def save_lstm_checkpoint(self, run_id: str, state_dict: dict) -> Path:
        import torch
        self._lstm_dir.mkdir(parents=True, exist_ok=True)
        path = self.lstm_checkpoint_path(run_id)
        torch.save(state_dict, path)
        return path

    def load_lstm_checkpoint(self, run_id: str) -> dict:
        import torch
        path = self.lstm_checkpoint_path(run_id)
        if not path.exists():
            raise NotFoundError(
                f"Checkpoint LSTM tidak ditemukan: {path}",
                code="CHECKPOINT_NOT_FOUND",
            )
        return torch.load(path, map_location="cpu")

    # ------------------------------------------------------------------
    # Metadata model (menutup bypass json.loads manual di service layer)
    # ------------------------------------------------------------------
    def metadata_path(self, filename: str = "metadata.json") -> Path:
        return self._lstm_dir / filename

    def load_metadata(self, filename: str = "metadata.json") -> dict:
        import json
        path = self.metadata_path(filename)
        if not path.exists():
            raise NotFoundError(
                f"Metadata model tidak ditemukan: {path}",
                code="METADATA_NOT_FOUND",
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def save_metadata(self, metadata: dict, filename: str = "metadata.json") -> Path:
        import json
        self._lstm_dir.mkdir(parents=True, exist_ok=True)
        path = self.metadata_path(filename)
        path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        return path

    # ------------------------------------------------------------------
    # Scaler (joblib) — artefak pendamping model
    # ------------------------------------------------------------------
    def scaler_path(self, filename: str = "scaler.joblib") -> Path:
        return self._lstm_dir / filename

    def load_scaler(self, filename: str = "scaler.joblib"):
        import joblib
        path = self.scaler_path(filename)
        if not path.exists():
            raise NotFoundError(
                f"Scaler tidak ditemukan: {path}",
                code="SCALER_NOT_FOUND",
            )
        return joblib.load(path)

    def save_scaler(self, scaler, filename: str = "scaler.joblib") -> Path:
        import joblib
        self._lstm_dir.mkdir(parents=True, exist_ok=True)
        path = self.scaler_path(filename)
        joblib.dump(scaler, path)
        return path
