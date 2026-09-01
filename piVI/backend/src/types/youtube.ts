export interface YoutubeMatch {
  video_id: string;
  title: string;
  channel: string;
  resolved_at: string;
}

export interface YoutubeMapFile {
  generated_at: string;
  entries: Record<string, YoutubeMatch>;
  /** Guarda quem nao tem video para o resolver nao gastar quota tentando de novo. */
  misses: Record<string, string>;
}

export interface PlayableSource extends YoutubeMatch {
  provider: "youtube";
  embed_url: string;
  watch_url: string;
  origin: "map" | "live";
}
