import 'reflect-metadata';

import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';

import { AppModule } from './app.module';
import { config, envFile } from './config';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.enableCors();
  app.setGlobalPrefix('api');
  app.useGlobalPipes(
    new ValidationPipe({ whitelist: true, transform: true }),
  );

  console.log(
    envFile ? `[boot] .env carregado de ${envFile}` : '[boot] sem .env; usando o ambiente',
  );
  if (!config.s3.bucket) {
    console.warn(
      '[boot] S3_BUCKET nao definido: playlists funcionam, mas o upload de ' +
        'capa responde 503. Ver nest-api/README.md.',
    );
  }

  await app.listen(config.port);
  console.log(`[boot] nest-api ouvindo em http://localhost:${config.port}/api`);
}

bootstrap().catch((err) => {
  console.error('[fatal]', err);
  process.exit(1);
});
