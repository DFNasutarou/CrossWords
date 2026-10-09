/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages などのサブパス配信でも動くよう相対パスでビルドする
export default defineConfig({
  base: "./",
  plugins: [react()],
  test: {
    include: ["tests/**/*.test.ts"],
  },
});
