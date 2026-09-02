# Frontend

React + Vite + TypeScript. Duas abas: **Rádio** (busca/recomendação/player,
ainda não implementada) e **Playlists** (implementada).

---

## Rodando

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

O `vite.config.ts` faz proxy de duas APIs, então não há CORS em dev:

| Caminho no front | Vai para |
| --- | --- |
| `/nest/*` | `http://localhost:8001/api/*` — playlists (NestJS) |
| `/api/*` | `http://localhost:8000/api/*` — recomendação (Express) |

Suba o `nest-api` antes, senão a aba Playlists mostra erro ao carregar.

---

## Estrutura

```
src/
  App.tsx                        abas e roteamento por estado
  lib/api.ts                     cliente da API de playlists (NestJS)
  lib/recsysApi.ts               cliente da API de recomendação (Express)
  features/playlists/
    PlaylistsTab.tsx             lista, criação, exclusão
    PlaylistGenerator.tsx        busca uma música e gera a playlist
    PlaylistTracks.tsx           nomes das faixas, sob demanda
    PlaylistCover.tsx            capa: placeholder, adicionar, excluir
```

### Gerar playlist a partir de uma música

Um clique, três requests:

1. `GET /api/search?q=…` — a pessoa busca e escolhe a música semente.
2. `GET /api/recommend/:trackId?n=10` — dez faixas parecidas (cosseno, com
   teto de 2 por artista).
3. `POST /nest/playlists` com `trackIds` = **semente + as 10** — a playlist
   começa pela música escolhida, então tem 11 faixas.

Nasce sem capa (`imageUrl: null`); a imagem é um passo separado.

**Os nomes das faixas não são guardados na playlist.** O NestJS grava só os
ids, porque a fonte da verdade sobre faixas é o serviço de recomendação.
`PlaylistTracks` busca os nomes quando a pessoa clica em "Ver faixas" — ~10
requests paralelos a um serviço local, e uma faixa que falha aparece como
"faixa indisponível" sem derrubar a lista.

### A capa (`PlaylistCover`)

O ponto central: **`imageUrl: null` é estado normal**, não erro.

- **Sem imagem** → placeholder com a inicial do nome, e um botão
  "Adicionar imagem".
- **Com imagem** → a foto do S3, mais "Trocar imagem" e "Excluir imagem".
- O `<input type="file">` fica escondido; o botão o dispara via ref. Depois de
  cada escolha o `value` é limpo, senão escolher o mesmo arquivo de novo não
  emite `change`.
- Validação de tipo e de 5 MB acontece **no cliente e no servidor**. A do
  cliente é só para dar erro rápido; a que vale é a do NestJS.
- Todo request devolve a playlist atualizada, e `PlaylistsTab.replace()`
  substitui só aquele item no estado — sem recarregar a lista inteira.

---

## Pontos de atenção (rádio, quando for implementado)

- **`409` não é erro.** A faixa existe mas não tem vídeo mapeado; o player deve
  pular para a próxima recomendação em silêncio.
- **O `embed_url` já vem com `enablejsapi=1`**, pronto para o IFrame Player API.
- **`artists` é string**, colaborações separadas por `;` — dividir antes de
  exibir.
- **Estado do player é do cliente.** O backend só resolve ids.

---

## Pendências

- [ ] Aba Rádio: player IFrame e o laço de recomendação contínua
- [ ] Adicionar faixas manualmente a uma playlist (`PATCH /playlists/:id`)
- [ ] Editar nome e descrição
- [ ] Reordenar e remover faixas individuais
- [ ] Gerar a partir de **várias** sementes (`POST /recommend/profile`, já existe na API)
