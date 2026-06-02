const { test, expect } = require('@playwright/test');

test.describe('Dashboard / Overview', () => {
  test('should clear history and reset statistics', async ({ page }) => {
    await page.goto('/');

    // Handle the browser confirm dialog automatically
    page.on('dialog', dialog => dialog.accept());

    const clearButton = page.getByRole('button', { name: /Clear History/i });
    await expect(clearButton).toBeVisible();

    await clearButton.click();

    // Check that stats reset to zero/defaults
    const totalTransactions = page.locator('p:near(h3:has-text("Total Transactions"))').first();
    const successRate = page.locator('p:near(h3:has-text("Success Rate"))').first();

    await expect(totalTransactions).toHaveText('0');
    // Default success rate for 0 transactions should be 100% as per requirements
    await expect(successRate).toHaveText('100%');
  });
});