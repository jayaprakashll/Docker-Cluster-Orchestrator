import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],

  server: {
    host: "0.0.0.0",
    port: 5173,

    proxy: {
      "/manager-api": {
        target: "http://host.docker.internal:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/manager-api/, ""),
      },
    },
  },
});