"""
Resolve faixas do catalogo para videos do YouTube.

Gera youtube_map.json, consumido pelo backend em GET /api/play/:trackId.

Uso:
    export YOUTUBE_API_KEY=...
    python data/preprocess/resolve_youtube.py --limit 90
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_CATALOG = HERE / "tracks_clean.csv"
DEFAULT_MAP = HERE / "youtube_map.json"

SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search"
SEARCH_COST = 100
DAILY_QUOTA = 10_000


def load_map(path):
    if not path.exists():
        return {"generated_at": None, "entries": {}, "misses": {}}
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_map(path, data):
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def build_query(row):
    # So o primeiro artista: colaboracoes inteiras na query derrubam a precisao.
    artist = str(row["artists"]).split(";")[0].strip()
    return f"{row['track_name']} {artist}".strip()


def search(api_key, query, timeout):
    params = urllib.parse.urlencode(
        {
            "key": api_key,
            "part": "snippet",
            "type": "video",
            "videoEmbeddable": "true",
            "maxResults": 1,
            "q": query,
        }
    )
    url = f"{SEARCH_ENDPOINT}?{params}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as res:
            body = json.load(res)
    except urllib.error.HTTPError as err:
        if err.code == 403:
            raise QuotaExceeded() from err
        print(f"[erro] HTTP {err.code} em '{query}'")
        return None
    except (urllib.error.URLError, TimeoutError) as err:
        print(f"[erro] falha de rede em '{query}': {err}")
        return None

    items = body.get("items") or []
    if not items:
        return None

    item = items[0]
    video_id = item.get("id", {}).get("videoId")
    if not video_id:
        return None

    snippet = item.get("snippet", {})
    return {
        "video_id": video_id,
        "title": snippet.get("title", ""),
        "channel": snippet.get("channelTitle", ""),
        "resolved_at": datetime.now(timezone.utc).isoformat(),
    }


class QuotaExceeded(Exception):
    pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--out", default=DEFAULT_MAP)
    parser.add_argument(
        "--limit",
        type=int,
        default=DAILY_QUOTA // SEARCH_COST,
        help="maximo de buscas nesta execucao (quota diaria / 100)",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--retry-misses",
        action="store_true",
        help="tenta de novo as faixas que ja falharam",
    )
    args = parser.parse_args()

    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        sys.exit("[fatal] defina YOUTUBE_API_KEY")

    out_path = Path(args.out)
    data = load_map(out_path)
    entries, misses = data["entries"], data["misses"]

    if args.retry_misses:
        misses.clear()

    df = pd.read_csv(args.catalog)
    # Ordena por popularidade: com quota para ~100 faixas por dia, as que o
    # usuario tem chance de pedir precisam entrar no mapa primeiro.
    df = df.sort_values("popularity", ascending=False)

    pending = df[~df["track_id"].isin(set(entries) | set(misses))]
    print(f"[plan] {len(entries)} resolvidas, {len(pending)} pendentes")

    resolved = failed = 0
    try:
        for _, row in pending.head(args.limit).iterrows():
            track_id = row["track_id"]
            match = search(api_key, build_query(row), args.timeout)
            if match:
                entries[track_id] = match
                resolved += 1
                print(f"[ok] {row['track_name']} -> {match['video_id']}")
            else:
                misses[track_id] = build_query(row)
                failed += 1
    except QuotaExceeded:
        print("[quota] limite diario atingido, parando")
    except KeyboardInterrupt:
        print("\n[stop] interrompido")
    finally:
        # Grava sempre: o progresso de uma execucao interrompida nao pode ser
        # perdido, ou a quota do dia vai embora sem resultado.
        save_map(out_path, data)
        print(f"[save] {out_path}: +{resolved} resolvidas, +{failed} sem video")
        print(f"[save] total {len(entries)} faixas tocaveis")


if __name__ == "__main__":
    main()
