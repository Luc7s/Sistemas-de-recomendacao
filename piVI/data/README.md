# Data — pipeline de dados

Tudo que transforma o CSV bruto nos artefatos que o backend carrega no boot.

A decisão que orienta esta pasta: **tudo que é caro ou depende de rede acontece
aqui, offline.** O backend nunca chama uma API externa no caminho da
requisição — ele só lê arquivos prontos.

---

## Estrutura

```
data/
├── raw/
│   └── spotify-tracks-dataset-detailed.csv    dataset original
└── preprocess/
    ├── preprocess.py            limpeza e deduplicação
    ├── vectorize.py             → tracks.json, features.json
    ├── resolve_youtube.py       → youtube_map.json
    └── tracks_clean.csv         catálogo limpo (intermediário)
```

---

## Fluxo

```
spotify-tracks-dataset-detailed.csv
        │  preprocess.py
        ▼
tracks_clean.csv                      82.924 faixas únicas
        │
        ├─ vectorize.py ─────────────▶ tracks.json + features.json
        │
        └─ resolve_youtube.py ───────▶ youtube_map.json
```

Os três `.json` finais são **artefatos gerados** e estão no `.gitignore`.
Quem clona o repositório precisa regerá-los.

---

## 1. `preprocess.py` — limpeza

```bash
python data/preprocess/preprocess.py
```

Quatro etapas, nesta ordem:

| # | Etapa | O que remove |
|---|---|---|
| 1 | Nulos | linhas sem `track_id`, `track_name` ou `artists` |
| 2 | Áudio inválido | `tempo`, `duration_ms` ou `time_signature` zerados |
| 3 | Duplicatas de `track_id` | a mesma faixa repetida por gênero catalogado |
| 4 | Variantes | a mesma gravação em coletâneas diferentes |

Os passos 3 e 4 **não descartam informação**: antes de colapsar um grupo, os
gêneros de todas as linhas são unidos na que sobrevive (a mais popular). Uma
faixa catalogada como `dance` e como `pop` termina com ambos.

A chave do passo 4 é `track_name + artists + duration_ms`. A duração bate ao
milissegundo, o que um cover ou versão ao vivo nunca faz — por isso ela separa
"mesma gravação republicada" de "regravação".

| Flag | Efeito |
|---|---|
| `--raw CAMINHO` | outro CSV de entrada |
| `--out-dir DIR` | outro destino |
| `--keep-variants` | não executa o passo 4 |

**Saída:** `tracks_clean.csv`, 82.924 faixas, 20 colunas.

---

## 2. `vectorize.py` — vetorização

```bash
python data/preprocess/vectorize.py
```

Transforma cada faixa num vetor de **140 dimensões**, em três blocos:

| Bloco | Dims | Conteúdo | Tratamento |
|---|---|---|---|
| Áudio | 9 | `danceability`, `energy`, `valence`, `speechiness`, `acousticness`, `instrumentalness`, `liveness` | já em `[0,1]` |
| | | `loudness`, `tempo` | min-max |
| Tonal | 17 | `key` (one-hot 12), compasso (one-hot 4), modo | binário |
| Gênero | 114 | vocabulário do dataset | multi-hot |

### Por que pesos por bloco

**Cada bloco é normalizado antes de receber peso.** Sem isso os 114 gêneros
esmagariam os 9 atributos de áudio só por serem mais numerosos, e o
recomendador viraria um filtro de "mesmo gênero" — ignorando se a música é
lenta ou acelerada, triste ou animada.

Normalizar cada bloco para norma unitária antes de aplicar o peso faz o peso
significar a mesma coisa independentemente de quantas colunas o bloco tem.

| Peso | Padrão | Flag |
|---|---|---|
| Áudio | `1.0` | `--audio-weight` |
| Tonal | `0.3` | `--tonal-weight` |
| Gênero | `1.2` | `--genre-weight` |

```bash
# recomendação mais colada no gênero
python data/preprocess/vectorize.py --genre-weight 2.5

# ignorando tonalidade por completo
python data/preprocess/vectorize.py --tonal-weight 0
```

O vetor final é **L2-normalizado**, o que permite ao backend tratar
similaridade de cosseno como produto escalar puro.

| Flag | Padrão | Efeito |
|---|---|---|
| `--decimals N` | `5` | casas decimais gravadas; menos casas = arquivo menor |

**Saída:** `tracks.json` (18 MB) e `features.json` (63 MB). ~16 s.

### Formato dos artefatos

`tracks.json` — array, uma entrada por faixa:

```json
[
  {
    "track_id":    "3nqQXoyQOWXiESFLlDF1hG",
    "track_name":  "Unholy (feat. Kim Petras)",
    "artists":     "Sam Smith;Kim Petras",
    "album_name":  "Unholy (feat. Kim Petras)",
    "popularity":  100,
    "duration_ms": 156943,
    "explicit":    false,
    "genres":      ["dance", "pop"]
  }
]
```

`features.json` — matriz alinhada linha a linha com `tracks.json`:

```json
{
  "rows":          82924,
  "cols":          140,
  "normalized":    "l2",
  "feature_names": ["danceability", "energy", "...", "genre_pop"],
  "values":        [[0.31, 0.47, "..."]]
}
```

> **O alinhamento é um contrato.** A linha `i` de `values` descreve a faixa `i`
> de `tracks.json`. O backend valida isso no boot e recusa subir se as
> contagens divergirem. Sempre regere os dois juntos.

---

## 3. `resolve_youtube.py` — mapa de vídeos

Resolve `track_id → videoId` para o backend poder tocar as faixas.
Detalhes de configuração da chave em [`../../README.md`](../../README.md).

```bash
export YOUTUBE_API_KEY=...
python data/preprocess/resolve_youtube.py --limit 100
```

> **A quota é o gargalo.** A YouTube Data API dá **10.000 unidades por dia** e
> cada busca custa **100** — ou seja, **100 faixas por dia**. É exatamente por
> isso que a resolução mora aqui, offline, e não numa chamada por clique.

O script foi escrito para conviver com esse limite:

- **Retomável** — grava o progresso mesmo interrompido com Ctrl+C, e pula o que
  já resolveu numa execução anterior.
- **Ordenado por popularidade** — os primeiros dias de quota cobrem justamente
  as faixas que alguém tem chance de pedir.
- **Registra as falhas** em `misses`, para não gastar quota tentando de novo a
  mesma faixa sem vídeo.

| Flag | Padrão | Efeito |
|---|---|---|
| `--limit N` | `100` | máximo de buscas nesta execução |
| `--retry-misses` | — | tenta de novo as faixas que falharam antes |
| `--timeout S` | `10.0` | timeout por requisição |

**Saída:** `youtube_map.json`.

```json
{
  "generated_at": "2026-08-31T00:00:00Z",
  "entries": {
    "3nqQXoyQOWXiESFLlDF1hG": {
      "video_id":    "Uq9gPaIzbe8",
      "title":       "Sam Smith, Kim Petras - Unholy (Official Music Video)",
      "channel":     "Sam Smith",
      "resolved_at": "2026-08-31T00:00:00Z"
    }
  },
  "misses": {}
}
```

A busca usa **apenas o primeiro artista** — o dataset separa colaborações por
`;`, e a lista inteira na query derruba a precisão.

---

## Recriando tudo do zero

```bash
cd piVI
python data/preprocess/preprocess.py
python data/preprocess/vectorize.py
YOUTUBE_API_KEY=... python data/preprocess/resolve_youtube.py --limit 100
```

Dependências: `pandas`, `numpy`. O `resolve_youtube.py` usa só a biblioteca
padrão para HTTP.
