export interface Playlist {
  id: string;
  name: string;
  description: string | null;
  /** URL publica da capa no S3. `null` = playlist sem foto. */
  imageUrl: string | null;
  /** Chave do objeto no bucket, necessaria para deletar. Interna. */
  imageKey: string | null;
  trackIds: string[];
  createdAt: string;
  updatedAt: string;
}

/** Forma exposta pela API: sem a chave do bucket. */
export type PlaylistView = Omit<Playlist, 'imageKey'>;

export function toView(playlist: Playlist): PlaylistView {
  const { imageKey: _imageKey, ...view } = playlist;
  return view;
}
