import {
  BadRequestException,
  Body,
  Controller,
  Delete,
  Get,
  HttpCode,
  Param,
  Patch,
  Post,
  UploadedFile,
  UseInterceptors,
} from '@nestjs/common';
import { FileInterceptor } from '@nestjs/platform-express';
import { memoryStorage } from 'multer';

import { config } from '../config';
import { CreatePlaylistDto, UpdatePlaylistDto } from './dto';
import { PlaylistView, toView } from './playlist.entity';
import { PlaylistsService } from './playlists.service';

type UploadedImage = {
  buffer: Buffer;
  mimetype: string;
  originalname: string;
  size: number;
};

@Controller('playlists')
export class PlaylistsController {
  constructor(private readonly playlists: PlaylistsService) {}

  @Get()
  findAll(): PlaylistView[] {
    return this.playlists.findAll().map(toView);
  }

  @Get(':id')
  findOne(@Param('id') id: string): PlaylistView {
    return toView(this.playlists.findOne(id));
  }

  @Post()
  create(@Body() dto: CreatePlaylistDto): PlaylistView {
    return toView(this.playlists.create(dto));
  }

  @Patch(':id')
  update(
    @Param('id') id: string,
    @Body() dto: UpdatePlaylistDto,
  ): PlaylistView {
    return toView(this.playlists.update(id, dto));
  }

  @Delete(':id')
  @HttpCode(204)
  async remove(@Param('id') id: string): Promise<void> {
    await this.playlists.remove(id);
  }

  /** Adiciona (ou troca) a capa. Campo do multipart: `file`. */
  @Post(':id/image')
  @UseInterceptors(
    FileInterceptor('file', {
      storage: memoryStorage(),
      limits: { fileSize: config.upload.maxBytes, files: 1 },
    }),
  )
  async setImage(
    @Param('id') id: string,
    @UploadedFile() file?: UploadedImage,
  ): Promise<PlaylistView> {
    if (!file) {
      throw new BadRequestException('envie a imagem no campo "file"');
    }
    const allowed: readonly string[] = config.upload.allowedMimeTypes;
    if (!allowed.includes(file.mimetype)) {
      throw new BadRequestException(
        `tipo nao suportado: ${file.mimetype} (aceitos: ${allowed.join(', ')})`,
      );
    }
    return toView(await this.playlists.setImage(id, file));
  }

  /** Remove a capa: `imageUrl` volta a ser `null`. */
  @Delete(':id/image')
  async removeImage(@Param('id') id: string): Promise<PlaylistView> {
    return toView(await this.playlists.removeImage(id));
  }
}
