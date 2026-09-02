import { useState } from 'react';

import { playlistsApi, type Playlist } from '../../lib/api';
import { formatArtists, recsysApi, type Track } from '../../lib/recsysApi';

interface Props {
  /** Chamado com a playlist recem-criada, para entrar na lista. */
  onGenerated: (playlist: Playlist) => void;
}

/** Quantas faixas a playlist gerada tem. */
const PLAYLIST_SIZE = 10;

/**
 * Busca uma musica e gera uma playlist a partir dela: um clique dispara
 * `GET /recommend/:trackId?n=10` e cria a playlist com os ids devolvidos.
 */
export function PlaylistGenerator({ onGenerated }: Props) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Track[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [generatingId, setGeneratingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(event: React.FormEvent) {
    event.preventDefault();
    if (!query.trim()) return;

    setSearching(true);
    setError(null);
    try {
      setResults(await recsysApi.search(query.trim()));
    } catch (err) {
      setError(
        err instanceof Error
          ? `${err.message} (a API de recomendação está no ar?)`
          : 'falha na busca',
      );
    } finally {
      setSearching(false);
    }
  }

  async function handleGenerate(seed: Track) {
    setGeneratingId(seed.track_id);
    setError(null);
    try {
      const { results: recommended } = await recsysApi.recommend(
        seed.track_id,
        PLAYLIST_SIZE,
      );
      // A semente entra na frente: a playlist começa pela música escolhida.
      const trackIds = [
        seed.track_id,
        ...recommended.map((track) => track.track_id),
      ];
      const playlist = await playlistsApi.create({
        name: `Baseado em ${seed.track_name}`,
        description: `Gerada a partir de ${seed.track_name} — ${formatArtists(seed.artists)}`,
        trackIds,
      });
      onGenerated(playlist);
      // Limpa a busca: a playlist já apareceu na lista abaixo.
      setResults(null);
      setQuery('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'falha ao gerar');
    } finally {
      setGeneratingId(null);
    }
  }

  return (
    <div className="generator">
      <h3>Gerar a partir de uma música</h3>

      <form className="create" onSubmit={handleSearch}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar música ou artista"
          aria-label="Buscar música ou artista"
        />
        <button type="submit" disabled={searching || !query.trim()}>
          {searching ? 'Buscando…' : 'Buscar'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {results !== null &&
        (results.length === 0 ? (
          <p className="muted">Nenhuma faixa encontrada.</p>
        ) : (
          <ul className="results">
            {results.map((track) => (
              <li key={track.track_id}>
                <div>
                  <strong>{track.track_name}</strong>
                  <span className="muted"> · {formatArtists(track.artists)}</span>
                </div>
                <button
                  type="button"
                  disabled={generatingId !== null}
                  onClick={() => void handleGenerate(track)}
                >
                  {generatingId === track.track_id
                    ? 'Gerando…'
                    : `Gerar playlist (${PLAYLIST_SIZE})`}
                </button>
              </li>
            ))}
          </ul>
        ))}
    </div>
  );
}
