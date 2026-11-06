
from pathlib import Path

from src.persistence import load_artifacts
from src.recommender import normalize_text


BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


class AppState:
    def __init__(self):
        self.X = None
        self.scaler = None
        self.feature_columns = None
        self.df_clean = None
        self.metadata = None

        self.search_names = None
        self.search_artists = None

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

        # Normaliza os textos apenas uma vez.
        self.search_names = (
            self.df_clean["track_name"]
            .fillna("")
            .apply(normalize_text)
        )

        self.search_artists = (
            self.df_clean["artists"]
            .fillna("")
            .apply(normalize_text)
        )

        self.loaded = True

        print(
            f"Modelo carregado: {len(self.df_clean)} músicas"
        )

        print(
            f"Gêneros: {self.df_clean['track_genre'].nunique()}"
        )

        print(
            f"Características: {self.X.shape[1]}"
        )


state = AppState()
