
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

    feat["key_sin"] = np.sin(
        2 * np.pi * feat["key"] / 12
    )

    feat["key_cos"] = np.cos(
        2 * np.pi * feat["key"] / 12
    )

    scaler = StandardScaler()

    feat[STANDARDIZE_FEATURES] = scaler.fit_transform(
        feat[STANDARDIZE_FEATURES]
    )

    feat[BINARY_FEATURES] = (
        feat[BINARY_FEATURES] - 0.5
    )

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

    X = feature_matrix.values.astype(np.float32)

    return X, feature_matrix, scaler


def vectorize_new_song(
    song,
    scaler,
    feature_columns,
    genre_weight=GENRE_WEIGHT
):
    """
    Transforma uma música nova utilizando o mesmo
    scaler e a mesma estrutura de features do treinamento.

    Parameters
    ----------
    song : dict ou pandas.Series
        Informações da música.

    scaler : StandardScaler
        Scaler treinado pelo build_features().

    feature_columns : list
        Colunas originais da feature_matrix.

    genre_weight : float
        Peso aplicado ao gênero musical.

    Returns
    -------
    numpy.ndarray
        Vetor da música com shape (1, n_features).
    """

    song = pd.DataFrame([song])

    required_features = (
        SKEWED_FEATURES
        + STANDARDIZE_FEATURES
        + BINARY_FEATURES
        + ["key", "track_genre"]
    )

    missing_features = [
        col for col in required_features
        if col not in song.columns
    ]

    if missing_features:
        raise ValueError(
            f"Informações ausentes na música: {missing_features}"
        )

    # 1. Tratamento das variáveis assimétricas

    for col in SKEWED_FEATURES:
        song[col] = np.log1p(song[col])

    # 2. Codificação cíclica da tonalidade

    song["key_sin"] = np.sin(
        2 * np.pi * song["key"] / 12
    )

    song["key_cos"] = np.cos(
        2 * np.pi * song["key"] / 12
    )

    song[STANDARDIZE_FEATURES] = scaler.transform(
        song[STANDARDIZE_FEATURES]
    )


    song[BINARY_FEATURES] = (
        song[BINARY_FEATURES].astype(int) - 0.5
    )


    genre_dummies = pd.get_dummies(
        song["track_genre"],
        prefix="genre"
    ).astype(float) * genre_weight


    audio_feature_cols = (
        STANDARDIZE_FEATURES
        + BINARY_FEATURES
        + CYCLIC_FEATURES
    )

    feature_matrix = pd.concat(
        [
            song[audio_feature_cols],
            genre_dummies
        ],
        axis=1
    )

    feature_matrix = feature_matrix.reindex(
        columns=feature_columns,
        fill_value=0
    )


    X_new = feature_matrix.values.astype(np.float32)

    return X_new
