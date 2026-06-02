const { test, expect } = require('@playwright/test');

test.describe('Flow Definition Validations', () => {
  const uniqueFlowName = 'Validation Test Flow ' + Date.now();

  // Robust Cleanup: Ensures test data is removed from the database after every run
  test.afterEach(async ({ page }) => {
    try {
      await page.goto('/flows');
      // Use the semantic row role and filter by the unique name
      const flowRow = page.getByRole('row').filter({ hasText: uniqueFlowName });
      if (await flowRow.count() > 0) {
        page.on('dialog', dialog => dialog.accept()); 
        // Targeted delete within the specific row
        await flowRow.getByRole('button', { name: /delete/i }).click();
        // Verify removal from the data-testid container
        await expect(page.getByTestId('flow-list')).not.toContainText(uniqueFlowName);
      }
    } catch (e) {
      console.log('Cleanup navigation failed or flow already deleted');
    }
  });

  test('should enforce currency selection when validation is enabled', async ({ page }) => {
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