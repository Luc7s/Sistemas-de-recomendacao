
from pathlib import Path

from src.persistence import load_artifacts


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


class AppState:
    def __init__(self):
        self.X = None
        self.scaler = None
        self.feature_columns = None
        self.df_clean = None
        self.metadata = None
        self.loaded = False

    def load(self):
        if self.loaded:
            return

        artifacts = load_artifacts(MODELS_DIR)

        self.X = artifacts["X"]
        self.scaler = artifacts["scaler"]
        self.feature_columns = artifacts["feature_columns"]
        self.df_clean = artifacts["df_clean"]
        self.metadata = artifacts["metadata"]

        self.loaded = True

        print(
            f"Modelo carregado: {len(self.df_clean)} músicas"
        )


state = AppState()
