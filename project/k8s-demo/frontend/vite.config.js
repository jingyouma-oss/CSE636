import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // For local `npm run dev` only; in the cluster, Nginx does the /api proxy.
  server: {
    proxy: { '/api': 'http://localhost:8000' },
  },
})
