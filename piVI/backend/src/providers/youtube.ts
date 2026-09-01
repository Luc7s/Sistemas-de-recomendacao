import { readFile, writeFile } from "node:fs/promises";

import { config } from "../config.js";
import type { Track } from "../types/track.js";
import type {
  PlayableSource,
  YoutubeMapFile,
  YoutubeMatch,
} from "../types/youtube.js";

const SEARCH_ENDPOINT = "https://www.googleapis.com/youtube/v3/search";

const SEARCH_COST = 100;
const DAY_MS = 24 * 60 * 60 * 1000;

/**
 * Resolve faixas do catalogo para videos do YouTube.
 *
 * O caminho normal e o mapa pre-resolvido offline pelo resolve_youtube.py:
 * zero chamada externa em runtime, o que mantem a demo imune a rate limit. A
 * busca ao vivo e so rede de seguranca e fica desligada por padrao, porque a
 * quota diaria de 10.000 unidades so cobre 100 buscas.
 */
export class YoutubeProvider {
  private readonly entries: Map<string, YoutubeMatch>;
  private readonly misses: Set<string>;

  private quotaUsed = 0;
  private quotaWindowStart = Date.now();

  private dirty = false;
  private flushTimer: NodeJS.Timeout | null = null;

  private constructor(map: YoutubeMapFile) {
    this.entries = new Map(Object.entries(map.entries));
    this.misses = new Set(Object.keys(map.misses));
  }

  static async load(): Promise<YoutubeProvider> {
    try {
      const raw = await readFile(config.youtubeMapPath, "utf-8");
      return new YoutubeProvider(JSON.parse(raw) as YoutubeMapFile);
    } catch (err) {
      if ((err as NodeJS.ErrnoException).code !== "ENOENT") throw err;
      console.warn(
        `[youtube] ${config.youtubeMapPath} nao existe. Rode ` +
          `data/preprocess/resolve_youtube.py para gerar o mapa.`,
      );
      return new YoutubeProvider({
        generated_at: new Date().toISOString(),
        entries: {},
        misses: {},
      });
    }
  }

  get size(): number {
    return this.entries.size;
  }

  get liveEnabled(): boolean {
    return Boolean(config.youtubeApiKey) && config.youtubeLiveFallback;
  }

  async resolve(track: Track): Promise<PlayableSource | null> {
    const cached = this.entries.get(track.track_id);
    if (cached) return toPlayable(cached, "map");

    if (!this.liveEnabled || this.misses.has(track.track_id)) return null;

    const match = await this.searchLive(track);
    if (!match) {
      this.misses.add(track.track_id);
      return null;
    }

    this.entries.set(track.track_id, match);
    this.scheduleFlush();
    return toPlayable(match, "live");
  }

  private async searchLive(track: Track): Promise<YoutubeMatch | null> {
    if (!this.spendQuota(SEARCH_COST)) {
      console.warn("[youtube] quota diaria esgotada, busca ao vivo suspensa");
      return null;
    }

    const url = new URL(SEARCH_ENDPOINT);
    url.searchParams.set("key", config.youtubeApiKey!);
    url.searchParams.set("part", "snippet");
    url.searchParams.set("type", "video");
    url.searchParams.set("videoEmbeddable", "true");
    url.searchParams.set("maxResults", "1");
    url.searchParams.set("q", buildQuery(track));

    try {
      const res = await fetch(url, {
        signal: AbortSignal.timeout(config.youtubeTimeoutMs),
      });
      if (!res.ok) {
        console.warn(`[youtube] busca falhou (HTTP ${res.status})`);
        return null;
      }

      const body = (await res.json()) as YoutubeSearchResponse;
      const item = body.items?.[0];
      if (!item?.id?.videoId) return null;

      return {
        video_id: item.id.videoId,
        title: item.snippet?.title ?? track.track_name,
        channel: item.snippet?.channelTitle ?? "",
        resolved_at: new Date().toISOString(),
      };
    } catch (err) {
      console.warn("[youtube] busca ao vivo falhou:", (err as Error).message);
      return null;
    }
  }

  private spendQuota(cost: number): boolean {
    if (Date.now() - this.quotaWindowStart >= DAY_MS) {
      this.quotaUsed = 0;
      this.quotaWindowStart = Date.now();
    }
    if (this.quotaUsed + cost > config.youtubeDailyQuota) return false;
    this.quotaUsed += cost;
    return true;
  }

  private scheduleFlush(): void {
    this.dirty = true;
    if (this.flushTimer) return;

    this.flushTimer = setTimeout(() => {
      this.flushTimer = null;
      void this.flush();
    }, config.youtubeFlushMs);
    this.flushTimer.unref();
  }

  async flush(): Promise<void> {
    if (!this.dirty) return;
    this.dirty = false;

    const payload: YoutubeMapFile = {
      generated_at: new Date().toISOString(),
      entries: Object.fromEntries(this.entries),
      misses: Object.fromEntries([...this.misses].map((id) => [id, "live"])),
    };

    try {
      await writeFile(
        config.youtubeMapPath,
        JSON.stringify(payload, null, 2),
        "utf-8",
      );
    } catch (err) {
      // Perder o cache em disco nao justifica derrubar a API.
      this.dirty = true;
      console.warn("[youtube] nao consegui gravar o mapa:", (err as Error).message);
    }
  }
}

/** So o primeiro artista: colaboracoes inteiras na query derrubam a precisao. */
function buildQuery(track: Track): string {
  const artist = track.artists.split(";")[0]?.trim() ?? "";
  return `${track.track_name} ${artist}`.trim();
}

function toPlayable(
  match: YoutubeMatch,
  origin: "map" | "live",
): PlayableSource {
  return {
    ...match,
    provider: "youtube",
    embed_url: `https://www.youtube.com/embed/${match.video_id}?enablejsapi=1`,
    watch_url: `https://www.youtube.com/watch?v=${match.video_id}`,
    origin,
  };
}

interface YoutubeSearchResponse {
  items?: Array<{
    id?: { videoId?: string };
    snippet?: { title?: string; channelTitle?: string };
  }>;
}
