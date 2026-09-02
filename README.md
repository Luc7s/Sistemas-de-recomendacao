# Sistema de Recomendação Musical

Recomendador de músicas *content-based* sobre um catálogo de 82.924 faixas do
Spotify, com reprodução via YouTube.

O dataset não tem usuários nem histórico de escuta, então filtragem
colaborativa está fora de questão. A recomendação vem da similaridade entre as
próprias faixas: atributos de áudio, tonalidade e gênero.

---

## Documentação

| Parte | Conteúdo |
|---|---|
| [**data/**](piVI/data/README.md) | pipeline de dados: limpeza, vetorização, mapa do YouTube |
| [**backend/**](piVI/backend/README.md) | serviço Node: como roda, como o recomendador funciona |
| [**api/**](piVI/api/README.md) | referência HTTP: rotas, parâmetros, códigos de erro |
| [**nest-api/**](piVI/nest-api/README.md) | API de playlists (NestJS): CRUD e capas no bucket S3 |
| [**frontend/**](piVI/frontend/README.md) | interface: playlists e capas prontas, player pendente |

---

## Arquitetura

```
data/raw/*.csv
      │
      │  preprocess.py        limpeza, deduplicação
      ▼
data/preprocess/tracks_clean.csv
      │
      │  vectorize.py         vetorização em 140 dimensões
      ▼
tracks.json + features.json ──────┐
                                  │
data/preprocess/youtube_map.json ─┤   (resolve_youtube.py, offline)
                                  │
                                  ▼
                          backend (Express + TypeScript)
                                  │
                          ┌───────┴────────┐
                          │                │
                    Recommender      YoutubeProvider
                  similaridade de     track_id → vídeo
                      cosseno
                                  │
                                  ▼
                            HTTP /api/*
                                  │
                                  ▼
                         frontend + IFrame Player
```

Ao lado disso, sem tocar no motor de recomendação, roda a API de playlists:

```
frontend (React + Vite)
      │
      │  /nest/playlists            multipart no upload de capa
      ▼
nest-api (NestJS, porta 8001)
      │
      └── S3 ──► devolve imageUrl (ou null, quando não há capa)
```

**Nada disso passa pelo Spotify.** As faixas vêm do dataset do Kaggle e o
áudio, quando o player entrar, vem do YouTube — por isso não há login nem
assinatura envolvidos.

Três estágios, com fronteiras nítidas:

| Estágio | Onde roda | Produz |
|---|---|---|
| **Preparação** | Python, offline | `tracks.json`, `features.json`, `youtube_map.json` |
| **Serviço** | Node, em memória | API HTTP de busca, recomendação e playback |
| **Reprodução** | Navegador | player do YouTube encadeando recomendações |

A decisão central é que **tudo que é caro ou depende de rede acontece offline**.
O backend só carrega artefatos prontos: sobe em ~1,3 s e nunca chama uma API
externa no caminho da requisição.

### Recomendação

Cada faixa vira um vetor de 140 dimensões em três blocos — áudio (9), tonal
(17) e gênero (114). Cada bloco é normalizado antes de receber peso, senão os
114 gêneros esmagariam os 9 atributos de áudio só por serem mais numerosos.

Os vetores saem L2-normalizados, então similaridade de cosseno é um produto
escalar puro. A busca é uma varredura linear (~25 ms para 82k faixas), o que
evita manter uma matriz de similaridade 82k × 82k (~27 GB) em memória.

Detalhes em [data/](piVI/data/README.md) e [backend/](piVI/backend/README.md).

---

## Por que YouTube e não Spotify

O dataset é do Spotify, mas isso não obriga a tocar pelo Spotify:

- O **Web Playback SDK exige conta Premium** — usuário free não toca nada.
- O `preview_url` de 30 s **foi removido** para apps criados após nov/2024.
- Um app em modo *development* aceita no máximo **25 usuários cadastrados** um
  a um no dashboard.

O YouTube toca a faixa completa, sem login do usuário e sem cadastro prévio.
O `track_id` do Spotify continua útil como link "abrir no Spotify".

---

## Conectando ao YouTube

### 1. Obter a chave

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2. Crie um projeto.
3. Em **APIs e serviços → Biblioteca**, ative a **YouTube Data API v3**.
4. Em **Credenciais**, crie uma **chave de API**.

### 2. Configurar

```bash
cp piVI/.env.example piVI/.env
# edite piVI/.env e cole a chave em YOUTUBE_API_KEY
```

O `.env` está no `.gitignore`.

### 3. Resolver as faixas

```bash
export YOUTUBE_API_KEY=...
python piVI/data/preprocess/resolve_youtube.py --limit 100
```

Isso gera `youtube_map.json`, o mapa `track_id → videoId` que o backend lê no
boot.

> **A quota é o gargalo.** A YouTube Data API dá **10.000 unidades por dia** e
> cada busca custa **100** — ou seja, **100 faixas por dia**. Por isso a
> resolução é offline e incremental, e não uma chamada por clique.

O script é **retomável**: guarda o progresso mesmo interrompido com Ctrl+C,
pula o que já resolveu e ordena por popularidade, então os primeiros dias de
quota cobrem justamente as faixas que alguém tem chance de pedir. Rode alguns
dias até cobrir o catálogo relevante.

### 4. Busca ao vivo (opcional)

Para faixas fora do mapa, o backend pode buscar na hora:

```bash
YOUTUBE_LIVE_FALLBACK=true
```

**Desligado por padrão.** Cada faixa não mapeada queima 100 unidades de quota,
e 100 requisições esvaziam o dia inteiro. Use só em desenvolvimento; numa
apresentação, deixe `false` e confie no mapa.

Mais detalhes em [data/](piVI/data/README.md).

---

## Executando

### Pipeline de dados (uma vez)

```bash
cd piVI
python data/preprocess/preprocess.py       # CSV bruto → tracks_clean.csv
python data/preprocess/vectorize.py        # → tracks.json + features.json
```

Os três `.json` são artefatos gerados e não vão para o git.

### Backend

```bash
cd piVI/backend
npm install
DATA_DIR=../data npm run dev
```

Ou via Docker:

```bash
cd piVI
docker compose up backend
```

> O serviço `ml` do `docker-compose.yml` aponta para `./ml`, que ainda não
> existe — suba o backend explicitamente, como acima.

Verificando:

```bash
curl "http://localhost:8000/api/health"
# {"status":"ok","tracks":82924,"dimensions":140,"playable":0,...}
```

Rotas completas em [api/](piVI/api/README.md).

---

## Estrutura

```
piVI/
├── data/          pipeline de dados (Python)
├── backend/       serviço HTTP de recomendação (Express + TypeScript)
├── nest-api/      API de playlists (NestJS + S3)
├── api/           referência das rotas
├── frontend/      interface (React + Vite)
└── docker-compose.yml
```

---

## Variáveis de ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `PORT` | `8000` | porta da API |
| `DATA_DIR` | `/app/data` | raiz dos artefatos de dados |
| `YOUTUBE_API_KEY` | — | chave da YouTube Data API v3 |
| `YOUTUBE_LIVE_FALLBACK` | `false` | busca ao vivo para faixas fora do mapa |
| `YOUTUBE_DAILY_QUOTA` | `10000` | teto diário de quota |
| `S3_BUCKET` | — | bucket das capas de playlist (`nest-api`) |
| `AWS_REGION` | `us-east-1` | região do bucket |
| `S3_PUBLIC_BASE_URL` | — | CDN na frente do bucket; vazio usa a URL da AWS |

As demais variáveis do S3 estão em [nest-api/](piVI/nest-api/README.md).

---

## Próximos passos

- [ ] Gerar playlist a partir de uma música escolhida
- [ ] Player com IFrame Player API, encadeando recomendações num rádio
      contínuo.
- [ ] Popular `youtube_map.json` além das 100 faixas iniciais.
- [ ] Definir o papel do Postgres, hoje declarado no compose mas não usado.
