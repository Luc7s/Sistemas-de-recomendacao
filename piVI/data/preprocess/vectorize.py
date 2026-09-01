"""
Gera os artefatos que o backend carrega no boot.

Le tracks_clean.csv e escreve tracks.json (catalogo) e features.json (matriz de
vetores L2-normalizados), alinhados linha a linha.

Uso:
    python data/preprocess/vectorize.py
    python data/preprocess/vectorize.py --genre-weight 2.0
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_CATALOG = HERE / "tracks_clean.csv"
DEFAULT_OUT = HERE

CATALOG_FIELDS = [
    "track_id",
    "track_name",
    "artists",
    "album_name",
    "popularity",
    "duration_ms",
    "explicit",
]

# Ja vem no intervalo [0, 1] do Spotify.
UNIT_FEATURES = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
]

# Escala aberta: precisa de min-max antes de entrar no vetor.
SCALED_FEATURES = ["loudness", "tempo"]

# Pesos por bloco. Sem isto os 114 generos dominariam os 9 atributos de audio
# so por serem mais numerosos, e a recomendacao viraria "mesmo genero" puro.
DEFAULT_WEIGHTS = {"audio": 1.0, "tonal": 0.3, "genre": 1.2}


def build_catalog(df):
    records = []
    for row in df.itertuples(index=False):
        records.append(
            {
                "track_id": row.track_id,
                "track_name": row.track_name,
                "artists": row.artists,
                "album_name": row.album_name,
                "popularity": int(row.popularity),
                "duration_ms": int(row.duration_ms),
                "explicit": bool(row.explicit),
                "genres": sorted(str(row.genres).split("|")),
            }
        )
    return records


def minmax(series):
    lo, hi = series.min(), series.max()
    span = hi - lo
    if span == 0:
        return np.zeros(len(series), dtype=np.float32)
    return ((series - lo) / span).to_numpy(dtype=np.float32)


def one_hot(series, values, prefix):
    matrix = np.zeros((len(series), len(values)), dtype=np.float32)
    index = {v: i for i, v in enumerate(values)}
    for row, value in enumerate(series):
        col = index.get(value)
        if col is not None:
            matrix[row, col] = 1.0
    return matrix, [f"{prefix}_{v}" for v in values]


def multi_hot_genres(series, vocabulary):
    matrix = np.zeros((len(series), len(vocabulary)), dtype=np.float32)
    index = {g: i for i, g in enumerate(vocabulary)}
    for row, raw in enumerate(series):
        for genre in str(raw).split("|"):
            col = index.get(genre)
            if col is not None:
                matrix[row, col] = 1.0
    return matrix, [f"genre_{g}" for g in vocabulary]


def normalize_rows(matrix):
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def build_block(matrix, weight):
    """Normaliza o bloco e aplica o peso, para que o peso valha o mesmo
    independente de quantas colunas o bloco tem."""
    return normalize_rows(matrix) * weight


def build_features(df, weights):
    audio = np.column_stack(
        [df[col].to_numpy(dtype=np.float32) for col in UNIT_FEATURES]
        + [minmax(df[col]) for col in SCALED_FEATURES]
    )
    audio_names = UNIT_FEATURES + SCALED_FEATURES

    key_matrix, key_names = one_hot(df["key"], list(range(12)), "key")
    sig_matrix, sig_names = one_hot(
        df["time_signature"], sorted(df["time_signature"].unique()), "time_signature"
    )
    mode = df["mode"].to_numpy(dtype=np.float32).reshape(-1, 1)
    tonal = np.hstack([key_matrix, sig_matrix, mode])
    tonal_names = key_names + sig_names + ["mode"]

    vocabulary = sorted({g for raw in df["genres"] for g in str(raw).split("|")})
    genre_matrix, genre_names = multi_hot_genres(df["genres"], vocabulary)

    matrix = np.hstack(
        [
            build_block(audio, weights["audio"]),
            build_block(tonal, weights["tonal"]),
            build_block(genre_matrix, weights["genre"]),
        ]
    )

    # O recommender assume vetores unitarios e trata cosseno como produto
    # escalar puro; a normalizacao final tem que acontecer aqui.
    matrix = normalize_rows(matrix)
    return matrix, audio_names + tonal_names + genre_names


def save_json(path, payload):
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    size_mb = path.stat().st_size / 1_000_000
    print(f"[save] {path} ({size_mb:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--out-dir", default=DEFAULT_OUT)
    parser.add_argument("--audio-weight", type=float, default=DEFAULT_WEIGHTS["audio"])
    parser.add_argument("--tonal-weight", type=float, default=DEFAULT_WEIGHTS["tonal"])
    parser.add_argument("--genre-weight", type=float, default=DEFAULT_WEIGHTS["genre"])
    parser.add_argument(
        "--decimals",
        type=int,
        default=5,
        help="casas decimais gravadas; menos casas = arquivo menor",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.catalog)
    print(f"[load] {args.catalog}: {len(df)} faixas")

    weights = {
        "audio": args.audio_weight,
        "tonal": args.tonal_weight,
        "genre": args.genre_weight,
    }
    matrix, names = build_features(df, weights)
    print(f"[build] matriz {matrix.shape[0]} x {matrix.shape[1]} | pesos {weights}")

    save_json(out_dir / "tracks.json", build_catalog(df))
    save_json(
        out_dir / "features.json",
        {
            "rows": int(matrix.shape[0]),
            "cols": int(matrix.shape[1]),
            "normalized": "l2",
            "feature_names": names,
            "values": np.round(matrix, args.decimals).tolist(),
        },
    )


if __name__ == "__main__":
    main()
