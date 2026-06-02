const { test, expect } = require('@playwright/test');

test.describe('Flow Definition Validations', () => {
  test('should enforce currency selection when validation is enabled', async ({ page }) => {
    await page.goto('/flows');
    
    await page.getByTestId('flow-name-input').fill('Validation Test Flow');
    const currencyCheckbox = page.locator('#currency-validation');
    const currencySelect = page.locator('#allowed-currency');

    // Verify disabled state
    await expect(currencySelect).toBeDisabled();
    
    // Enable validation
    await currencyCheckbox.check();
    await expect(currencySelect).toBeEnabled();
    await expect(currencySelect).toBeRequired();

    // Test custom browser validation message
    await page.getByTestId('flow-submit-button').click();
    
    const validationMessage = await currencySelect.evaluate(el => el.validationMessage);
    expect(validationMessage).toBe('Select a currency to continue.');

    // Fill and submit
    await currencySelect.selectOption('EUR');
    await page.getByTestId('flow-submit-button').click();
    
    await expect(page.locator('table')).toContainText('Validation Test Flow');
  });
});