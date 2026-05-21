const { test, expect } = require('@playwright/test');

test.describe('Transaction Lifecycle', () => {
  const testFlowName = 'E2E Test Flow ' + Date.now();
  const today = new Date().toISOString().split('T')[0];
  const validXml = `<?xml version="1.0" encoding="UTF-8"?>
    <Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
      <CstmrCdtTrfInitn>
        <GrpHdr>
          <MsgId>PW-MSG-100</MsgId>
          <CreDtTm>${new Date().toISOString()}</CreDtTm>
        </GrpHdr>
        <PmtInf>
          <PmtMtd>TRF</PmtMtd>
          <ReqdExctnDt>${today}</ReqdExctnDt>
          <DbtrAgt><FinInstnId><BIC>TESTBIC</BIC></FinInstnId></DbtrAgt>
          <DbtrAcct><Id><IBAN>SE123</IBAN></Id></DbtrAcct>
          <CdtTrfTxInf>
            <PmtId><InstrId>TX-PW-001</InstrId></PmtId>
            <Amt><InstdAmt Ccy="EUR">123.45</InstdAmt></Amt>
          </CdtTrfTxInf>
        </PmtInf>
      </CstmrCdtTrfInitn>
    </Document>`;

  test('should create a flow and handle duplicate file uploads', async ({ page }) => {
    // 1. Setup: Create a Flow with Duplicate Check enabled
    await page.goto('/flows');
    await page.getByTestId('flow-name-input').fill(testFlowName);
    await page.fill('#message-format', 'Pain.001');
    await page.check('#duplicate-check');
    await page.getByTestId('flow-submit-button').click();
    await expect(page.locator('table')).toContainText(testFlowName);

    // 2. Navigate to Transactions
    await page.goto('/transactions');

    // 3. Verify UI contrast and alignment (Sanity check)
    const flowSelect = page.getByTestId('flow-select');
    const fileInput = page.getByTestId('iso-file-upload');
    await expect(flowSelect).toHaveClass(/bg-gray-100/);
    await expect(flowSelect).toBeVisible();

    // 4. Perform first upload
    // We wait for the select element to contain the dynamic flow name
    // This confirms the API call finished and React re-rendered the options.
    await expect(flowSelect).toContainText(testFlowName);

    // Selecting by the exact label text is the most reliable way for standard HTML selects
    const fullLabel = `${testFlowName} (Pain.001)`;
    await flowSelect.selectOption({ label: fullLabel });

    await fileInput.setInputFiles({
      name: 'test.xml',
      mimeType: 'application/xml',
      buffer: Buffer.from(validXml)
    });
    await page.getByTestId('upload-button').click();
    await expect(page.getByTestId('upload-status-message')).toContainText('Upload successful');

    // 5. Perform duplicate upload to trigger validation error
    await fileInput.setInputFiles({
      name: 'test_duplicate.xml',
      mimeType: 'application/xml',
      buffer: Buffer.from(validXml)
    });
    await page.getByTestId('upload-button').click();
    
    // 6. Verify row exists and status is "Validation Failed"
    const lastRow = page.locator('tbody tr').last();
    const statusBtn = lastRow.getByTestId('status-badge-error');
    await expect(statusBtn).toHaveText('Validation Failed');

    // 7. Check the accessibility-compliant modal
    await statusBtn.click();
    const modal = page.getByRole('dialog');
    await expect(modal).toContainText('Duplicate Error');
    await page.getByLabel('Close modal').click();
    await expect(modal).not.toBeVisible();

    // 8. Cleanup: Delete the flow created for this test
    // This will cascade and delete all transactions associated with it.
    await page.goto('/flows');
    const flowRow = page.locator('tr', { hasText: testFlowName });
    await page.on('dialog', dialog => dialog.accept()); // Automatically accept the confirmation window
    await flowRow.getByLabel(`Delete flow ${testFlowName}`).click();
    await expect(page.locator('table')).not.toContainText(testFlowName);
  });
});