"""
Limpeza do dataset de musicas do Spotify.

Le o CSV bruto, remove linhas invalidas e colapsa duplicatas, gerando um
catalogo com uma linha por faixa.

Uso:
    python data/preprocess/preprocess.py
    python data/preprocess/preprocess.py --raw outro.csv --out-dir /tmp/saida
"""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# Caminhos resolvidos a partir deste arquivo: roda de qualquer diretorio.
HERE = Path(__file__).resolve().parent
DEFAULT_RAW = HERE.parent / "raw" / "spotify-tracks-dataset-detailed.csv"
DEFAULT_OUT = HERE

# Colunas que sobrevivem no catalogo limpo.
CATALOG_COLUMNS = [
    "track_id",
    "track_name",
    "artists",
    "album_name",
    "popularity",
    "duration_ms",
    "explicit",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
    "genres",
]

# Valores que o Spotify usa como "nao foi possivel analisar".
INVALID_RULES = {
    "tempo": lambda s: s <= 0,
    "duration_ms": lambda s: s <= 0,
    "time_signature": lambda s: s == 0,
}

# Identifica a mesma gravacao publicada sob track_ids diferentes: a duracao
# bate ao milissegundo, o que um cover ou versao ao vivo nunca faz.
VARIANT_KEY = ["track_name", "artists", "duration_ms"]


def load_raw(path):
    df = pd.read_csv(path)
    print(f"[load] {path}: {df.shape[0]} linhas, {df.shape[1]} colunas")
    return df


def clean(df, dedup_variants=True):
    """Remove linhas invalidas e colapsa duplicatas em uma faixa por track_id."""
    n0 = len(df)

    # 1. Linhas sem identificacao textual (o dataset tem exatamente 1).
    df = df.dropna(subset=["track_id", "track_name", "artists"])
    print(f"[clean] nulos removidos: {n0 - len(df)}")

    # 2. Faixas com analise de audio invalida (tempo/duracao/compasso zerados).
    n1 = len(df)
    invalid = np.zeros(len(df), dtype=bool)
    for col, rule in INVALID_RULES.items():
        invalid |= rule(df[col])
    df = df[~invalid]
    print(f"[clean] linhas com audio invalido removidas: {n1 - len(df)}")

    # 3. A mesma faixa aparece uma vez por genero em que foi catalogada.
    #    Agregamos os generos antes de descartar, para nao perder o rotulo.
    n2 = len(df)
    df = collapse(df, ["track_id"])
    print(f"[clean] duplicatas de track_id colapsadas: {n2 - len(df)}")

    # 4. A mesma gravacao publicada em varias coletaneas, cada uma com seu
    #    track_id. Mesma agregacao de generos do passo anterior.
    if dedup_variants:
        n3 = len(df)
        df = collapse(df, VARIANT_KEY)
        print(f"[clean] variantes da mesma faixa removidas: {n3 - len(df)}")

    df = df.reset_index(drop=True)
    print(f"[clean] resultado: {len(df)} faixas unicas (de {n0})")
    return df


def collapse(df, key):
    """
    Reduz cada grupo a uma linha, unindo os generos de todas as descartadas.

    Sobrevive a linha mais popular do grupo; as features de audio sao
    identicas entre duplicatas, entao so o metadado esta em disputa.
    """
    source = "genres" if "genres" in df.columns else "track_genre"

    genres = (
        df.assign(_g=df[source].str.split("|"))
        .explode("_g")
        .groupby(key)["_g"]
        .apply(lambda s: "|".join(sorted(set(s))))
        .rename("genres")
    )

    kept = df.sort_values("popularity", ascending=False).drop_duplicates(key)
    if "genres" in kept.columns:
        kept = kept.drop(columns="genres")
    return kept.merge(genres, on=key)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", default=DEFAULT_RAW)
    parser.add_argument("--out-dir", default=DEFAULT_OUT)
    parser.add_argument(
        "--keep-variants",
        action="store_true",
        help="nao remove regravacoes com mesmo nome/artista/duracao",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_raw(args.raw)
    df = clean(df, dedup_variants=not args.keep_variants)

    out_path = out_dir / "tracks_clean.csv"
    df[CATALOG_COLUMNS].to_csv(out_path, index=False)
    print(f"[save] {out_path}")


if __name__ == "__main__":
    main()
