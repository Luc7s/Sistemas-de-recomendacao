export interface Track {
  track_id: string;
  track_name: string;
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

/** Formato de data/preprocess/features.json. */
export interface FeaturesFile {
  rows: number;
  cols: number;
  normalized: string;
  feature_names: string[];
  values: number[][];
}
