import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // API de playlists (NestJS).
      '/nest': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/nest/, '/api'),
      },
      // API de recomendacao (Express).
      '/api': 'http://localhost:8000',
    },
  },
});
