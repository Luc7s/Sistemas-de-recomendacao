
import re

from fastapi import APIRouter, HTTPException, Query

from app.state import state
from app.schemas import (
    SongOut,
    SearchResponse,
    RecommendResponse,
    RecommendationOut,
    GenresResponse,
    HealthResponse,
)

from src.recommender import (
    normalize_text,
    recommend_songs,
    recommend_songs_mmr,
)


router = APIRouter()


RECOMMENDERS = {
    "baseline": recommend_songs,
    "mmr": recommend_songs_mmr,
}


def to_song_out(row):
    album = row.get("album_name")

    return SongOut(
        track_id=str(row.get("track_id", "")),
        track_name=str(row.get("track_name", "")),
        artists=str(row.get("artists", "")),
        track_genre=str(row.get("track_genre", "")),
        album_name=str(album) if album is not None else None,
        popularity=int(row.get("popularity", 0)),
    )


@router.get("/health", response_model=HealthResponse)
def health():

    if not state.loaded:
        return HealthResponse(status="not_loaded")

    return HealthResponse(
        status="ok",
        n_songs=len(state.df_clean),
        n_genres=state.df_clean["track_genre"].nunique(),
        default_recommender=state.metadata.get(
            "default_recommender", "mmr"
        ),
    )


@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    query = normalize_text(q)

    if not query:
        return SearchResponse(query=q, results=[])

    df = state.df_clean

    # A busca considera título e artista.
    # O artista não elimina resultados encontrados pelo título.
    title_matches = state.search_names.str.contains(
        re.escape(query),
        regex=True,
        na=False,
    )

    artist_matches = state.search_artists.str.contains(
        re.escape(query),
        regex=True,
        na=False,
    )

    results = df[title_matches | artist_matches].head(limit)

    return SearchResponse(
        query=q,
        results=[
            to_song_out(row)
            for _, row in results.iterrows()
        ],
    )


@router.get(
    "/recommend/{track_id}",
    response_model=RecommendResponse
)
def recommend(
    track_id: str,
    n: int = Query(10, ge=1, le=50),
    method: str = Query("mmr", pattern="^(mmr|baseline)$"),
):
    df = state.df_clean

    seed_rows = df[
        df["track_id"].astype(str) == track_id
    ]

    if seed_rows.empty:
        raise HTTPException(
            status_code=404,
            detail="Música não encontrada no dataset.",
        )

    seed = seed_rows.iloc[0]

    recommender = RECOMMENDERS[method]

    recommendations = recommender(
        track_name=seed["track_name"],
        df=df,
        X=state.X,
        artist_hint=seed["artists"],
        n=n,
    )

    if recommendations is None:
        raise HTTPException(
            status_code=404,
            detail="Não foi possível gerar recomendações.",
        )

    results = []

    for _, row in recommendations.iterrows():
        song = to_song_out(row)

        results.append(
            RecommendationOut(
                **song.model_dump(),
                similarity=float(row["similarity"]),
            )
        )

    return RecommendResponse(
        seed=to_song_out(seed),
        recommender=method,
        recommendations=results,
    )


@router.get("/genres", response_model=GenresResponse)
def genres():

    genres_list = sorted(
        state.df_clean["track_genre"]
        .dropna()
        .unique()
        .tolist()
    )

    return GenresResponse(genres=genres_list)
