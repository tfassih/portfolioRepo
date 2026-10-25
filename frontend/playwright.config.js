import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";

const localPython = fileURLToPath(new URL(
  process.platform === "win32" ? "../.venv/Scripts/python.exe" : "../.venv/bin/python",
  import.meta.url,
));
const python = process.env.TEST_PYTHON || (existsSync(localPython) ? localPython : "python");

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false,
  workers: 1,
  use: { baseURL: "http://127.0.0.1:4322", trace: "retain-on-failure" },
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] } },
  ],
  webServer: [
    {
      command: `"${python}" ../backend/content/tests/browser_server.py`,
      url: "http://127.0.0.1:8001/health/",
      reuseExistingServer: false,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 4322 --ignore-lock",
      url: "http://127.0.0.1:4322/",
      env: {
        API_ORIGIN: "http://127.0.0.1:8001",
        PUBLIC_API_ORIGIN: "http://127.0.0.1:8001",
        INTERNAL_API_KEY: "test-only-internal-key",
        ASTRO_TELEMETRY_DISABLED: "1",
      },
      reuseExistingServer: false,
    },
  ],
});
