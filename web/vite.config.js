import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The proxy is why there is no CORS configuration anywhere: in development the
// browser only ever talks to Vite, which forwards /api to Flask.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
