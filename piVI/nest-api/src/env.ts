import fs from 'node:fs';
import path from 'node:path';

import dotenv from 'dotenv';

/**
 * Carrega o `.env` mais proximo, subindo a arvore a partir do cwd.
 *
 * O arquivo pode estar em `nest-api/`, em `piVI/` ou na raiz do repo — todas
 * as tres sao escolhas razoaveis, e o servico nao deveria se importar. No
 * container o compose injeta as variaveis direto, nao ha `.env`, e ai a busca
 * simplesmente nao acha nada.
 *
 * Variavel ja definida no ambiente ganha do arquivo (default do dotenv).
 */
export function loadEnv(): string | null {
  let dir = process.cwd();

  for (let i = 0; i < 5; i += 1) {
    const candidate = path.join(dir, '.env');
    if (fs.existsSync(candidate)) {
      dotenv.config({ path: candidate });
      return candidate;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }

  return null;
}
