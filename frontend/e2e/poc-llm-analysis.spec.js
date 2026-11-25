/**
 * POC Test: Intentional selector failure for LLM analysis
 *
 * This test deliberately uses a broken selector to demonstrate the LLM
 * analysis reporter in action. Run with:
 *
 *   npx playwright test poc-llm-analysis.spec.js
 *
 * Then check test-results/llm-analysis/llm-analysis-report.json for results.
 */

const { test, expect } = require('@playwright/test');

test.describe('LLM Analysis POC', () => {
  test('accessibility test with intentional failure', async ({ page }) => {
    // This test will fail with a broken selector, triggering LLM analysis
    await page.goto('http://localhost:3000');

    // Try to find an element with an intentionally wrong selector
    // This mimics real-world selector drift scenarios
    const element = await page.locator('[data-testid="nonexistent-button-that-moved"]');
    await expect(element).toBeVisible({ timeout: 3000 });
  });
});
