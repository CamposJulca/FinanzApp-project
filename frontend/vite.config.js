import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  cacheDir: ".vite-cache",
  server: {
    host: true,
    port: 8029,
    strictPort: true,
    hmr: false, // 🔥 CLAVE
    allowedHosts: [
      "finanzapp-dev.ngrok.io",
      "finanzapp.ngrok.io",
    ],
    proxy: {
      "/api": "http://127.0.0.1:8090",
      "/login": "http://127.0.0.1:8090",
      "/logout": "http://127.0.0.1:8090",
    },
  },
});
