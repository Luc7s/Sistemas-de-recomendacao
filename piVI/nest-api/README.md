# nest-api — playlists

API **NestJS** de playlists. Separada do `backend/` (Express, recomendação) de
propósito: o motor de recomendação é stateless e carrega artefatos do
preprocess na memória; playlist é CRUD com upload de arquivo.

- Porta: **8001** (prefixo `/api`)
- Persistência: **em memória** (`PlaylistsService`) — trocar por Postgres
  depois muda só esse service.
- Imagens: **bucket S3**. O backend nunca serve bytes de imagem, só devolve a
  URL pública do objeto.

---

## Rodando

```bash
cd nest-api
npm install
npm run dev            # nest start --watch
```

Ou via compose, junto com o resto: `docker compose up nest-api`.

---

## Variáveis de ambiente

Ver `../.env.example`. As que importam:

| Variável | Efeito |
| --- | --- |
| `S3_BUCKET` | Bucket das capas. **Sem ela o upload falha com 500.** |
| `AWS_REGION` | Região do bucket (default `us-east-1`). |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | Credencial. Em EC2/ECS pode omitir e usar IAM role. |
| `S3_KEY_PREFIX` | Prefixo das chaves (default `playlists`). |
| `S3_ENDPOINT` | Endpoint compatível (MinIO, R2). Vazio = AWS. |
| `S3_FORCE_PATH_STYLE` | `true` para MinIO. |
| `S3_PUBLIC_BASE_URL` | Base da URL pública (CloudFront). Vazio = URL padrão da AWS. |

Para as URLs devolvidas serem abertas pelo navegador, os objetos precisam ser
legíveis publicamente — bucket policy de leitura no prefixo, ou CloudFront na
frente. Sem isso, o próximo passo é trocar `publicUrl()` por URL pré-assinada.

---

## Rotas

| Método | Rota | O que faz |
| --- | --- | --- |
| `GET` | `/api/playlists` | Lista, mais recentes primeiro. |
| `GET` | `/api/playlists/:id` | Uma playlist. `404` se não existe. |
| `POST` | `/api/playlists` | Cria. Body: `{ name, description?, trackIds? }`. Nasce com `imageUrl: null`. |
| `PATCH` | `/api/playlists/:id` | Atualiza nome, descrição ou faixas. |
| `DELETE` | `/api/playlists/:id` | Remove a playlist **e** a capa do bucket. `204`. |
| `POST` | `/api/playlists/:id/image` | Adiciona/troca a capa. `multipart/form-data`, campo `file`. |
| `DELETE` | `/api/playlists/:id/image` | Remove a capa: `imageUrl` volta a `null`. Idempotente. |

Upload: até **5 MB**, tipos `image/jpeg`, `image/png`, `image/webp`,
`image/avif`. Fora disso → `400`.

### Forma da resposta

```json
{
  "id": "992afd53-5554-4750-bbaa-9dec786f53fb",
  "name": "Foco",
  "description": null,
  "imageUrl": null,
  "trackIds": [],
  "createdAt": "2026-09-02T12:10:51.492Z",
  "updatedAt": "2026-09-02T12:10:51.492Z"
}
```

`imageKey` (a chave do objeto no bucket) existe na entidade mas **não é
exposta** — `toView()` a remove antes de responder.

---

## Decisões que valem saber

- **`imageUrl: null` é estado normal**, não erro. O front mostra placeholder.
- **Ordem no upload:** sobe a nova imagem, só então apaga a antiga. Se o upload
  falhar, a playlist continua com a capa que tinha.
- **Falha ao deletar do S3 não derruba a operação.** A playlist perde a capa de
  qualquer jeito; sobra no máximo um objeto órfão no bucket, que fica logado
  como warning. Uma lifecycle rule no bucket resolve o acúmulo.
- **Multer em `memoryStorage`:** o arquivo vai direto do request para o S3, sem
  tocar disco. Só funciona bem porque o limite é 5 MB.

---

## Pendências

- [ ] Postgres (Prisma) no lugar do `Map` em memória
- [ ] Autenticação — hoje qualquer um edita qualquer playlist
- [ ] URL pré-assinada, se o bucket não puder ser público
