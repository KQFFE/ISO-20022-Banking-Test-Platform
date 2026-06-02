import React, { useState, useEffect } from 'react';
import axios from 'axios';
import FlowList from '../components/flows/FlowList';
import { API_BASE_URL, fetchWithRetry } from '../utils/api';

function Flows() {
  const [flows, setFlows] = useState([]);
  const [newFlow, setNewFlow] = useState({
    name: '',
    direction: 'Outbound',
    message_format: 'Pain.001',
    file_format: 'XML',
    bic_codes: [],
    valid_ibans: [],
    special_character_support: false,
    back_dated: false,
    future_dated: false,
    duplicate_check: false,
    currency_validation: false,
    allowed_currency: ''
  });
  const [editingId, setEditingId] = useState(null);
  const [bicString, setBicString] = useState('');
  const [ibanString, setIbanString] = useState('');

  const fetchFlows = async () => {
    try {
      const response = await fetchWithRetry(`${API_BASE_URL}/flows/`);
      setFlows(response.data);
    } catch (err) {
      console.error("Error fetching flows:", err);
    }
  };

  useEffect(() => {
    fetchFlows();
  }, []);

  const handleCreateFlow = async (e) => {
    e.preventDefault();
    const bicArray = bicString.split(',').map(s => s.trim()).filter(s => s);
    const ibanArray = ibanString.split(',').map(s => s.trim()).filter(s => s);

    const flowToSubmit = {
      ...newFlow,
      bic_codes: bicArray,
      valid_ibans: ibanArray
    };

    try {
      if (editingId) {
        await axios.put(`${API_BASE_URL}/flows/${editingId}`, flowToSubmit); // Direct axios.put for state-changing operation
      } else {
        await axios.post(`${API_BASE_URL}/flows/`, flowToSubmit); // Direct axios.post for state-changing operation
      }
      
      setEditingId(null);
      setBicString('');
      setIbanString('');
      setNewFlow({
        name: '',
        direction: 'Outbound',
        message_format: 'Pain.001',
        file_format: 'XML',
        special_character_support: false,
        back_dated: false,
        future_dated: false,
        duplicate_check: false,
        currency_validation: false,
        allowed_currency: ''
      });
      fetchFlows();
    } catch (err) {
      console.error("Error creating flow:", err);
    }
  };

  const handleEditInitiate = (flow) => {
    setEditingId(flow.id);
    setBicString(flow.bic_codes.join(', '));
    setIbanString(flow.valid_ibans.join(', '));
    setNewFlow({
      name: flow.name || '',
      direction: flow.direction || 'Outbound',
      message_format: flow.message_format || '',
      file_format: flow.file_format || 'XML',
      special_character_support: !!flow.special_character_support,
      back_dated: !!flow.back_dated,
      future_dated: !!flow.future_dated,
      duplicate_check: !!flow.duplicate_check,
      currency_validation: !!flow.currency_validation,
      allowed_currency: flow.allowed_currency || ''
    });
    // Scroll to form
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDeleteFlow = async (flowId) => {
    if (!window.confirm("Are you sure? This may fail if transactions are linked to this flow.")) return;
    try {
      await axios.delete(`${API_BASE_URL}/flows/${flowId}`); // Direct axios.delete for state-changing operation
      fetchFlows();
    } catch (err) {
      console.error("Failed to delete flow:", err);
      alert("Could not delete flow. It might be in use by existing transactions.");
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Flow Definitions</h1>

      <div className="mb-8 p-4 bg-white shadow rounded-lg">
        <h2 className="text-lg font-semibold mb-4">
          {editingId ? `Editing Flow: ${newFlow.name}` : 'Create New Flow'}
        </h2>
        <form onSubmit={handleCreateFlow} className="grid grid-cols-2 gap-4">
          <div className="flex flex-col">
            <label htmlFor="flow-name" className="text-sm font-medium text-gray-700 mb-1">Flow Name</label>
            <input 
              id="flow-name"
              data-testid="flow-name-input"
              className="border p-2 rounded" 
              placeholder="e.g. SEPA Outbound" 
              value={newFlow.name}
              onChange={(e) => setNewFlow({...newFlow, name: e.target.value})}
              required
            />
          </div>
          <div className="flex flex-col">
            <label htmlFor="flow-direction" className="text-sm font-medium text-gray-700 mb-1">Direction</label>
            <select 
              id="flow-direction"
              className="border p-2 rounded"
              value={newFlow.direction}
              onChange={(e) => setNewFlow({...newFlow, direction: e.target.value})}
            >
              <option value="Inbound">Inbound</option>
              <option value="Outbound">Outbound</option>
            </select>
          </div>
          <div className="flex flex-col">
            <label htmlFor="message-format" className="text-sm font-medium text-gray-700 mb-1">Message Format</label>
            <input 
              id="message-format"
              className="border p-2 rounded" 
              placeholder="e.g. Pain.001" 
              value={newFlow.message_format}
              onChange={(e) => setNewFlow({...newFlow, message_format: e.target.value})}
            />
          </div>
          <div className="flex flex-col">
            <label htmlFor="allowed-bics" className="text-sm font-medium text-gray-700 mb-1">Allowed BICs</label>
            <input 
              id="allowed-bics"
              className="border p-2 rounded" 
              placeholder="Comma separated list" 
              value={bicString}
              onChange={(e) => setBicString(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2 p-2">
            <label className="flex items-center gap-2 text-sm">
              <input 
                id="special-char-support"
                type="checkbox" 
                checked={newFlow.special_character_support}
                onChange={(e) => setNewFlow({...newFlow, special_character_support: e.target.checked})}
              />
              Special Character Support
            </label>
            <label htmlFor="back-dated-check" className="flex items-center gap-2 text-sm">
              <input 
                id="back-dated-check"
                type="checkbox" 
                checked={newFlow.back_dated}
                onChange={(e) => setNewFlow({...newFlow, back_dated: e.target.checked})}
              />
              Allow Back Dated
            </label>
            <label htmlFor="future-dated-check" className="flex items-center gap-2 text-sm">
              <input 
                id="future-dated-check"
                type="checkbox" 
                checked={newFlow.future_dated}
                onChange={(e) => setNewFlow({...newFlow, future_dated: e.target.checked})}
              />
              Allow Future Dated
            </label>
            <label htmlFor="duplicate-check" className="flex items-center gap-2 text-sm">
              <input 
                id="duplicate-check"
                type="checkbox" 
                checked={newFlow.duplicate_check}
                onChange={(e) => setNewFlow({...newFlow, duplicate_check: e.target.checked})}
              />
              Duplicate Check
            </label>
            <div className="mt-4 pt-4 border-t border-gray-100">
              <label htmlFor="currency-validation" className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-2">
                <input 
                  id="currency-validation"
                  type="checkbox" 
                  checked={newFlow.currency_validation}
                  onChange={(e) => setNewFlow({...newFlow, currency_validation: e.target.checked})}
                />
                Currency Validation
              </label>
              <select 
                id="allowed-currency"
                className={`w-full border p-2 rounded text-sm ${!newFlow.currency_validation ? 'bg-gray-100 cursor-not-allowed text-gray-400' : 'bg-white text-gray-900'}`}
                value={newFlow.allowed_currency}
                onChange={(e) => setNewFlow({...newFlow, allowed_currency: e.target.value})}
                disabled={!newFlow.currency_validation}
                required={newFlow.currency_validation}
                onInvalid={(e) => e.target.setCustomValidity('Select a currency to continue.')}
                onInput={(e) => e.target.setCustomValidity('')}
              >
                <option value="">-- Select Currency --</option>
                <option value="SEK">SEK</option>
                <option value="DKK">DKK</option>
                <option value="NOK">NOK</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="USD">USD</option>
              </select>
            </div>
          </div>
          <div className="flex flex-col">
            <label htmlFor="iban-patterns" className="text-sm font-medium text-gray-700 mb-1">IBAN Patterns</label>
            <input 
              id="iban-patterns"
              className="border p-2 rounded" 
              placeholder="e.g. DE%, FR123" 
              value={ibanString}
              onChange={(e) => setIbanString(e.target.value)}
            />
          </div>
          <div className="hidden md:block"></div> {/* Spacer to keep buttons in bottom right */}
          <div className="flex gap-2">
            <button 
              type="submit" 
              data-testid="flow-submit-button"
              className="flex-1 bg-blue-600 text-white rounded p-2 hover:bg-blue-700"
            >
              {editingId ? 'Update Flow' : 'Add Flow'}
            </button>
            {editingId && (
              <button 
                type="button" 
                onClick={() => {
                  setEditingId(null);
                  setBicString('');
                  setIbanString('');
                  setNewFlow({
                    name: '',
                    direction: 'Outbound',
                    message_format: 'Pain.001',
                    file_format: 'XML',
                    special_character_support: false,
                    back_dated: false,
                    future_dated: false,
                    duplicate_check: false,
                    currency_validation: false,
                    allowed_currency: ''
                  });
                }}
                className="px-4 bg-gray-500 text-white rounded hover:bg-gray-600">
                Cancel
              </button>
            )}
          </div>
        </form>
      </div>

      <div className="bg-white shadow rounded-lg">
        <FlowList flows={flows} onDelete={handleDeleteFlow} onEdit={handleEditInitiate} />
      </div>
    </div>
  );
}

export default Flows;