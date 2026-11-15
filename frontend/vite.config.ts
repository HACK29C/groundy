import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// Groundy se publica en GitHub Pages con dominio propio (groundy.site), por eso base = '/'.
export default defineConfig({
  base: '/',
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      // El service worker se activa en el paso F10 (modo sin conexión); por ahora solo el manifiesto.
      injectRegister: false,
      selfDestroying: true,
      manifest: {
        name: 'Groundy',
        short_name: 'Groundy',
        description: 'Your farm seen from space, with the evidence behind every number. By Potatonauts.',
        lang: 'en',
        theme_color: '#0E3B23',
        background_color: '#FFF9F5',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: '/brand/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/brand/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
    }),
  ],
})
