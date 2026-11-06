
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity


RESULT_COLS = [
    "track_name",
    "artists",
    "track_genre",
    "popularity",
    "similarity"
]


def find_song_index(df, track_name, artist_hint=None):

    matches = df[
        df["track_name"].str.strip().str.lower()
        == track_name.strip().lower()
    ]

    if artist_hint:
        matches = matches[
            matches["artists"].str.contains(
                artist_hint.strip(),
                case=False,
                na=False,
                regex=False
            )
        ]

    if matches.empty:
        return None

    return df.index.get_loc(matches.index[0])

def recommend_songs(track_name, df, X, artist_hint=None, n=10):

    idx = find_song_index(df, track_name, artist_hint)

    if idx is None:
        return None

    similarities = cosine_similarity(
        X[idx].reshape(1, -1),
        X
    )[0]

    recommended_indices = np.argsort(-similarities)
    recommended_indices = recommended_indices[
        recommended_indices != idx
    ]

    recommended_indices = recommended_indices[:n]

    result = df.iloc[recommended_indices].copy()

    result["similarity"] = similarities[recommended_indices]

    available_cols = [
        col for col in RESULT_COLS if col in result.columns
    ]

    return result[available_cols].reset_index(drop=True)


def recommend_songs_mmr(
    track_name,
    df,
    X,
    artist_hint=None,
    n=10,
    lam=0.75,
    pool_size=100
):

    idx = find_song_index(df, track_name, artist_hint)

    if idx is None:
        return None

    similarities = cosine_similarity(
        X[idx].reshape(1, -1),
        X
    )[0]

    candidates = np.argsort(-similarities)
    candidates = candidates[candidates != idx][:pool_size]

    relevance = similarities[candidates]

    similarity_matrix = cosine_similarity(X[candidates])

    selected = []
    remaining = list(range(len(candidates)))

    while len(selected) < n and remaining:

        if not selected:
            best = max(
                remaining,
                key=lambda p: relevance[p]
            )

        else:
            best = max(
                remaining,
                key=lambda p:
                    lam * relevance[p]
                    - (1 - lam) * max(
                        similarity_matrix[p, s]
                        for s in selected
                    )
            )

        selected.append(best)
        remaining.remove(best)

    selected_indices = candidates[selected]

    result = df.iloc[selected_indices].copy()

    result["similarity"] = relevance[selected]

    available_cols = [
        col for col in RESULT_COLS if col in result.columns
    ]

    return result[available_cols].reset_index(drop=True)
