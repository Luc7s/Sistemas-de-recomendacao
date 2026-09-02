import fs from "node:fs";
import path from "node:path";

/**
 * Acha a pasta `data/`.
 *
 * No container o compose monta ./data em /app/data e o cwd e /app, entao a
 * primeira tentativa resolve. Rodando local o cwd e piVI/backend, e a pasta
 * esta um nivel acima — daí a subida na arvore.
 */
function resolveDataDir(): string {
  if (process.env.DATA_DIR) return process.env.DATA_DIR;

  let dir = process.cwd();
  for (let i = 0; i < 5; i += 1) {
    const candidate = path.join(dir, "data");
    if (fs.existsSync(path.join(candidate, "preprocess"))) return candidate;
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }

  return "/app/data";
}

const DATA_DIR = resolveDataDir();
const PREPROCESS_DIR = path.join(DATA_DIR, "preprocess");

export const config = {
  port: Number(process.env.PORT ?? 8000),

  dataDir: DATA_DIR,

  tracksPath: path.join(PREPROCESS_DIR, "tracks.json"),
  featuresPath: path.join(PREPROCESS_DIR, "features.json"),

  /** Quantos candidatos avaliar antes de diversificar e cortar. */
  candidatePool: 200,
  /** Maximo de faixas do mesmo artista numa lista de recomendacao. */
  maxPerArtist: 2,
  /** Peso da popularidade no score final (0 = so similaridade). */
  popularityWeight: 0.15,

  youtubeMapPath: path.join(PREPROCESS_DIR, "youtube_map.json"),
  youtubeApiKey: process.env.YOUTUBE_API_KEY || undefined,
  /** Busca ao vivo custa 100 de quota por faixa: desligada por padrao. */
  youtubeLiveFallback: process.env.YOUTUBE_LIVE_FALLBACK === "true",
  youtubeDailyQuota: Number(process.env.YOUTUBE_DAILY_QUOTA ?? 10_000),
  youtubeTimeoutMs: 5_000,
  youtubeFlushMs: 10_000,
} as const;
