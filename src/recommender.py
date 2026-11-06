

import numpy as np
import pandas as pd

import re
import unicodedata

from difflib import get_close_matches, SequenceMatcher
from sklearn.metrics.pairwise import cosine_similarity


RESULT_COLS = [
    "track_id",
    "track_name",
    "artists",
    "album_name",
    "track_genre",
    "popularity",
    "similarity"
]


def normalize_text(text):
    """
    Normaliza textos:
    - Converte para minúsculas.
    - Remove acentos.
    - Remove caracteres especiais.
    - Remove espaços extras.
    """

    text = str(text).strip().lower()

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        char for char in text
        if not unicodedata.combining(char)
    )

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return " ".join(text.split())


def find_song_index(df, track_name, artist_hint=None):
    """
    Localiza uma música priorizando o título.

    Ordem de busca:
    1. Nome exato.
    2. Nome parcial.
    3. Nome aproximado (erro de digitação).

    O artista é utilizado apenas como critério complementar.
    Um artista incorreto nunca elimina uma música encontrada.
    """

    query = normalize_text(track_name)

    if not query or "track_name" not in df.columns:
        return None

    names = (
        df["track_name"]
        .fillna("")
        .apply(normalize_text)
    )

    # Artista é um critério complementar.
    artist_query = normalize_text(artist_hint) if artist_hint else ""

    if artist_query and "artists" in df.columns:
        artists = (
            df["artists"]
            .fillna("")
            .apply(normalize_text)
        )

        artist_matches = artists.apply(
            lambda artist: artist_query in artist
        )
    else:
        artist_matches = pd.Series(
            False,
            index=df.index
        )

    # Remove títulos vazios.
    valid_names = names[names != ""]

    # Guarda os títulos únicos para evitar buscas repetidas.
    unique_names = valid_names.unique().tolist()

    if not unique_names:
        return None

    candidates = []

    # --------------------------------------------------
    # 1. BUSCA EXATA
    # --------------------------------------------------

    exact_matches = names == query

    if exact_matches.any():

        for position in np.flatnonzero(exact_matches.to_numpy()):

            candidates.append((
                3,
                1.0,
                bool(artist_matches.iloc[position]),
                position
            ))

    # --------------------------------------------------
    # 2. BUSCA PARCIAL
    # --------------------------------------------------

    else:

        partial_matches = names.str.contains(
            re.escape(query),
            regex=True,
            na=False
        )

        if partial_matches.any():

            for position in np.flatnonzero(
                partial_matches.to_numpy()
            ):

                title = names.iloc[position]

                # Quanto mais próximo do título completo,
                # maior a pontuação.
                title_score = len(query) / max(len(title), 1)

                candidates.append((
                    2,
                    title_score,
                    bool(artist_matches.iloc[position]),
                    position
                ))

    # --------------------------------------------------
    # 3. BUSCA APROXIMADA
    # --------------------------------------------------

    if not candidates and len(query) >= 4:

        similar_names = get_close_matches(
            query,
            unique_names,
            n=10,
            cutoff=0.65
        )

        for similar_name in similar_names:

            similarity = SequenceMatcher(
                None,
                query,
                similar_name
            ).ratio()

            matching_positions = np.flatnonzero(
                (names == similar_name).to_numpy()
            )

            for position in matching_positions:

                candidates.append((
                    1,
                    similarity,
                    bool(artist_matches.iloc[position]),
                    position
                ))

    # --------------------------------------------------
    # 4. ESCOLHA DO MELHOR RESULTADO
    # --------------------------------------------------

    if not candidates:
        return None

    # Primeiro prioriza a qualidade da correspondência
    # do título; depois utiliza o artista como desempate.
    best_candidate = max(
        candidates,
        key=lambda candidate: (
            candidate[0],
            candidate[1],
            candidate[2]
        )
    )

    return best_candidate[3]


def recommend_songs(track_name, df, X, artist_hint=None, n=10):

    idx = find_song_index(
        df,
        track_name,
        artist_hint
    )

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
        col for col in RESULT_COLS
        if col in result.columns
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

    idx = find_song_index(
        df,
        track_name,
        artist_hint
    )

    if idx is None:
        return None

    similarities = cosine_similarity(
        X[idx].reshape(1, -1),
        X
    )[0]

    candidates = np.argsort(-similarities)

    candidates = candidates[
        candidates != idx
    ][:pool_size]

    relevance = similarities[candidates]

    similarity_matrix = cosine_similarity(
        X[candidates]
    )

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
        col for col in RESULT_COLS
        if col in result.columns
    ]

    return result[available_cols].reset_index(drop=True)
