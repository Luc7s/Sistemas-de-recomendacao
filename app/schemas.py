
from typing import Optional
from pydantic import BaseModel


class SongOut(BaseModel):
    track_id: str
    track_name: str
    artists: str
    track_genre: str
    album_name: Optional[str] = None
    popularity: int = 0


class SearchResponse(BaseModel):
    query: str
    results: list[SongOut]


class RecommendationOut(SongOut):
    similarity: float


class RecommendResponse(BaseModel):
    seed: SongOut
    recommender: str
    recommendations: list[RecommendationOut]


class GenresResponse(BaseModel):
    genres: list[str]


class HealthResponse(BaseModel):
    status: str
    n_songs: Optional[int] = None
    n_genres: Optional[int] = None
    default_recommender: Optional[str] = None
