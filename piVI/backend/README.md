# Backend

Serviço HTTP que carrega os artefatos do pipeline e responde busca,
recomendação e resolução de playback.

Referência das rotas: [`../api/README.md`](../api/README.md).

**Stack:** Node 22 · TypeScript · Express 5 · Zod

---

## Executando

```bash
npm install
DATA_DIR=../data npm run dev
```

```
[boot] carregando artefatos do preprocess...
[boot] 82924 faixas, 140 dimensoes (1278 ms)
[boot] 0 faixas com video mapeado
[boot] API ouvindo em http://localhost:8000/api
```

Se aparecer erro de arquivo inexistente, os artefatos ainda não foram gerados —
veja [`../data/README.md`](../data/README.md).

| Script | Efeito |
|---|---|
| `npm run dev` | tsx com watch |
| `npm run build` | compila para `dist/` |
| `npm start` | roda o build |
| `npm run typecheck` | `tsc --noEmit` |

### Docker

```bash
cd ..
docker compose up backend
```

> O serviço `ml` do `docker-compose.yml` aponta para `./ml`, que ainda não
> existe. Suba o backend explicitamente, como acima.

---

## Estrutura

```
src/
├── server.ts              bootstrap: carrega artefatos, monta o Express
├── routes.ts              rotas e validação de entrada (Zod)
├── recommender.ts         similaridade de cosseno
├── config.ts              configuração e variáveis de ambiente
├── providers/
│   └── youtube.ts         resolução track_id → vídeo
└── types/
    ├── track.ts           Track, ScoredTrack, FeaturesFile
    └── youtube.ts         YoutubeMatch, YoutubeMapFile, PlayableSource
```

---

## Boot

O servidor carrega **tudo em memória antes de aceitar conexões**, em paralelo:

```ts
const [recommender, youtube] = await Promise.all([
  Recommender.load(),
  YoutubeProvider.load(),
]);
```

Isso troca ~1,3 s de partida por latência previsível em toda requisição — não
há I/O de disco nem chamada de rede no caminho quente.

`Recommender.load()` **recusa subir** se `tracks.json` e `features.json`
tiverem contagens diferentes. Artefatos desalinhados produziriam recomendações
silenciosamente erradas (a faixa `i` descrita pelo vetor de outra), e falhar
alto no boot é muito melhor do que servir lixo plausível.

`YoutubeProvider.load()` **não** falha se o mapa não existir: emite um aviso e
segue com zero faixas tocáveis. Playback é um recurso opcional; a recomendação
funciona sem ele.

---

## `Recommender`

Recomendador *content-based*: sem usuários no dataset, a similaridade é entre
as próprias faixas.

### Representação em memória

A matriz 82.924 × 140 é achatada num `Float32Array` contíguo em vez de um array
de arrays. A varredura fica ~25% mais rápida e o heap cai de **~146 MB para
~5 MB**.

```
linha r ocupa [r*cols, r*cols + cols)
```

### Busca

Varredura linear sobre as 82.924 faixas, ~25 ms. A alternativa — pré-computar
uma matriz de similaridade — exigiria 82k × 82k ≈ **27 GB**. Para este volume,
força bruta ganha por larga margem em simplicidade e memória.

Como os vetores chegam L2-normalizados do `vectorize.py`, a similaridade de
cosseno é um **produto escalar puro**, sem divisão por normas.

### Score e diversificação

```
score = (1 - w) * similaridade + w * (popularidade / 100)      w = 0.15
```

Similaridade pura devolve faixas obscuras que ninguém reconhece, o que faz a
recomendação **parecer** quebrada mesmo estando matematicamente correta. Os 15%
de popularidade compram reconhecimento sem descaracterizar o resultado.

Depois disso, no máximo **2 faixas do mesmo artista** por lista — senão uma
semente de um artista prolífico devolve só o álbum dele.

### Perfil

`recommendFromProfile()` monta o **centroide** dos vetores das faixas
escolhidas. Sem histórico real de escuta, é a aproximação disponível de "gosto".

O centroide é **renormalizado**: a média de vetores unitários não é unitária, e
sem isso as similaridades sairiam comprimidas.

---

## `YoutubeProvider`

Resolve `track_id → vídeo`. Ver [`../data/README.md`](../data/README.md) para
como o mapa é gerado.

### Ordem de resolução

1. **Mapa em memória** — carregado no boot, custo zero.
2. **Miss conhecido** — devolve `null` sem tentar de novo.
3. **Busca ao vivo** — só se `YOUTUBE_LIVE_FALLBACK=true` e houver chave.

A busca ao vivo é **desligada por padrão**: cada faixa não mapeada queima 100
unidades de quota, e 100 requisições esvaziam o dia inteiro. Ela existe como
rede de segurança em desenvolvimento, não como caminho normal.

### Proteções da busca ao vivo

| Proteção | Como |
|---|---|
| Timeout | `AbortSignal.timeout(5s)` — uma busca lenta não pode segurar a requisição do Express |
| Orçamento | contador de quota em memória, janela de 24 h |
| Persistência | resultados novos são gravados no mapa, agrupados numa janela de 10 s |
| Falha isolada | erro de rede vira `null` e log, nunca 500 |

A gravação do mapa é *debounced* porque o arquivo tem uma entrada por faixa —
reescrevê-lo a cada resolução seria desperdício. Se a gravação falhar, o mapa em
memória continua válido: perder o cache em disco não justifica derrubar a API.

---

## Configuração

Tudo em `src/config.ts`.

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `8000` | porta da API |
| `DATA_DIR` | `/app/data` | raiz dos artefatos (`../data` fora do Docker) |
| `YOUTUBE_API_KEY` | — | chave da YouTube Data API v3 |
| `YOUTUBE_LIVE_FALLBACK` | `false` | busca ao vivo para faixas fora do mapa |
| `YOUTUBE_DAILY_QUOTA` | `10000` | teto diário de quota |

Constantes de tuning, sem variável de ambiente:

| Constante | Valor | Efeito |
|---|---|---|
| `candidatePool` | `200` | candidatos avaliados antes de diversificar |
| `maxPerArtist` | `2` | teto de faixas do mesmo artista por lista |
| `popularityWeight` | `0.15` | peso da popularidade no score |
| `youtubeTimeoutMs` | `5000` | timeout da busca ao vivo |
| `youtubeFlushMs` | `10000` | janela de agrupamento antes de gravar o mapa |

---

## Convenções

- **ESM nativo.** `"type": "module"`, `moduleResolution: NodeNext` — imports
  relativos precisam da extensão `.js`, mesmo apontando para um `.ts`.
- **`strict` + `noUncheckedIndexedAccess`.** Acesso indexado devolve
  `T | undefined`; daí os `!` ao varrer arrays cujo tamanho já foi validado.
- **Validação na borda.** Todo input de rota passa por um schema Zod em
  `routes.ts`; o resto do código assume dados válidos.
- **Comentários registram decisão, não mecânica.** Se o comentário explica o que
  o código já diz, ele sai.
