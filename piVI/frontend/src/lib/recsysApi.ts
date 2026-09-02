/**
 * Cliente da API de recomendacao (Express, porta 8000).
 * Separada da API de playlists (NestJS) de proposito: sao dois servicos.
 */
const BASE = import.meta.env.VITE_RECSYS_URL ?? '/api';

export interface Track {
  track_id: string;
  track_name: string;
  /** String, nao array: colaboracoes separadas por `;`. */
  artists: string;
  album_name: string;
  popularity: number;
  duration_ms: number;
  explicit: boolean;
  genres: string[];
}

export interface ScoredTrack extends Track {
  similarity: number;
}

async function parse<T>(res: Response): Promise<T> {
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(body?.error ?? `erro ${res.status}`);
  }
  return body as T;
}

/** `artists` vem como string; a interface exibe separado. */
export function formatArtists(artists: string): string {
  return artists.split(';').filter(Boolean).join(', ');
}

export const recsysApi = {
  search: (q: string, limit = 8) =>
    fetch(`${BASE}/search?q=${encodeURIComponent(q)}&limit=${limit}`)
      .then(parse<{ query: string; results: Track[] }>)
      .then((body) => body.results),

  /** Faixas parecidas com a semente. A semente nunca vem nos resultados. */
  recommend: (trackId: string, n = 10) =>
    fetch(`${BASE}/recommend/${encodeURIComponent(trackId)}?n=${n}`).then(
      parse<{ seed: Track; results: ScoredTrack[] }>,
    ),

  getTrack: (trackId: string) =>
    fetch(`${BASE}/tracks/${encodeURIComponent(trackId)}`).then(parse<Track>),
};
