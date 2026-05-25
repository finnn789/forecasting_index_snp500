from pathlib import Path

from app.core.exceptions import NotFoundError
from app.core.settings import settings
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

    def list_lstm_runs(self) -> list[str]:
        if not self._lstm_dir.exists():
            return []
        return [p.stem for p in sorted(self._lstm_dir.glob("*.pt"))]

    def finbert_local_dir(self) -> Path:
        return Path(settings.finbert_local_path)
