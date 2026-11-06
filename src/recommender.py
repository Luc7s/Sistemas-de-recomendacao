import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from difflib import get_close_matches


RESULT_COLS = [
    "track_name",
    "artists",
    "track_genre",
    "popularity",
    "similarity"
]


def normalize_text(text):
    return " ".join(str(text).strip().lower().split())


def find_song_index(df, track_name, artist_hint=None):
    track_name = normalize_text(track_name)

    names = df["track_name"].fillna("").apply(normalize_text)

    matches = df[names == track_name]

    if artist_hint:
        artist_hint = normalize_text(artist_hint)

        matches = matches[
            df.loc[matches.index, "artists"]
            .fillna("")
            .apply(lambda artist: artist_hint in normalize_text(artist))
        ]

    if not matches.empty:
        return df.index.get_loc(matches.index[0])

    if artist_hint:
        artist_matches = df[
            df["artists"].fillna("").apply(
                lambda artist: artist_hint in normalize_text(artist)
            )
        ]

        possible_names = artist_matches["track_name"].fillna("").tolist()
    else:
        possible_names = df["track_name"].fillna("").tolist()

    normalized_names = {
        normalize_text(name): name for name in possible_names
    }

    closest = get_close_matches(
        track_name,
        list(normalized_names.keys()),
        n=1,
        cutoff=0.75
    )

    if not closest:
        return None

    corrected_name = closest[0]

    matches = df[
        df["track_name"].fillna("").apply(normalize_text) == corrected_name
    ]

    if artist_hint:
        matches = matches[
            df.loc[matches.index, "artists"]
            .fillna("")
            .apply(lambda artist: artist_hint in normalize_text(artist))
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
    ][:n]

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
            best = max(remaining, key=lambda p: relevance[p])
        else:
            best = max(
                remaining,
                key=lambda p: (
                    lam * relevance[p]
                    - (1 - lam) * max(
                        similarity_matrix[p, s]
                        for s in selected
                    )
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