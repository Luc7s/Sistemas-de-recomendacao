# Frontend

React + Vite + TypeScript. Duas abas: **Rádio** (busca/recomendação/player,
ainda não implementada) e **Playlists**, onde dá para criar playlists e
gerenciar a capa de cada uma.

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
  features/playlists/
    PlaylistsTab.tsx             lista, criação, exclusão
    PlaylistCover.tsx            capa: placeholder, adicionar, excluir
```

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

- [ ] Gerar a playlist a partir de uma música escolhida
- [ ] Aba Rádio: player IFrame e o laço de recomendação contínua
- [ ] Editar nome e descrição
