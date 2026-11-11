const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: '.',
  testMatch: 'benchmark.spec.js',
  outputDir: '../test-results/playwright-visual',
  timeout: 60000,
  workers: 1,
  reporter: 'list',
  use: {
    ...devices['Desktop Chrome'],
    baseURL: 'http://localhost:3100',
    viewport: { width: 1280, height: 720 },
    locale: 'en-US',
    timezoneId: 'UTC',
    serviceWorkers: 'block',
  },
  webServer: {
    command: 'npm start',
    url: 'http://localhost:3100',
    env: { PORT: '3100', BROWSER: 'none' },
    reuseExistingServer: false,
    timeout: 120000,
  },
});
