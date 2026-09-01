# Frontend

> **Ainda não implementado.**

Interface de busca, recomendação e reprodução.

---

## Plano

Consome a API documentada em [`../api/README.md`](../api/README.md) e toca as
faixas com o **IFrame Player API** do YouTube.

O laço central — o "rádio contínuo":

1. Usuário busca e escolhe uma faixa (`GET /search`).
2. Resolve o vídeo (`GET /play/:trackId`) e carrega no player.
3. Ao terminar (`onStateChange` → `ENDED`), pede a próxima
   (`GET /recommend/:trackId?n=1`) e volta ao passo 2.

Esqueleto do laço em [`../api/README.md`](../api/README.md).

---

## Pontos de atenção

- **`409` não é erro.** Significa que a faixa existe mas não tem vídeo mapeado.
  O player deve pular para a próxima recomendação em silêncio.
- **O `embed_url` já vem com `enablejsapi=1`**, pronto para o IFrame Player API.
- **`artists` é string**, com colaborações separadas por `;` — dividir antes de
  exibir.
- **Estado do player é do cliente.** O backend só resolve ids; fila, play/pause
  e volume não passam por ele.

---

## Decisões pendentes

- [ ] Framework (ou HTML + JS puro)
- [ ] Como montar o perfil de gosto para `POST /recommend/profile`
- [ ] Porta de desenvolvimento e configuração de CORS no backend
