/// <reference types="vitest/config" />
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules/recharts')) return 'recharts'
          if (id.includes('node_modules/react-router')) return 'router'
          if (id.includes('node_modules/@tanstack')) return 'query'
        },
      },
    },
  },
  // @ts-expect-error vitest extends UserConfig
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    env: {
      VITE_API_BASE_URL: 'http://127.0.0.1:8001/api/v1',
      VITE_WS_BASE_URL: 'ws://127.0.0.1:8001/ws/alerts',
      VITE_APP_NAME: 'RetainAI',
      VITE_APP_VERSION: '0.1.0',
      VITE_USE_MOCK_DATA: 'false',
      VITE_RM_ID: 'RM-01',
      VITE_RM_NAME: 'RM User',
      VITE_ENABLE_SIMULATOR: 'true',
      VITE_ENABLE_SYSTEM_PAGE: 'true',
    },
  },
})
