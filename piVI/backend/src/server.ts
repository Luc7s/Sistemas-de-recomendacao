import cors from "cors";
import express from "express";

import { config } from "./config.js";
import { YoutubeProvider } from "./providers/youtube.js";
import { Recommender } from "./recommender.js";
import { createRoutes } from "./routes.js";

async function main() {
  console.log("[boot] carregando artefatos do preprocess...");
  const started = Date.now();
  const [recommender, youtube] = await Promise.all([
    Recommender.load(),
    YoutubeProvider.load(),
  ]);
  console.log(
    `[boot] ${recommender.size} faixas, ${recommender.dimensions} dimensoes ` +
      `(${Date.now() - started} ms)`,
  );
  console.log(`[boot] ${youtube.size} faixas com video mapeado`);

  const app = express();
  app.use(cors());
  app.use(express.json());
  app.use("/api", createRoutes(recommender, youtube));

  app.use((_req, res) => res.status(404).json({ error: "rota nao encontrada" }));

  app.use(
    (
      err: Error,
      _req: express.Request,
      res: express.Response,
      _next: express.NextFunction,
    ) => {
      console.error("[erro]", err);
      res.status(500).json({ error: "erro interno" });
    },
  );

  app.listen(config.port, () => {
    console.log(`[boot] API ouvindo em http://localhost:${config.port}/api`);
  });
}

main().catch((err) => {
  console.error("[fatal]", err);
  process.exit(1);
});
