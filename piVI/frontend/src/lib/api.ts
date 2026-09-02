/** Base da API de playlists (NestJS). O proxy do Vite reescreve /nest -> /api. */
const NEST_BASE = import.meta.env.VITE_NEST_URL ?? '/nest';

export interface Playlist {
  id: string;
  name: string;
  description: string | null;
  /** `null` quando a playlist nao tem capa. */
  imageUrl: string | null;
  trackIds: string[];
  createdAt: string;
  updatedAt: string;
}

async function parse<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const message =
      (body && (body.message ?? body.error)) || `erro ${res.status}`;
    throw new Error(Array.isArray(message) ? message.join(', ') : message);
  }
  return body as T;
}

export const playlistsApi = {
  list: () => fetch(`${NEST_BASE}/playlists`).then(parse<Playlist[]>),

  create: (input: { name: string; description?: string }) =>
    fetch(`${NEST_BASE}/playlists`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
    }).then(parse<Playlist>),

  remove: (id: string) =>
    fetch(`${NEST_BASE}/playlists/${id}`, { method: 'DELETE' }).then(
      parse<void>,
    ),

  /** Adiciona ou troca a capa. O backend devolve a playlist com a URL do S3. */
  uploadImage: (id: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return fetch(`${NEST_BASE}/playlists/${id}/image`, {
      method: 'POST',
      body: form,
    }).then(parse<Playlist>);
  },

  /** Remove a capa: a playlist volta com `imageUrl: null`. */
  removeImage: (id: string) =>
    fetch(`${NEST_BASE}/playlists/${id}/image`, { method: 'DELETE' }).then(
      parse<Playlist>,
    ),
};
