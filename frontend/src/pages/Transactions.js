import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000'; // Your FastAPI backend URL

function Transactions() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [flows, setFlows] = useState([]);
  const [selectedFlowId, setSelectedFlowId] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [uploadMessage, setUploadMessage] = useState('');
  const [error, setError] = useState('');

  const fetchTransactions = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/transactions/`);
      setTransactions(response.data);
    } catch (err) {
      console.error("Error fetching transactions:", err);
      setError("Failed to load transactions.");
    }
  }, []);

  const fetchFlows = useCallback(async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/flows/`);
      setFlows(response.data);
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
    fetchTransactions();
  }, [fetchFlows, fetchTransactions]);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleFlowChange = (event) => {
    setSelectedFlowId(event.target.value);
  };

  const handleUpload = async () => {
    if (!selectedFile || !selectedFlowId) {
      setError("Please select a file and a flow.");
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      setUploadMessage('Uploading...');
      setError('');
      const response = await axios.post(`${API_BASE_URL}/transactions/upload/${selectedFlowId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadMessage(`Upload successful: ${response.data.transactions_imported} transactions imported.`);
      setSelectedFile(null); // Clear selected file
      fetchTransactions();
    } catch (err) {
      console.error("Upload error:", err.response ? err.response.data : err.message);
      setError(`Upload failed: ${err.response ? err.response.data.detail : err.message}`);
      setUploadMessage('');
    }
  };

  const handleGenerateOutput = async (transactionId) => {
    try {
      setUploadMessage(`Generating output for ID: ${transactionId}...`);
      // Placeholder for the execution endpoint
      await axios.post(`${API_BASE_URL}/transactions/${transactionId}/execute`);
      setUploadMessage(`Output file generated successfully for Transaction ${transactionId}`);
      fetchTransactions();
    } catch (err) {
      setError("Failed to generate output file.");
    }
  };

  const handleDownload = (filename) => {
    if (!filename) return;
    const url = `${API_BASE_URL}/transactions/download/${filename}`;
    window.open(url, '_blank');
  };

  const handleDelete = async (transactionId) => {
    if (!window.confirm("Are you sure you want to delete this transaction?")) return;
    try {
      await axios.delete(`${API_BASE_URL}/transactions/${transactionId}`);
      setUploadMessage(`Transaction ${transactionId} deleted.`);
      fetchTransactions(); // Refresh the list after deletion
    } catch (err) {
      setError("Failed to delete transaction.");
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Transactions</h1>

      <div className="mb-6 p-4 border rounded-lg bg-white shadow-sm">
        <h2 className="text-xl font-semibold mb-3">Upload ISO 20022 File</h2>
        {error && <p className="text-red-500 mb-2">{error}</p>}
        {uploadMessage && <p className="text-green-600 mb-2">{uploadMessage}</p>}

        <div className="mb-3">
          <label htmlFor="flow-select" className="block text-sm font-medium text-gray-700">Select Flow:</label>
          <select
            id="flow-select"
            className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
            value={selectedFlowId}
            onChange={handleFlowChange}
          >
            <option value="">-- Select a Flow --</option>
            {flows.map((flow) => (
              <option key={flow.id} value={flow.id}>
                {flow.name} ({flow.message_format})
              </option>
            ))}
          </select>
        </div>

        <input type="file" onChange={handleFileChange} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
        <button
          onClick={handleUpload}
          disabled={!selectedFile || !selectedFlowId}
          className="mt-4 px-4 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Upload and Process
        </button>
      </div>

      <h2 className="text-xl font-semibold mb-3">Processed Transactions</h2>
      <div className="bg-white shadow-sm rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Flow</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Instruction ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Currency</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {transactions.map((tx) => (
              <tr key={tx.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{tx.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{flows.find(f => f.id === tx.flow_id)?.name || 'N/A'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tx.instruction_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tx.amount.toFixed(2)}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tx.currency}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    tx.status === 'Executed' ? 'bg-green-100 text-green-800' : 
                    tx.status === 'Validation Failed' ? 'bg-red-100 text-red-800' : 
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {tx.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  {tx.status !== 'Executed' && (
                    <button 
                      onClick={() => handleGenerateOutput(tx.id)}
                      className="text-blue-600 hover:text-blue-900 bg-blue-50 px-3 py-1 rounded-md disabled:opacity-50"
                      disabled={tx.status === 'Validation Failed'}
                    >
                      Generate Output
                    </button>
                  )}
                  {tx.status === 'Executed' && tx.raw_data?.output_file && (
                    <button 
                      onClick={() => handleDownload(tx.raw_data.output_file)}
                      className="text-green-600 hover:text-green-900 bg-green-50 px-3 py-1 rounded-md"
                    >
                      Download XML
                    </button>
                  )}
                  <button 
                    onClick={() => handleDelete(tx.id)}
                    className="text-red-600 hover:text-red-900 bg-red-50 px-3 py-1 rounded-md"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Transactions;