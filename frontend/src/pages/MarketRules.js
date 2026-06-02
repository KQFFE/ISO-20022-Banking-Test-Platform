import React, { useState, useMemo } from 'react';

const FLOW_SYSTEMS = [
  'Business Central',
  'FirstVision',
  'iCard',
  'Navision',
  'NETS',
  'NFS-Ascent',
  'Therefore'
];

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
  const [searchTerm, setSearchTerm] = useState('');

  // Generate the list of selectable flows similar to TestFiles.js
  const allFlowOptions = useMemo(() => {
    return [...FLOW_SYSTEMS].sort((a, b) => a.localeCompare(b)).flatMap(system => [
      `${system} (Inbound)`,
      `${system} (Outbound)`
    ]);
  }, []);

  // Filter rules based on selection. 
  // If Inbound is selected, show camt. If Outbound is selected, show pain.
  // If nothing is selected, show all.
  const filteredRules = useMemo(() => {
    if (!searchTerm) return RULES;
    
    const isOutbound = searchTerm.toLowerCase().includes('outbound');
    const isInbound = searchTerm.toLowerCase().includes('inbound');

    if (isOutbound) return RULES.filter(r => r.format.toLowerCase().includes('pain'));
    if (isInbound) return RULES.filter(r => r.format.toLowerCase().includes('camt'));
    
    return RULES;
  }, [searchTerm]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Market Rules & Requirements</h1>
      <p className="text-gray-600 mb-8">Detailed validation logic and requirement specifications per message format.</p>

      {/* Searchable Flow Selection */}
      <div className="mb-10 max-w-md">
        <label htmlFor="flow-search" className="block text-sm font-medium text-gray-700 mb-2">
          Filter Rules by Flow Configuration
        </label>
        <div className="relative">
          <input
            id="flow-search"
            list="flow-options"
            type="text"
            className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm p-2.5 border"
            placeholder="Search and pick a flow (e.g. iCard Inbound)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <datalist id="flow-options">
            {allFlowOptions.map(option => <option key={option} value={option} />)}
          </datalist>
          {searchTerm && (
            <button 
              onClick={() => setSearchTerm('')}
              className="absolute right-3 top-2.5 text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      <div className="space-y-10">
        {filteredRules.map((section) => (
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