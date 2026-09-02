import { useEffect, useState } from 'react';

import { formatArtists, recsysApi, type Track } from '../../lib/recsysApi';

interface Props {
  trackIds: string[];
}

/**
 * Nomes das faixas de uma playlist.
 *
 * O NestJS guarda so os ids — a fonte da verdade sobre faixas e o servico de
 * recomendacao. Entao os nomes sao buscados aqui, sob demanda, quando a pessoa
 * abre a playlist. Sao ~10 requests a um servico local, em paralelo.
 */
export function PlaylistTracks({ trackIds }: Props) {
  const [tracks, setTracks] = useState<(Track | null)[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    Promise.all(
      // Uma faixa que sumiu do dataset nao deve derrubar a lista inteira.
      trackIds.map((id) => recsysApi.getTrack(id).catch(() => null)),
    )
      .then((loaded) => {
        if (active) setTracks(loaded);
      })
      .catch((err: unknown) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'falha ao carregar');
        }
      });

    return () => {
      active = false;
    };
  }, [trackIds]);

  if (error) return <p className="error">{error}</p>;
  if (!tracks) return <p className="muted">Carregando faixas…</p>;

  return (
    <ol className="tracks">
      {tracks.map((track, index) => (
        <li key={trackIds[index]}>
          {track ? (
            <>
              {track.track_name}
              <span className="muted"> · {formatArtists(track.artists)}</span>
            </>
          ) : (
            <span className="muted">faixa indisponível</span>
          )}
        </li>
      ))}
    </ol>
  );
}
