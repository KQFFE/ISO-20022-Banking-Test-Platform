import React, { useState, useEffect } from 'react';
import axios from 'axios';
import FlowList from '../components/flows/FlowList';

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
    future_dated: false
  });

  const fetchFlows = async () => {
    try {
      const response = await axios.get('http://localhost:8000/flows/');
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
    // Extract arrays from form elements since they aren't bound to state
    const bicArray = e.target.elements.bic_codes.value.split(',').map(s => s.trim()).filter(s => s);
    const ibanArray = e.target.elements.valid_ibans.value.split(',').map(s => s.trim()).filter(s => s);

    const flowToSubmit = {
      ...newFlow,
      bic_codes: bicArray,
      valid_ibans: ibanArray
    };

    try {
      await axios.post('http://localhost:8000/flows/', flowToSubmit);
      setNewFlow({
        name: '',
        direction: 'Outbound',
        message_format: 'Pain.001',
        file_format: 'XML',
        bic_codes: [],
        valid_ibans: [],
        special_character_support: false,
        back_dated: false,
        future_dated: false
      });
      fetchFlows();
      e.target.reset();
    } catch (err) {
      console.error("Error creating flow:", err);
    }
  };

  const handleDeleteFlow = async (flowId) => {
    if (!window.confirm("Are you sure? This may fail if transactions are linked to this flow.")) return;
    try {
      await axios.delete(`http://localhost:8000/flows/${flowId}`);
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
        <h2 className="text-lg font-semibold mb-4">Create New Flow</h2>
        <form onSubmit={handleCreateFlow} className="grid grid-cols-2 gap-4">
          <input 
            className="border p-2 rounded" 
            placeholder="Flow Name (e.g. SEPA Outbound)" 
            value={newFlow.name}
            onChange={(e) => setNewFlow({...newFlow, name: e.target.value})}
            required
          />
          <select 
            className="border p-2 rounded"
            value={newFlow.direction}
            onChange={(e) => setNewFlow({...newFlow, direction: e.target.value})}
          >
            <option value="Inbound">Inbound</option>
            <option value="Outbound">Outbound</option>
          </select>
          <input 
            className="border p-2 rounded" 
            placeholder="Message Format (e.g. Pain.001)" 
            value={newFlow.message_format}
            onChange={(e) => setNewFlow({...newFlow, message_format: e.target.value})}
          />
          <input 
            name="bic_codes"
            className="border p-2 rounded" 
            placeholder="Allowed BICs (comma separated)" 
          />
          <input 
            name="valid_ibans"
            className="border p-2 rounded" 
            placeholder="IBAN Patterns (e.g. DE%, FR123)" 
          />
          <div className="flex flex-col gap-2 p-2">
            <label className="flex items-center gap-2 text-sm">
              <input 
                type="checkbox" 
                checked={newFlow.special_character_support}
                onChange={(e) => setNewFlow({...newFlow, special_character_support: e.target.checked})}
              />
              Special Character Support
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input 
                type="checkbox" 
                checked={newFlow.back_dated}
                onChange={(e) => setNewFlow({...newFlow, back_dated: e.target.checked})}
              />
              Allow Back Dated
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input 
                type="checkbox" 
                checked={newFlow.future_dated}
                onChange={(e) => setNewFlow({...newFlow, future_dated: e.target.checked})}
              />
              Allow Future Dated
            </label>
          </div>
          <button type="submit" className="bg-blue-600 text-white rounded p-2 hover:bg-blue-700">
            Add Flow
          </button>
        </form>
      </div>

      <div className="bg-white shadow rounded-lg">
        <FlowList flows={flows} onDelete={handleDeleteFlow} />
      </div>
    </div>
  );
}

export default Flows;