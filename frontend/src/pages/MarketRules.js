import React from 'react';

const RULES = [
  {
    format: 'pain.001 (Credit Transfer)',
    fields: [
      { path: 'GrpHdr/MsgId', rule: 'Unique within 24h', mandatory: 'Yes', type: 'Max35Text' },
      { path: 'PmtInf/ReqdExctnDt', rule: 'T or T+30 range', mandatory: 'Yes', type: 'ISODate' },
      { path: 'Dbtr/Nm', rule: 'No special chars', mandatory: 'Yes', type: 'Max70Text' },
      { path: 'DbtrAcct/Id/IBAN', rule: 'Valid ISO structure', mandatory: 'Yes', type: 'IBAN2007Identifier' },
    ]
  },
  {
    format: 'camt.054 (Notifications)',
    fields: [
      { path: 'Ntfctn/Id', rule: 'System generated', mandatory: 'Yes', type: 'Max35Text' },
      { path: 'Ntfctn/Ntry/Amt', rule: 'Matching original pain.001', mandatory: 'Yes', type: 'ActiveOrHistoricCurrencyAndAmount' },
      { path: 'Ntfctn/Ntry/Sts', rule: 'BOOK or PDNG only', mandatory: 'Yes', type: 'EntryStatus1Code' },
    ]
  }
];

function MarketRules() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Market Rules & Requirements</h1>
      <p className="text-gray-600 mb-8">Detailed validation logic and requirement specifications per message format.</p>

      <div className="space-y-10">
        {RULES.map((section) => (
          <div key={section.format} className="bg-white shadow-sm border rounded-lg overflow-hidden">
            <div className="bg-gray-800 px-6 py-3">
              <h2 className="text-lg font-semibold text-white">{section.format}</h2>
            </div>
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">XML Path</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ISO Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Mandatory</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Business Rule</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {section.fields.map((field, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-blue-600">{field.path}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{field.type}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded text-xs font-bold ${field.mandatory === 'Yes' ? 'bg-orange-100 text-orange-800' : 'bg-gray-100 text-gray-800'}`}>
                        {field.mandatory}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-700">{field.rule}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
      </div>

      <div className="mt-12 bg-yellow-50 border-l-4 border-yellow-400 p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">Note on EPC Implementation</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>
                The rules listed here follow the **SEPA Credit Transfer (SCT)** and **SEPA Direct Debit (SDD)** rulebooks defined by the European Payments Council. 
                Country-specific deviations (like Swedish character handling) are managed via Flow Definitions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default MarketRules;