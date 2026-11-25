const { defineConfig, devices } = require('@playwright/test');
const LLMFailureReporter = require('./reporters/llm-failure-reporter');

module.exports = defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  timeout: 15000,
  workers: 1,
  reporter: [
    'html',
    [LLMFailureReporter, {
      outputDir: './test-results/llm-analysis',
      apiEndpoint: 'http://localhost:8000',
      enableAnalysis: process.env.DISABLE_LLM_ANALYSIS !== 'true',
    }],
  ],
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});