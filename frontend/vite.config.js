import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Dev server runs on 5173; API base URL is provided via VITE_API_BASE_URL.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
  },
});
