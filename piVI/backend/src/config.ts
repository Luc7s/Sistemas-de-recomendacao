import path from "node:path";

// No container o compose monta ./data em /app/data.
const DATA_DIR = process.env.DATA_DIR ?? "/app/data";
const PREPROCESS_DIR = path.join(DATA_DIR, "preprocess");

export const config = {
  port: Number(process.env.PORT ?? 8000),

  tracksPath: path.join(PREPROCESS_DIR, "tracks.json"),
  featuresPath: path.join(PREPROCESS_DIR, "features.json"),

  /** Quantos candidatos avaliar antes de diversificar e cortar. */
  candidatePool: 200,
  /** Maximo de faixas do mesmo artista numa lista de recomendacao. */
  maxPerArtist: 2,
  /** Peso da popularidade no score final (0 = so similaridade). */
  popularityWeight: 0.15,
} as const;
