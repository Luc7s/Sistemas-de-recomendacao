
from pathlib import Path

from src.data_loader import load_dataset
from src.preprocessing import clean_data

from src.features import (
    build_features,
    GENRE_WEIGHT,
    SKEWED_FEATURES,
    STANDARDIZE_FEATURES,
    BINARY_FEATURES,
    CYCLIC_FEATURES
)

from src.persistence import save_artifacts


MODELS_DIR = Path("models")


def main():

    print("=" * 50)
    print("MUSIC RECOMMENDATION MODEL TRAINING")
    print("=" * 50)

    # 1. Carregamento do dataset

    print("\n1. Loading dataset...")

    df = load_dataset()

    print(f"Original dataset: {df.shape}")

    # 2. Limpeza dos dados

    print("\n2. Cleaning dataset...")

    df_clean = clean_data(df)

    print(f"Clean dataset: {df_clean.shape}")

    # 3. Engenharia de características

    print("\n3. Building features...")

    X, feature_matrix, scaler = build_features(
        df_clean,
        genre_weight=GENRE_WEIGHT
    )

    print(f"Songs: {X.shape[0]}")
    print(f"Features: {X.shape[1]}")

    # 4. Configurações do modelo

    metadata = {

        "model_name": "Spotify Content-Based Recommender",

        "model_version": "1.0.0",

        "n_songs": int(len(df_clean)),

        "n_genres": int(df_clean["track_genre"].nunique()),

        "feature_dim": int(X.shape[1]),

        "feature_matrix_shape": list(X.shape),

        "genre_weight": GENRE_WEIGHT,

        "features": {

            "skewed": SKEWED_FEATURES,

            "standardize": STANDARDIZE_FEATURES,

            "binary": BINARY_FEATURES,

            "cyclic": CYCLIC_FEATURES

        },

        "transformations": {

            "skewed": "log1p",

            "scaler": "StandardScaler",

            "genre_encoding": "One-Hot Encoding",

            "key_encoding": "Sinusoidal Encoding"

        },

        "default_recommender": "mmr",

        "mmr_params": {

            "lam": 0.75,

            "pool_size": 100

        }

    }

    # 5. Salvamento dos artefatos

    print("\n4. Saving model artifacts...")

    save_artifacts(
        models_dir=MODELS_DIR,
        X=X,
        scaler=scaler,
        feature_matrix=feature_matrix,
        df_clean=df_clean,
        metadata=metadata
    )

    # 6. Finalização

    print("\n" + "=" * 50)
    print("TRAINING COMPLETED SUCCESSFULLY")
    print("=" * 50)

    print(f"Songs processed: {len(df_clean)}")
    print(f"Features generated: {X.shape[1]}")
    print(f"Model directory: {MODELS_DIR.resolve()}")


if __name__ == "__main__":
    main()
