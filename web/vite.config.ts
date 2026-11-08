import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// 開発時は Vite が画面を配り、/api だけ `inquiry-triage serve`（8765）へ中継する。
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8765" } },
  build: { outDir: "dist", emptyOutDir: true },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
