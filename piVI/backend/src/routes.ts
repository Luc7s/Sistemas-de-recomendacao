import { Router } from "express";
import { z } from "zod";

import { YoutubeProvider } from "./providers/youtube.js";
import { Recommender, UnknownTrackError } from "./recommender.js";

const searchQuery = z.object({
  q: z.string().min(1, "informe o termo de busca"),
  limit: z.coerce.number().int().min(1).max(50).default(10),
});

const recommendQuery = z.object({
  n: z.coerce.number().int().min(1).max(50).default(10),
  diversify: z
    .enum(["true", "false"])
    .default("true")
    .transform((v) => v === "true"),
});

const profileBody = z.object({
  track_ids: z.array(z.string().min(1)).min(1).max(20),
  n: z.number().int().min(1).max(50).default(10),
  diversify: z.boolean().default(true),
});

export function createRoutes(
  recommender: Recommender,
  youtube: YoutubeProvider,
): Router {
  const router = Router();

  router.get("/health", (_req, res) => {
    res.json({
      status: "ok",
      tracks: recommender.size,
      dimensions: recommender.dimensions,
      playable: youtube.size,
      youtube_live_fallback: youtube.liveEnabled,
    });
  });

  router.get("/search", (req, res) => {
    const parsed = searchQuery.safeParse(req.query);
    if (!parsed.success) {
      return res.status(400).json({ error: parsed.error.issues[0]?.message });
    }
    const { q, limit } = parsed.data;
    res.json({ query: q, results: recommender.search(q, limit) });
  });

  router.get("/tracks/:trackId", (req, res) => {
    const track = recommender.getTrack(req.params.trackId);
    if (!track) return res.status(404).json({ error: "faixa nao encontrada" });
    res.json(track);
  });

  router.get("/recommend/:trackId", (req, res) => {
    const parsed = recommendQuery.safeParse(req.query);
    if (!parsed.success) {
      return res.status(400).json({ error: parsed.error.issues[0]?.message });
    }
    const { n, diversify } = parsed.data;

    try {
      const seed = recommender.getTrack(req.params.trackId);
      const results = recommender.recommend(req.params.trackId, n, diversify);
      res.json({ seed, results });
    } catch (err) {
      if (err instanceof UnknownTrackError) {
        return res.status(404).json({ error: err.message });
      }
      throw err;
    }
  });

  // Sem historico de usuario no dataset, o perfil e montado na hora a partir
  // das faixas que a pessoa escolheu na interface.
  router.post("/recommend/profile", (req, res) => {
    const parsed = profileBody.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: parsed.error.issues[0]?.message });
    }
    const { track_ids, n, diversify } = parsed.data;

    try {
      const seeds = track_ids
        .map((id) => recommender.getTrack(id))
        .filter((t) => t !== undefined);
      const results = recommender.recommendFromProfile(track_ids, n, diversify);
      res.json({ seeds, results });
    } catch (err) {
      if (err instanceof UnknownTrackError) {
        return res.status(404).json({ error: err.message });
      }
      throw err;
    }
  });

  router.get("/play/:trackId", async (req, res, next) => {
    const track = recommender.getTrack(req.params.trackId);
    if (!track) return res.status(404).json({ error: "faixa nao encontrada" });

    try {
      const source = await youtube.resolve(track);
      if (!source) {
        // 404 diria que a faixa nao existe; ela existe, so nao tem video.
        return res.status(409).json({
          error: "faixa sem video correspondente",
          track_id: track.track_id,
        });
      }
      res.json({ track, source });
    } catch (err) {
      next(err);
    }
  });

  return router;
}
