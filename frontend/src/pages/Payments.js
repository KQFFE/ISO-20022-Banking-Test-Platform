import React, { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { API_BASE_URL, fetchWithRetry } from '../utils/api';

function Payments() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [flows, setFlows] = useState([]);
  const [selectedFlowId, setSelectedFlowId] = useState('');
  const [uploadMessage, setUploadMessage] = useState('');
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const fetchFlows = useCallback(async () => {
    try {
      const response = await fetchWithRetry(`${API_BASE_URL}/flows/`);
      // Include both Initiation (pain) and Reporting (camt) flows
      const paymentFlows = response.data.filter(f => 
        f.message_format.toLowerCase().includes('pain') || 
        f.message_format.toLowerCase().includes('camt')
      );
      setFlows(paymentFlows.length > 0 ? paymentFlows : response.data);
      if (response.data.length > 0 && !selectedFlowId) {
        setSelectedFlowId(response.data[0].id);
      }
    } catch (err) {
      console.error("Error fetching flows:", err);
      setError("Failed to load flow definitions.");
    }
  }, [selectedFlowId]);

  useEffect(() => {
    fetchFlows();
  }, [fetchFlows]);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleFlowChange = (event) => {
    setSelectedFlowId(event.target.value);
  };

  const handleUpload = async () => {
    if (!selectedFile || !selectedFlowId) {
      setError("Please select a file and a flow configuration.");
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setUploadMessage('Processing ISO 20022 file...');
      setError('');
      const response = await axios.post(`${API_BASE_URL}/transactions/upload/${selectedFlowId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadMessage(`Success: ${response.data.transactions_imported} payment instructions imported.`);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    } catch (err) {
      console.error("Upload error:", err.response ? err.response.data : err.message);
      setError(`Upload failed: ${err.response ? err.response.data.detail : err.message}`);
      setUploadMessage('');
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Payments & Notifications</h1>
      <p className="text-gray-600 mb-6">Test the payment lifecycle: Initiation (pain.001) and Bank Notifications (camt.054).</p>

      <div className="mb-6 p-6 border rounded-lg bg-white shadow-sm border-blue-100">
        <h2 className="text-xl font-semibold mb-4 text-blue-800">Upload ISO 20022 Message</h2>
        {error && <p className="text-red-500 mb-4 bg-red-50 p-2 rounded border border-red-100">{error}</p>}
        {uploadMessage && <p data-testid="upload-status-message" className="text-green-600 mb-4 bg-green-50 p-2 rounded border border-green-100 font-medium">{uploadMessage}</p>}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="flex flex-col">
            <label htmlFor="flow-select" className="block text-sm font-medium text-gray-700 mb-2">Target Payment Flow</label>
            <select
              id="flow-select"
              data-testid="flow-select"
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={selectedFlowId}
              onChange={handleFlowChange}
            >
              <option value="">-- Select Flow Configuration --</option>
              {flows.map((flow) => (
                <option key={flow.id} value={flow.id}>
                  {flow.name} ({flow.message_format})
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-col">
            <label htmlFor="iso-file-upload" className="block text-sm font-medium text-gray-700 mb-2">ISO 20022 XML (pain/camt)</label>
            <input 
              id="iso-file-upload" 
              data-testid="iso-file-upload"
              ref={fileInputRef}
              type="file" 
              accept=".xml"
              onChange={handleFileChange} 
              className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" 
            />
          </div>
        </div>
        <button
          onClick={handleUpload}
          data-testid="upload-button"
          disabled={!selectedFile || !selectedFlowId}
          className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white font-bold rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          Validate and Process Message
        </button>
      </div>
    </div>
  );
}

export default Payments;