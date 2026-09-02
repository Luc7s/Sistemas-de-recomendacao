import { loadEnv } from './env';

/** Roda antes de qualquer leitura de `process.env` abaixo. */
export const envFile = loadEnv();

/**
 * Configuracao da API de playlists.
 *
 * As imagens vivem num bucket S3: o backend nunca serve bytes, so devolve a
 * URL publica do objeto. `S3_PUBLIC_BASE_URL` existe para o caso de CloudFront
 * ou de um endpoint compativel (MinIO, R2) na frente do bucket.
 */
export const config = {
  port: Number(process.env.PORT ?? 8001),

  s3: {
    // Aceita os dois nomes: `AWS_S3_BUCKET` e o padrao do console da AWS.
    bucket: process.env.S3_BUCKET ?? process.env.AWS_S3_BUCKET ?? '',
    region: process.env.AWS_REGION ?? 'us-east-1',
    /** Prefixo das chaves dentro do bucket. */
    keyPrefix: process.env.S3_KEY_PREFIX ?? 'playlists',
    /** Endpoint alternativo (MinIO/R2). Vazio = AWS. */
    endpoint: process.env.S3_ENDPOINT || undefined,
    forcePathStyle: process.env.S3_FORCE_PATH_STYLE === 'true',
    /** Base da URL publica. Vazio = monta a URL padrao da AWS. */
    publicBaseUrl: process.env.S3_PUBLIC_BASE_URL || undefined,
  },

  upload: {
    /** 5 MB. Capa de playlist nao precisa de mais que isso. */
    maxBytes: 5 * 1024 * 1024,
    allowedMimeTypes: [
      'image/jpeg',
      'image/png',
      'image/webp',
      'image/avif',
    ] as const,
  },
} as const;
