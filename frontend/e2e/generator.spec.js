const { test, expect } = require('@playwright/test');

test.describe('ISO 20022 File Generator', () => {
  test('should update message type based on flow direction', async ({ page }) => {
    await page.goto('/test-files');

    const flowInput = page.locator('input[list="flow-options-generator"]');
    const typeSelect = page.locator('label:has-text("Message Type") + select');

    // 1. Test Inbound logic
    await flowInput.fill('Business Central (Inbound)');
    await expect(typeSelect).toHaveValue('camt.054.001.02');

    // 2. Test Outbound logic
    await flowInput.fill('Business Central (Outbound)');
    await expect(typeSelect).toHaveValue('pain.001.001.03');
  });

  test('should toggle cross-border target country selection', async ({ page }) => {
    await page.goto('/test-files');
    
    const cbToggle = page.locator('#cb-toggle');
    const targetCountryDiv = page.locator('.animate-fade-in');

    await expect(targetCountryDiv).not.toBeVisible();
    
    await cbToggle.check();
    await expect(targetCountryDiv).toBeVisible();
    await expect(targetCountryDiv).toContainText('Target Country');
  });

  test('should display correctly grouped countries', async ({ page }) => {
    await page.goto('/test-files');
    const countrySelect = page.locator('label:has-text("Originating Country") + select');
    
    await expect(countrySelect).toContainText('SE'); // Nordic group
    await expect(countrySelect).toContainText('DE'); // Alphabetical group
  });
});