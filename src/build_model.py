
from src.data_loader import load_dataset
from src.preprocessing import clean_data
from src.features import build_features, GENRE_WEIGHT
from src.persistence import save_artifacts


def main():

    print("1. Loading dataset")

    df = load_dataset()

    print(f"Dataset: {df.shape}")

    print("\n2. Cleaning data")

    df_clean = clean_data(df)

    print("\n3. Building features")

    X, feature_matrix, scaler = build_features(
        df_clean,
        genre_weight=GENRE_WEIGHT
    )

    print(f"Songs: {X.shape[0]}")
    print(f"Features: {X.shape[1]}")

    metadata = {
        "n_songs": int(len(df_clean)),
        "n_genres": int(df_clean["track_genre"].nunique()),
        "feature_dim": int(X.shape[1]),
        "genre_weight": GENRE_WEIGHT,
        "default_recommender": "mmr",
        "mmr_params": {
            "lam": 0.75,
            "pool_size": 100
        }
    }

    print("\n4. Saving model")

    save_artifacts(
        "models",
        X,
        scaler,
        feature_matrix,
        df_clean,
        metadata
    )

    print("\nTraining completed!")


if __name__ == "__main__":
    main()
