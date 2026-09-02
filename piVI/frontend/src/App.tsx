import { useState } from 'react';

import { PlaylistsTab } from './features/playlists/PlaylistsTab';

type Tab = 'radio' | 'playlists';

const TABS: { id: Tab; label: string }[] = [
  { id: 'radio', label: 'Rádio' },
  { id: 'playlists', label: 'Playlists' },
];

export default function App() {
  const [tab, setTab] = useState<Tab>('playlists');

  return (
    <main>
      <h1>Sistema de recomendação</h1>

      <nav className="tabs" role="tablist">
        {TABS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={tab === id}
            className={tab === id ? 'tab tab--active' : 'tab'}
            onClick={() => setTab(id)}
          >
            {label}
          </button>
        ))}
      </nav>

      {tab === 'playlists' ? (
        <PlaylistsTab />
      ) : (
        <section>
          <h2>Rádio</h2>
          <p className="muted">
            Busca, recomendação e player ainda não implementados.
          </p>
        </section>
      )}
    </main>
  );
}
