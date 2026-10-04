import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import vercel from "@astrojs/vercel";
export default defineConfig({
  site: "https://thomasfassih.com",
  output: "server",
  adapter: vercel(),
  integrations: [react()],
  trailingSlash: "always",
});