import { existsSync } from "node:fs";

import { defineConfig } from "@playwright/test";

const chromeExecutable = process.env.PLAYWRIGHT_CHROME_PATH;

if (chromeExecutable && !existsSync(chromeExecutable)) {
  throw new Error(`System Chrome was not found at ${chromeExecutable}`);
}

export default defineConfig({
  testDir: "./e2e",
  outputDir: "./test-results/playwright",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 10_000 },
  reporter: [
    ["line"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
  ],
  use: {
    baseURL: process.env.SBLN_E2E_BASE_URL ?? "http://localhost:3000",
    browserName: "chromium",
    headless: true,
    launchOptions: chromeExecutable ? { executablePath: chromeExecutable } : undefined,
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "off",
  },
});
