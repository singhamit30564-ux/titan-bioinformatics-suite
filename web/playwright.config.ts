import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright smoke config. `testDir` is pinned to tests/e2e so the runner never
 * picks up the vitest unit tests under tests/ (their @vitest/expect matchers
 * collide with Playwright's). The webServer serves the production build output
 * that the CI `npm run build` step produces just before the e2e step.
 */
export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: "**/*.spec.ts",
  timeout: 30_000,
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["github"]] : "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run preview -- --port 4173 --strictPort",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
