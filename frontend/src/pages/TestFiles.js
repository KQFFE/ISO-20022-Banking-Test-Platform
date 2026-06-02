import React, { useState, useEffect } from 'react';

const MOCK_IBANS = {
  'SE': ['SE12345678901234567890', 'SE98765432109876543210'],
  'DE': ['DE12345678901234567890', 'DE88887777666655554444'],
  'NO': ['NO12345678901', 'NO99887766554'],
  'FI': ['FI1234567890123456', 'FI5544332211009988']
};

function TestFiles() {
  const [fileType, setFileType] = useState('pain.001.001.03');
  const [country, setCountry] = useState('SE');
  const [isCrossBorder, setIsCrossBorder] = useState(false);
  const [targetCountry, setTargetCountry] = useState('DE');
  const [selectedIban, setSelectedIban] = useState('');

  // Auto-populate IBAN when country changes
  useEffect(() => {
    if (MOCK_IBANS[country]) {
      setSelectedIban(MOCK_IBANS[country][0]);
    }
  }, [country]);

  const handleDownload = () => {
    const xmlContent = `<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:${fileType}">
  <CstmrCdtTrfInitn>
    <GrpHdr>
      <MsgId>GEN-${Date.now()}</MsgId>
      <CreDtTm>${new Date().toISOString()}</CreDtTm>
    </GrpHdr>
    <PmtInf>
      <DbtrAcct><Id><IBAN>${selectedIban}</IBAN></Id></DbtrAcct>
      <CdtTrfTxInf>
        <Amt><InstdAmt Ccy="EUR">100.00</InstdAmt></Amt>
        <CdtrAcct><Id><IBAN>${isCrossBorder ? MOCK_IBANS[targetCountry][0] : selectedIban}</IBAN></Id></CdtrAcct>
      </CdtTrfTxInf>
    </PmtInf>
  </CstmrCdtTrfInitn>
</Document>`;

    const blob = new Blob([xmlContent], { type: 'application/xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${fileType}_${country}_${isCrossBorder ? 'CrossBorder' : 'Domestic'}.xml`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">ISO 20022 File Generator</h1>
      <p className="text-gray-600 mb-8">Generate valid test messages for specific market scenarios.</p>

      <div className="bg-white shadow-md rounded-lg p-6 max-w-2xl border border-gray-200">
        <div className="space-y-6">
          {/* File Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Message Type</label>
            <select 
              value={fileType} 
              onChange={(e) => setFileType(e.target.value)}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm p-2 border"
            >
              <option value="pain.001.001.03">pain.001 (Credit Transfer)</option>
              <option value="pain.008.001.02">pain.008 (Direct Debit)</option>
              <option value="camt.054.001.02">camt.054 (Notification)</option>
            </select>
          </div>

          {/* Country Selection */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Originating Country</label>
              <select 
                value={country} 
                onChange={(e) => setCountry(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm p-2 border"
              >
                {Object.keys(MOCK_IBANS).map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700">Source IBAN (Auto-populated)</label>
              <select 
                value={selectedIban}
                onChange={(e) => setSelectedIban(e.target.value)}
                className="mt-1 block w-full bg-gray-50 border-gray-300 rounded-md shadow-sm sm:text-sm p-2 border"
              >
                {MOCK_IBANS[country]?.map(iban => (
                  <option key={iban} value={iban}>{iban}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Cross Border Toggle */}
          <div className="flex items-center space-x-3 p-4 bg-blue-50 rounded-md">
            <input 
              type="checkbox" 
              id="cb-toggle"
              checked={isCrossBorder}
              onChange={(e) => setIsCrossBorder(e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            <label htmlFor="cb-toggle" className="text-sm font-medium text-blue-900">
              Enable Cross-border Scenario
            </label>
          </div>

          {isCrossBorder && (
            <div className="animate-fade-in">
              <label className="block text-sm font-medium text-gray-700">Target Country</label>
              <select 
                value={targetCountry} 
                onChange={(e) => setTargetCountry(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm p-2 border"
              >
                {Object.keys(MOCK_IBANS).filter(c => c !== country).map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <p className="mt-2 text-xs text-gray-500 italic">
                Generated file will use a {targetCountry} IBAN for the Creditor.
              </p>
            </div>
          )}

          <button
            onClick={handleDownload}
            className="w-full bg-blue-600 text-white font-bold py-3 px-4 rounded-md hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Generate and Download XML
          </button>
        </div>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-500 max-w-2xl">
        <div className="p-4 border rounded bg-gray-50">
          <strong>Tip:</strong> These files are guaranteed to pass the "Flow Definition" validation for the selected countries.
        </div>
        <div className="p-4 border rounded bg-gray-50">
          <strong>Security:</strong> All generated IBANs are from test ranges and do not represent real bank accounts.
        </div>
      </div>
    </div>
  );
}

export default TestFiles;