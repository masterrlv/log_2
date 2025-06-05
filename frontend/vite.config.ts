import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  base: '/',
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    strictPort: true,
  },
  preview: {
    port: 5173,
    strictPort: true,
  },
})
