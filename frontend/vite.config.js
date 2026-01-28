import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 8029,
    strictPort: true,
    hmr: false, // 🔥 CLAVE
    allowedHosts: [
      "finanzapp-dev.ngrok.io",
      "finanzapp.ngrok.io",
    ],
  },
});
