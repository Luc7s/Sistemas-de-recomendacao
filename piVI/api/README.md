# API — referência HTTP

Contrato das rotas expostas pelo backend. Implementação em
[`../backend/README.md`](../backend/README.md).

**Base:** `http://localhost:8000/api`
**Formato:** JSON em requisição e resposta.
**Autenticação:** nenhuma.

---

## Rotas

| Método | Rota | Descrição |
|---|---|---|
| `GET` | [`/health`](#get-health) | estado do serviço |
| `GET` | [`/search`](#get-search) | busca por nome ou artista |
| `GET` | [`/tracks/:trackId`](#get-trackstrackid) | metadados de uma faixa |
| `GET` | [`/recommend/:trackId`](#get-recommendtrackid) | faixas parecidas com uma semente |
| `POST` | [`/recommend/profile`](#post-recommendprofile) | recomendação a partir de várias sementes |
| `GET` | [`/play/:trackId`](#get-playtrackid) | resolve a faixa para um vídeo |

---

## Objetos

### `Track`

```json
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
```

`artists` é uma **string** com colaborações separadas por `;`, não um array.

### `ScoredTrack`

Um `Track` com um campo a mais:

| Campo | Tipo | Descrição |
|---|---|---|
| `similarity` | `number` | cosseno com a semente, `0`–`1`, 4 casas |

`similarity` é a similaridade **pura**. A ordem da lista segue o score final,
que também pondera popularidade — por isso os valores não vêm monotonicamente
decrescentes. Isso é esperado, não um bug.

### `PlayableSource`

```json
{
  "provider":    "youtube",
  "video_id":    "Uq9gPaIzbe8",
  "title":       "Sam Smith, Kim Petras - Unholy (Official Music Video)",
  "channel":     "Sam Smith",
  "resolved_at": "2026-08-31T00:00:00Z",
  "embed_url":   "https://www.youtube.com/embed/Uq9gPaIzbe8?enablejsapi=1",
  "watch_url":   "https://www.youtube.com/watch?v=Uq9gPaIzbe8",
  "origin":      "map"
}
```

| Campo | Valores | Descrição |
|---|---|---|
| `origin` | `map` \| `live` | mapa pré-resolvido ou busca em tempo real |
| `resolved_at` | ISO 8601 UTC | quando a faixa foi resolvida |

O `embed_url` já vem com `enablejsapi=1`, pronto para o IFrame Player API.

---

## `GET /health`

```bash
curl "http://localhost:8000/api/health"
```

```json
{
  "status": "ok",
  "tracks": 82924,
  "dimensions": 140,
  "playable": 1,
  "youtube_live_fallback": false
}
```

| Campo | Descrição |
|---|---|
| `tracks` | faixas no catálogo |
| `dimensions` | dimensões do vetor de features |
| `playable` | faixas com vídeo mapeado |
| `youtube_live_fallback` | se a busca em tempo real está ativa |

`playable: 0` significa que `youtube_map.json` não foi gerado — todo `/play`
responderá `409`.

---

## `GET /search`

| Parâmetro | Tipo | Padrão | Restrição |
|---|---|---|---|
| `q` | string | — | **obrigatório**, não vazio |
| `limit` | int | `10` | `1`–`50` |

```bash
curl "http://localhost:8000/api/search?q=Unholy&limit=2"
```

```json
{
  "query": "Unholy",
  "results": [
    { "track_id": "3nqQXoyQOWXiESFLlDF1hG", "track_name": "Unholy (feat. Kim Petras)" },
    { "track_id": "78XFPcFYN8YFOHjtVwnPsl", "track_name": "Unholy Confessions" }
  ]
}
```

Substring case-insensitive em `track_name` **e** `artists`, ordenada por
popularidade. Não há correção de digitação: "unholi" devolve lista vazia.

---

## `GET /tracks/:trackId`

```bash
curl "http://localhost:8000/api/tracks/3nqQXoyQOWXiESFLlDF1hG"
```

Devolve um `Track` sem envelope.

| Código | Situação |
|---|---|
| `200` | encontrada |
| `404` | `{ "error": "faixa nao encontrada" }` |

---

## `GET /recommend/:trackId`

| Parâmetro | Tipo | Padrão | Restrição |
|---|---|---|---|
| `n` | int | `10` | `1`–`50` |
| `diversify` | `"true"` \| `"false"` | `"true"` | teto de 2 faixas por artista |

```bash
curl "http://localhost:8000/api/recommend/3nqQXoyQOWXiESFLlDF1hG?n=3"
```

```json
{
  "seed": { "track_id": "3nqQXoyQOWXiESFLlDF1hG", "track_name": "Unholy (feat. Kim Petras)" },
  "results": [
    { "track_name": "Under The Influence", "artists": "Chris Brown",              "similarity": 0.9700 },
    { "track_name": "Havana",              "artists": "Camila Cabello;Young Thug", "similarity": 0.9900 },
    { "track_name": "You Right",           "artists": "Doja Cat;The Weeknd",       "similarity": 0.9790 }
  ]
}
```

A semente nunca aparece nos resultados.

| Código | Situação |
|---|---|
| `200` | ok |
| `400` | `n` fora de `1`–`50`, ou `diversify` inválido |
| `404` | `track_id` desconhecido |

---

## `POST /recommend/profile`

Recomendação a partir de várias sementes. Sem histórico de escuta no dataset,
o perfil é montado na hora com as faixas que a pessoa escolheu na interface.

```json
{
  "track_ids": ["3nqQXoyQOWXiESFLlDF1hG", "78XFPcFYN8YFOHjtVwnPsl"],
  "n": 10,
  "diversify": true
}
```

| Campo | Tipo | Padrão | Restrição |
|---|---|---|---|
| `track_ids` | string[] | — | **obrigatório**, 1–20 itens |
| `n` | int | `10` | `1`–`50` |
| `diversify` | bool | `true` | — |

```bash
curl -X POST "http://localhost:8000/api/recommend/profile" \
  -H "Content-Type: application/json" \
  -d '{"track_ids":["3nqQXoyQOWXiESFLlDF1hG"],"n":5}'
```

Resposta: `{ "seeds": Track[], "results": ScoredTrack[] }`.

O vetor de perfil é o **centroide** das sementes, renormalizado. Nenhuma das
sementes aparece nos resultados.

| Código | Situação |
|---|---|
| `200` | ok |
| `400` | corpo inválido |
| `404` | **nenhum** dos `track_ids` existe |

> Ids desconhecidos são **ignorados silenciosamente** se ao menos um for válido.
> Compare `seeds` com o que você enviou para detectar isso.

---

## `GET /play/:trackId`

Resolve a faixa para um vídeo do YouTube.

```bash
curl "http://localhost:8000/api/play/3nqQXoyQOWXiESFLlDF1hG"
```

```json
{
  "track":  { "track_id": "3nqQXoyQOWXiESFLlDF1hG", "track_name": "Unholy (feat. Kim Petras)" },
  "source": { "provider": "youtube", "video_id": "Uq9gPaIzbe8", "origin": "map" }
}
```

| Código | Significado | O que o cliente deve fazer |
|---|---|---|
| `200` | vídeo encontrado | tocar `source.embed_url` |
| `404` | a faixa **não existe** no catálogo | erro de verdade |
| `409` | a faixa existe, mas **não tem vídeo** | **pular para a próxima** |

A distinção entre 404 e 409 é intencional. O 409 é um estado normal — apenas
parte do catálogo está mapeada — e o cliente deve seguir a fila em silêncio, sem
mostrar erro ao usuário.

Se a resolução em tempo real estiver ativa, esta rota pode levar até **5 s** na
primeira chamada de uma faixa não mapeada. Com o mapa, responde de memória.

---

## Erros

Todo erro devolve um objeto com `error`:

```json
{ "error": "informe o termo de busca" }
```

| Código | Quando |
|---|---|
| `400` | validação de entrada (Zod); a mensagem é a do primeiro campo inválido |
| `404` | recurso ou rota inexistente |
| `409` | faixa sem vídeo |
| `500` | `{ "error": "erro interno" }` — detalhes só no log do servidor |

---

## CORS

`cors()` sem restrição de origem — qualquer site pode chamar a API.

> Adequado para desenvolvimento. **Restrinja à origem do frontend antes de
> expor publicamente.**

---

## Exemplo: rádio contínuo

O laço que o frontend deve implementar:

```js
async function tocar(trackId) {
  const res = await fetch(`/api/play/${trackId}`);

  if (res.status === 409) {              // sem vídeo: pula, não é erro
    return tocar(await proxima(trackId));
  }

  const { source } = await res.json();
  player.loadVideoById(source.video_id);
}

async function proxima(trackId) {
  const { results } = await (await fetch(`/api/recommend/${trackId}?n=1`)).json();
  return results[0].track_id;
}
```

Com `onStateChange` do IFrame Player disparando `tocar(await proxima(atual))`
no evento `ENDED`, a fila se alimenta sozinha.
