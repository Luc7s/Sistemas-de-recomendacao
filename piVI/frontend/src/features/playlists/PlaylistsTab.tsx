import { useCallback, useEffect, useState } from 'react';

import { playlistsApi, type Playlist } from '../../lib/api';
import { PlaylistCover } from './PlaylistCover';
import { PlaylistGenerator } from './PlaylistGenerator';
import { PlaylistTracks } from './PlaylistTracks';

export function PlaylistsTab() {
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState('');
  const [creating, setCreating] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setPlaylists(await playlistsApi.list());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'falha ao carregar');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  /** Troca uma playlist no estado sem recarregar a lista inteira. */
  function replace(updated: Playlist) {
    setPlaylists((current) =>
      current.map((p) => (p.id === updated.id ? updated : p)),
    );
  }

  async function handleCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;

    setCreating(true);
    try {
      const created = await playlistsApi.create({ name: name.trim() });
      setPlaylists((current) => [created, ...current]);
      setName('');
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'falha ao criar');
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await playlistsApi.remove(id);
      setPlaylists((current) => current.filter((p) => p.id !== id));
      if (openId === id) setOpenId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'falha ao excluir');
    }
  }

  return (
    <section>
      <h2>Playlists</h2>

      <PlaylistGenerator
        onGenerated={(playlist) => {
          setPlaylists((current) => [playlist, ...current]);
          // Ja abre as faixas: a pessoa quer ver o que foi gerado.
          setOpenId(playlist.id);
        }}
      />

      <h3>Criar vazia</h3>
      <form className="create" onSubmit={handleCreate}>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Nome da nova playlist"
          maxLength={120}
          aria-label="Nome da nova playlist"
        />
        <button type="submit" disabled={creating || !name.trim()}>
          Criar
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {loading ? (
        <p className="muted">Carregando…</p>
      ) : playlists.length === 0 ? (
        <p className="muted">Nenhuma playlist ainda.</p>
      ) : (
        <ul className="playlists">
          {playlists.map((playlist) => (
            <li key={playlist.id} className="playlist">
              <PlaylistCover
                imageUrl={playlist.imageUrl}
                name={playlist.name}
                onSelectFile={async (file) =>
                  replace(await playlistsApi.uploadImage(playlist.id, file))
                }
                onRemoveImage={async () =>
                  replace(await playlistsApi.removeImage(playlist.id))
                }
              />
              <div className="playlist__info">
                <h3>{playlist.name}</h3>
                <p className="muted">
                  {playlist.trackIds.length} faixa
                  {playlist.trackIds.length === 1 ? '' : 's'}
                  {playlist.imageUrl ? '' : ' · sem capa'}
                </p>
                <div className="playlist__buttons">
                  {playlist.trackIds.length > 0 && (
                    <button
                      type="button"
                      aria-expanded={openId === playlist.id}
                      onClick={() =>
                        setOpenId(openId === playlist.id ? null : playlist.id)
                      }
                    >
                      {openId === playlist.id ? 'Ocultar faixas' : 'Ver faixas'}
                    </button>
                  )}
                  <button
                    type="button"
                    className="danger"
                    onClick={() => void handleDelete(playlist.id)}
                  >
                    Excluir playlist
                  </button>
                </div>

                {openId === playlist.id && (
                  <PlaylistTracks trackIds={playlist.trackIds} />
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
