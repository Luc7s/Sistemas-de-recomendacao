import { randomUUID } from 'node:crypto';
import path from 'node:path';

import {
  DeleteObjectCommand,
  PutObjectCommand,
  S3Client,
} from '@aws-sdk/client-s3';
import {
  Injectable,
  Logger,
  ServiceUnavailableException,
} from '@nestjs/common';

import { config } from '../config';

export interface StoredImage {
  key: string;
  url: string;
}

@Injectable()
export class S3Service {
  private readonly logger = new Logger(S3Service.name);
  private readonly client = new S3Client({
    region: config.s3.region,
    endpoint: config.s3.endpoint,
    forcePathStyle: config.s3.forcePathStyle,
  });

  /** `true` quando o bucket esta configurado. */
  get configured(): boolean {
    return config.s3.bucket.length > 0;
  }

  /** Sobe o arquivo e devolve a chave + a URL publica. */
  async upload(file: {
    buffer: Buffer;
    mimetype: string;
    originalname: string;
  }): Promise<StoredImage> {
    if (!this.configured) {
      // 503, nao 500: o pedido esta certo, falta configurar o servidor.
      throw new ServiceUnavailableException(
        'upload de imagem indisponivel: defina S3_BUCKET no .env ' +
          '(ver nest-api/README.md)',
      );
    }

    const ext = path.extname(file.originalname).toLowerCase() || '.jpg';
    const key = `${config.s3.keyPrefix}/${randomUUID()}${ext}`;

    try {
      await this.client.send(
        new PutObjectCommand({
          Bucket: config.s3.bucket,
          Key: key,
          Body: file.buffer,
          ContentType: file.mimetype,
          CacheControl: 'public, max-age=31536000, immutable',
        }),
      );
    } catch (err) {
      throw new ServiceUnavailableException(this.explain(err));
    }

    return { key, url: this.publicUrl(key) };
  }

  /**
   * Traduz o erro do SDK para algo acionavel. As tres falhas de configuracao
   * mais comuns tem mensagens propias; o resto vai cru, mas logado.
   */
  private explain(err: unknown): string {
    const name = err instanceof Error ? err.name : '';
    this.logger.error(`falha no upload para o S3: ${String(err)}`);

    if (name === 'CredentialsProviderError') {
      return 'sem credencial da AWS: defina AWS_ACCESS_KEY_ID e ' +
        'AWS_SECRET_ACCESS_KEY no .env, ou use uma IAM role';
    }
    if (name === 'NoSuchBucket') {
      return `bucket "${config.s3.bucket}" nao existe na regiao ${config.s3.region}`;
    }
    if (name === 'AccessDenied') {
      return 'credencial sem permissao de s3:PutObject nesse bucket';
    }
    return `falha ao enviar a imagem para o S3: ${name || 'erro desconhecido'}`;
  }

  /**
   * Remove o objeto. Um erro aqui nao deve derrubar a operacao de negocio: a
   * playlist perde a capa de qualquer jeito, so fica um objeto orfao no bucket.
   */
  async remove(key: string): Promise<void> {
    if (!this.configured) return;
    try {
      await this.client.send(
        new DeleteObjectCommand({ Bucket: config.s3.bucket, Key: key }),
      );
    } catch (err) {
      this.logger.warn(`falha ao remover ${key} do bucket: ${String(err)}`);
    }
  }

  private publicUrl(key: string): string {
    if (config.s3.publicBaseUrl) {
      return `${config.s3.publicBaseUrl.replace(/\/$/, '')}/${key}`;
    }
    return `https://${config.s3.bucket}.s3.${config.s3.region}.amazonaws.com/${key}`;
  }
}
