import { defineConfig } from "vitest/config";
import path from "node:path";

export default defineConfig({
  test: {
    environment: "node",
    globals: true,
    cache: {
      dir: path.resolve(__dirname, ".vitest-cache"),
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname),
    },
  },
});
