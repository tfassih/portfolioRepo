import { fileURLToPath } from "node:url";

process.env.NODE_ENV = "development";
const { dev } = await import("astro");
const server = await dev({
  root: fileURLToPath(new URL("../", import.meta.url)),
  server: { host: "127.0.0.1", port: 4322 },
  devToolbar: { enabled: false },
  cacheDir: fileURLToPath(new URL("../node_modules/.astro-tests/", import.meta.url)),
  vite: { cacheDir: fileURLToPath(new URL("../node_modules/.vite-tests/", import.meta.url)) },
});

for (const signal of ["SIGINT", "SIGTERM"]) {
  process.once(signal, async () => {
    await server.stop();
    process.exit(0);
  });
}
