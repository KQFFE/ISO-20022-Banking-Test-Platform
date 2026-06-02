const { test, expect } = require('@playwright/test');

test.describe('Flow Definition Validations', () => {
  test('should enforce currency selection when validation is enabled', async ({ page }) => {
    const uniqueFlowName = 'Validation Test Flow ' + Date.now();
    await page.goto('/flows');
    
    await page.getByTestId('flow-name-input').fill(uniqueFlowName);
    const currencyCheckbox = page.locator('#currency-validation');
    const currencySelect = page.locator('#allowed-currency');

    // Verify disabled state
    await expect(currencySelect).toBeDisabled();
    
    // Enable validation
    await currencyCheckbox.check();
    await expect(currencySelect).toBeEnabled();
    await expect(currencySelect).toHaveAttribute('required');

    // Test custom browser validation message
    await page.getByTestId('flow-submit-button').click();
    
    const validationMessage = await currencySelect.evaluate(el => el.validationMessage);
    expect(validationMessage).toBe('Select a currency to continue.');

    // Fill and submit
    await currencySelect.selectOption('EUR');

    const responsePromise = page.waitForResponse(resp => resp.url().includes('/flows/') && resp.request().method() === 'POST');
    await page.getByTestId('flow-submit-button').click();
    const response = await responsePromise;

    if (response.status() !== 200) {
      // Attempt to get the detail from the response body
      const errorBody = await response.json().catch(() => ({}));
      const detail = errorBody.detail || 'Unknown internal error';
      throw new Error(`Flow creation failed with status ${response.status()}: ${detail}`);
    }
    
    // Targeted synchronization using semantic roles
    await expect(page.getByRole('row').filter({ hasText: uniqueFlowName })).toBeVisible();
  });
});