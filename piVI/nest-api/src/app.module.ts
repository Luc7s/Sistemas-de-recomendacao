import { Module } from '@nestjs/common';

import { PlaylistsModule } from './playlists/playlists.module';
import { StorageModule } from './storage/storage.module';

@Module({
  imports: [StorageModule, PlaylistsModule],
})
export class AppModule {}
