import { readFile } from "node:fs/promises";

import { config } from "./config.js";
import type { FeaturesFile, ScoredTrack, Track } from "./types/track.js";

export class Recommender {
  private constructor(
    private readonly tracks: Track[],
    private readonly matrix: Float32Array,
    private readonly rows: number,
    private readonly cols: number,
    private readonly featureNames: string[],
    private readonly indexById: Map<string, number>,
  ) {}

  static async load(): Promise<Recommender> {
    const [tracksRaw, featuresRaw] = await Promise.all([
      readFile(config.tracksPath, "utf-8"),
      readFile(config.featuresPath, "utf-8"),
    ]);

    const tracks = JSON.parse(tracksRaw) as Track[];
    const features = JSON.parse(featuresRaw) as FeaturesFile;
    const { rows, cols } = features;

    if (tracks.length !== rows || features.values.length !== rows) {
      throw new Error(
        `Artefatos desalinhados: ${tracks.length} faixas em tracks.json, ` +
          `${features.values.length} vetores em features.json (esperado ${rows}). ` +
          `Rode o preprocess novamente.`,
      );
    }

    // O JSON vem como array de arrays; achatamos num Float32Array porque um
    // buffer contiguo deixa a varredura ~25% mais rapida e corta o heap de
    // ~146 MB para ~5 MB.
    const matrix = new Float32Array(rows * cols);
    for (let r = 0; r < rows; r++) {
      const row = features.values[r]!;
      if (row.length !== cols) {
        throw new Error(`linha ${r} tem ${row.length} valores, esperado ${cols}`);
      }
      matrix.set(row, r * cols);
    }

    const indexById = new Map(tracks.map((t, i) => [t.track_id, i]));
    return new Recommender(
      tracks,
      matrix,
      rows,
      cols,
      features.feature_names,
      indexById,
    );
  }

  get size(): number {
    return this.rows;
  }

  get dimensions(): number {
    return this.cols;
  }

  get features(): string[] {
    return this.featureNames;
  }

  getTrack(trackId: string): Track | undefined {
    const row = this.indexById.get(trackId);
    return row === undefined ? undefined : this.tracks[row];
  }

  /** Busca por nome da faixa ou do artista, ordenada por popularidade. */
  search(query: string, limit = 10): Track[] {
    const q = query.trim().toLowerCase();
    if (!q) return [];

    const hits: Track[] = [];
    for (const track of this.tracks) {
      if (
        track.track_name.toLowerCase().includes(q) ||
        track.artists.toLowerCase().includes(q)
      ) {
        hits.push(track);
      }
    }
    return hits.sort((a, b) => b.popularity - a.popularity).slice(0, limit);
  }

  /** Faixas parecidas com uma faixa semente. */
  recommend(trackId: string, n = 10, diversify = true): ScoredTrack[] {
    const row = this.indexById.get(trackId);
    if (row === undefined) throw new UnknownTrackError(trackId);

    const vector = this.matrix.subarray(row * this.cols, (row + 1) * this.cols);
    return this.neighbors(vector, n, new Set([row]), diversify);
  }

  /**
   * Faixas parecidas com um conjunto de sementes.
   *
   * Sem historico real de usuario, o centroide dos vetores das faixas
   * escolhidas funciona como um perfil de gosto aproximado.
   */
  recommendFromProfile(
    trackIds: string[],
    n = 10,
    diversify = true,
  ): ScoredTrack[] {
    const rows = trackIds
      .map((id) => this.indexById.get(id))
      .filter((row): row is number => row !== undefined);

    if (rows.length === 0) throw new UnknownTrackError(trackIds.join(", "));

    const { cols } = this;
    const centroid = new Float32Array(cols);
    for (const row of rows) {
      const offset = row * cols;
      for (let c = 0; c < cols; c++) centroid[c]! += this.matrix[offset + c]!;
    }

    // Renormaliza: a media de vetores unitarios nao e unitaria, e sem isso as
    // similaridades sairiam comprimidas.
    let norm = 0;
    for (let c = 0; c < cols; c++) norm += centroid[c]! * centroid[c]!;
    norm = Math.sqrt(norm) || 1;
    for (let c = 0; c < cols; c++) centroid[c]! /= norm;

    return this.neighbors(centroid, n, new Set(rows), diversify);
  }

  private neighbors(
    vector: Float32Array,
    n: number,
    exclude: Set<number>,
    diversify: boolean,
  ): ScoredTrack[] {
    const { rows, cols, matrix, tracks } = this;
    const { popularityWeight: w, candidatePool, maxPerArtist } = config;

    // Varredura linear: 83k x 127 leva ~25 ms e evita manter uma matriz de
    // similaridade 83k x 83k (~27 GB) em memoria.
    const scored: Array<{ row: number; similarity: number; score: number }> = [];
    for (let row = 0; row < rows; row++) {
      if (exclude.has(row)) continue;

      const offset = row * cols;
      let dot = 0;
      for (let c = 0; c < cols; c++) dot += vector[c]! * matrix[offset + c]!;

      // Mistura popularidade: similaridade pura devolve faixas obscuras que
      // ninguem reconhece.
      const popularity = tracks[row]!.popularity / 100;
      scored.push({ row, similarity: dot, score: (1 - w) * dot + w * popularity });
    }

    scored.sort((a, b) => b.score - a.score);

    const results: ScoredTrack[] = [];
    const perArtist = new Map<string, number>();
    for (const candidate of scored.slice(0, candidatePool)) {
      const track = tracks[candidate.row]!;
      if (diversify && (perArtist.get(track.artists) ?? 0) >= maxPerArtist) {
        continue;
      }
      perArtist.set(track.artists, (perArtist.get(track.artists) ?? 0) + 1);
      results.push({
        ...track,
        similarity: Number(candidate.similarity.toFixed(4)),
      });
      if (results.length === n) break;
    }
    return results;
  }
}

export class UnknownTrackError extends Error {
  constructor(public readonly trackId: string) {
    super(`track_id desconhecido: ${trackId}`);
    this.name = "UnknownTrackError";
  }
}
