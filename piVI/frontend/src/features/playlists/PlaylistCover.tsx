import { useRef, useState } from 'react';

interface Props {
  imageUrl: string | null;
  name: string;
  onSelectFile: (file: File) => Promise<void>;
  onRemoveImage: () => Promise<void>;
}

const MAX_BYTES = 5 * 1024 * 1024;
const ACCEPTED = ['image/jpeg', 'image/png', 'image/webp', 'image/avif'];

/**
 * Capa da playlist. Sem imagem mostra o placeholder com a inicial do nome —
 * `imageUrl: null` e estado normal, nao erro.
 */
export function PlaylistCover({
  imageUrl,
  name,
  onSelectFile,
  onRemoveImage,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    // Limpa o input para permitir escolher o mesmo arquivo de novo.
    event.target.value = '';
    if (!file) return;

    if (!ACCEPTED.includes(file.type)) {
      setError('formato não suportado (use JPEG, PNG, WebP ou AVIF)');
      return;
    }
    if (file.size > MAX_BYTES) {
      setError('imagem acima de 5 MB');
      return;
    }

    setError(null);
    setBusy(true);
    try {
      await onSelectFile(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'falha no upload');
    } finally {
      setBusy(false);
    }
  }

  async function handleRemove() {
    setError(null);
    setBusy(true);
    try {
      await onRemoveImage();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'falha ao excluir');
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="cover">
      <div className="cover__frame">
        {imageUrl ? (
          <img src={imageUrl} alt={`Capa de ${name}`} />
        ) : (
          <span className="cover__placeholder" aria-hidden="true">
            {name.trim().charAt(0).toUpperCase() || '?'}
          </span>
        )}
      </div>

      <div className="cover__actions">
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED.join(',')}
          onChange={handleChange}
          hidden
        />
        <button
          type="button"
          disabled={busy}
          onClick={() => inputRef.current?.click()}
        >
          {imageUrl ? 'Trocar imagem' : 'Adicionar imagem'}
        </button>
        {imageUrl && (
          <button
            type="button"
            className="danger"
            disabled={busy}
            onClick={handleRemove}
          >
            Excluir imagem
          </button>
        )}
      </div>

      {error && <p className="error">{error}</p>}
    </div>
  );
}
