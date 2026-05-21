const { test, expect } = require('@playwright/test');

test.describe('Transaction Lifecycle', () => {
  const testFlowName = 'E2E Test Flow ' + Date.now();
  const validXml = `<?xml version="1.0" encoding="UTF-8"?>
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
      <CstmrCdtTrfInitn>
        <GrpHdr><MsgId>PW-MSG-100</MsgId></GrpHdr>
        <PmtInf>
          <PmtId><InstrId>TX-PW-001</InstrId></PmtId>
          <Amt><InstdAmt Ccy="EUR">123.45</InstdAmt></Amt>
          <DbtrAgt><FinInstnId><BIC>TESTBIC</BIC></FinInstnId></DbtrAgt>
          <DbtrAcct><Id><IBAN>SE123</IBAN></Id></DbtrAcct>
        </PmtInf>
      </CstmrCdtTrfInitn>
    </Document>`;

  test('should create a flow and handle duplicate file uploads', async ({ page }) => {
    // 1. Setup: Create a Flow with Duplicate Check enabled
    await page.goto('/flows');
    await page.fill('#flow-name', testFlowName);
    await page.fill('#message-format', 'Pain.001');
    await page.check('#duplicate-check');
    await page.click('button:has-text("Add Flow")');
    await expect(page.locator('table')).toContainText(testFlowName);

    // 2. Navigate to Transactions
    await page.goto('/transactions');

    // 3. Verify UI contrast and alignment (Sanity check)
    const flowSelect = page.locator('#flow-select');
    const fileInput = page.locator('#iso-file-upload');
    await expect(flowSelect).toHaveClass(/bg-gray-100/);
    await expect(flowSelect).toBeVisible();

    // 4. Perform first upload
    await flowSelect.selectOption({ label: new RegExp(testFlowName) });
    await fileInput.setInputFiles({
      name: 'test.xml',
      mimeType: 'application/xml',
      buffer: Buffer.from(validXml)
    });
    await page.click('button:has-text("Upload and Process")');
    await expect(page.locator('text=Upload successful')).toBeVisible();

    // 5. Perform duplicate upload to trigger validation error
    await fileInput.setInputFiles({
      name: 'test_duplicate.xml',
      mimeType: 'application/xml',
      buffer: Buffer.from(validXml)
    });
    await page.click('button:has-text("Upload and Process")');
    
    // 6. Verify row exists and status is "Validation Failed"
    const lastRow = page.locator('tbody tr').last();
    const statusBtn = lastRow.locator('button:has-text("Validation Failed")');
    await expect(statusBtn).toBeVisible();

    // 7. Check the accessibility-compliant modal
    await statusBtn.click();
    const modal = page.locator('role=dialog');
    await expect(modal).toContainText('Duplicate Error');
    await page.click('aria-label=Close modal');
    await expect(modal).not.toBeVisible();
  });
});