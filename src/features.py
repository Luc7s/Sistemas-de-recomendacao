import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


GENRE_WEIGHT = 1.2

SKEWED_FEATURES = [
    "speechiness",
    "instrumentalness",
    "liveness"
]

STANDARDIZE_FEATURES = [
    "danceability",
    "energy",
    "acousticness",
    "valence",
    "loudness",
    "tempo",
    "duration_ms",
    "time_signature"
] + SKEWED_FEATURES

BINARY_FEATURES = [
    "mode",
    "explicit"
]

CYCLIC_FEATURES = [
    "key_sin",
    "key_cos"
]


def build_features(df_clean, genre_weight=GENRE_WEIGHT):
    feat = df_clean.copy()

    required_features = (
        SKEWED_FEATURES
        + STANDARDIZE_FEATURES
        + BINARY_FEATURES
        + ["key", "track_genre"]
    )

    missing_features = [
        col for col in required_features
        if col not in feat.columns
    ]

    if missing_features:
        raise ValueError(
            f"Colunas ausentes no dataset: {missing_features}"
        )

    feat["explicit"] = feat["explicit"].astype(int)

    for col in SKEWED_FEATURES:
        feat[col] = np.log1p(feat[col])

    feat["key_sin"] = np.sin(2 * np.pi * feat["key"] / 12)
    feat["key_cos"] = np.cos(2 * np.pi * feat["key"] / 12)

    scaler = StandardScaler()

    feat[STANDARDIZE_FEATURES] = scaler.fit_transform(
        feat[STANDARDIZE_FEATURES]
    )

    feat[BINARY_FEATURES] = feat[BINARY_FEATURES] - 0.5

    audio_feature_cols = (
        STANDARDIZE_FEATURES
        + BINARY_FEATURES
        + CYCLIC_FEATURES
    )

    genre_dummies = pd.get_dummies(
        feat["track_genre"],
        prefix="genre"
    ).astype(float) * genre_weight

    feature_matrix = pd.concat(
        [feat[audio_feature_cols], genre_dummies],
        axis=1
    )

    # 9. Converte para matriz NumPy
    X = feature_matrix.values.astype(np.float32)

    return X, feature_matrix, scaler
