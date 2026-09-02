import { randomUUID } from 'node:crypto';

import { Injectable, NotFoundException } from '@nestjs/common';

import { S3Service } from '../storage/s3.service';
import { CreatePlaylistDto, UpdatePlaylistDto } from './dto';
import { Playlist } from './playlist.entity';

/**
 * Armazenamento em memoria. Serve para validar a aba e o fluxo de imagem;
 * quando entrar o Postgres, so este service muda.
 */
@Injectable()
export class PlaylistsService {
  private readonly playlists = new Map<string, Playlist>();

  constructor(private readonly s3: S3Service) {}

  findAll(): Playlist[] {
    return [...this.playlists.values()].sort((a, b) =>
      b.createdAt.localeCompare(a.createdAt),
    );
  }

  findOne(id: string): Playlist {
    const playlist = this.playlists.get(id);
    if (!playlist) {
      throw new NotFoundException('playlist nao encontrada');
    }
    return playlist;
  }

  create(dto: CreatePlaylistDto): Playlist {
    const now = new Date().toISOString();
    const playlist: Playlist = {
      id: randomUUID(),
      name: dto.name.trim(),
      description: dto.description?.trim() || null,
      // Playlist nasce sem capa; a imagem e um passo separado.
      imageUrl: null,
      imageKey: null,
      trackIds: dto.trackIds ?? [],
      createdAt: now,
      updatedAt: now,
    };
    this.playlists.set(playlist.id, playlist);
    return playlist;
  }

  update(id: string, dto: UpdatePlaylistDto): Playlist {
    const playlist = this.findOne(id);
    if (dto.name !== undefined) playlist.name = dto.name.trim();
    if (dto.description !== undefined) {
      playlist.description = dto.description.trim() || null;
    }
    if (dto.trackIds !== undefined) playlist.trackIds = dto.trackIds;
    playlist.updatedAt = new Date().toISOString();
    return playlist;
  }

  async remove(id: string): Promise<void> {
    const playlist = this.findOne(id);
    if (playlist.imageKey) {
      await this.s3.remove(playlist.imageKey);
    }
    this.playlists.delete(id);
  }

  /**
   * Sobe a nova capa e apaga a anterior. A ordem importa: se o upload falhar,
   * a playlist continua com a imagem que tinha.
   */
  async setImage(
    id: string,
    file: { buffer: Buffer; mimetype: string; originalname: string },
  ): Promise<Playlist> {
    const playlist = this.findOne(id);
    const previousKey = playlist.imageKey;

    const stored = await this.s3.upload(file);
    playlist.imageUrl = stored.url;
    playlist.imageKey = stored.key;
    playlist.updatedAt = new Date().toISOString();

    if (previousKey && previousKey !== stored.key) {
      await this.s3.remove(previousKey);
    }

    return playlist;
  }

  /** Volta a capa para `null` e remove o objeto do bucket. Idempotente. */
  async removeImage(id: string): Promise<Playlist> {
    const playlist = this.findOne(id);
    const key = playlist.imageKey;

    playlist.imageUrl = null;
    playlist.imageKey = null;
    playlist.updatedAt = new Date().toISOString();

    if (key) {
      await this.s3.remove(key);
    }

    return playlist;
  }
}
