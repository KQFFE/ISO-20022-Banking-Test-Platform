import React, { useState, useEffect, useCallback, useRef } from 'react'; // Import useRef
import axios from 'axios';
import { API_BASE_URL, fetchWithRetry } from '../utils/api'; // Import centralized API utilities


function Transactions() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [flows, setFlows] = useState([]);
  const [selectedFlowId, setSelectedFlowId] = useState('');
  const [transactions, setTransactions] = useState([]);
  const [uploadMessage, setUploadMessage] = useState('');
  const [error, setError] = useState('');
  const [errorDetailTx, setErrorDetailTx] = useState(null);
  const modalRef = useRef(null); // Ref for the modal container
  const prevActiveElement = useRef(null); // To store the element that had focus before modal opened

  const fetchTransactions = useCallback(async () => {
    try {
      const response = await fetchWithRetry(`${API_BASE_URL}/transactions/`);
      setTransactions(response.data);
    } catch (err) {
      console.error("Error fetching transactions:", err);
      setError("Failed to load transactions.");
    }
  }, []);

  const fetchFlows = useCallback(async () => {
    try {
      const response = await fetchWithRetry(`${API_BASE_URL}/flows/`);
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

  // Effect for modal accessibility (focus trapping and escape key)
  useEffect(() => {
    // Only run if the modal is open AND the ref has been attached to the DOM
    if (errorDetailTx && modalRef.current) {
      // Store the element that was focused before the modal opened
      prevActiveElement.current = document.activeElement;

      // Focus the first focusable element in the modal
      const focusableElements = modalRef.current.querySelectorAll(
        'button:not([disabled]), [href], input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusableElements.length > 0) {
        focusableElements[0].focus();
      }

      const handleKeyDown = (event) => {
        if (event.key === 'Escape') {
          setErrorDetailTx(null);
        } else if (event.key === 'Tab') {
          const firstElement = focusableElements[0];
          const lastElement = focusableElements[focusableElements.length - 1];

          if (event.shiftKey) { // Shift + Tab
            if (document.activeElement === firstElement) {
              lastElement.focus();
              event.preventDefault();
            }
          } else { // Tab
            if (document.activeElement === lastElement) {
              firstElement.focus();
              event.preventDefault();
            }
          }
        }
      };
      document.addEventListener('keydown', handleKeyDown);
      return () => {
        document.removeEventListener('keydown', handleKeyDown);
        // Return focus to the previously active element when modal closes
        if (prevActiveElement.current) {
          prevActiveElement.current.focus();
        }
      };
    }
  }, [errorDetailTx]); // Re-run effect when errorDetailTx changes (modal opens/closes)

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
      const response = await axios.post(`${API_BASE_URL}/transactions/upload/${selectedFlowId}`, formData, { // Direct axios.post for file upload (retries are complex)
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
      await axios.post(`${API_BASE_URL}/transactions/${transactionId}/execute`); // Direct axios.post for state-changing operation
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
      await axios.delete(`${API_BASE_URL}/transactions/${transactionId}`); // Direct axios.delete for state-changing operation
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="flex flex-col">
            <label htmlFor="flow-select" className="block text-sm font-medium text-gray-700 mb-1">Target Flow Configuration</label>
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
          <div className="flex flex-col">
            <label htmlFor="iso-file-upload" className="block text-sm font-medium text-gray-700 mb-1">ISO 20022 XML File</label>
            <input id="iso-file-upload" type="file" onChange={handleFileChange} className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
          </div>
        </div>
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
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Flow</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message ID</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Amount</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tx Count</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Currency</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {transactions.map((tx) => (
              <tr key={tx.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{tx.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{flows.find(f => f.id === tx.flow_id)?.name || 'N/A'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tx.instruction_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {(tx.raw_data?.batch_total || tx.amount).toFixed(2)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {tx.raw_data?.batch_count || 1}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{tx.currency}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {tx.status === 'Validation Failed' ? (
                    <button 
                      onClick={() => setErrorDetailTx(tx)}
                      className="px-2 py-1 rounded-full text-xs bg-red-100 text-red-800 hover:bg-red-200 transition-colors font-semibold underline decoration-dotted"
                      aria-label={`View validation errors for ${tx.instruction_id}`}
                    >
                      {tx.status}
                    </button>
                  ) : (
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      tx.status === 'Executed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-900'
                    }`}>
                      {tx.status}
                    </span>
                  )}
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

      {/* Validation Error Modal */}
      {errorDetailTx && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={() => setErrorDetailTx(null)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <div 
            ref={modalRef}
            className="bg-white rounded-lg max-w-lg w-full p-6 shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-center mb-4">
              <h3 id="modal-title" className="text-xl font-bold text-red-600">Validation Errors</h3>
              <button 
                onClick={() => setErrorDetailTx(null)}
                className="text-gray-400 hover:text-gray-600 focus:outline-none"
                aria-label="Close modal"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <p className="text-sm text-gray-600 mb-4">
              Message ID: <span className="font-mono font-bold">{errorDetailTx.instruction_id}</span>
            </p>
            <div className="bg-red-50 p-4 rounded-md max-h-60 overflow-y-auto border border-red-100">
              <ul className="list-disc list-inside space-y-2">
                {errorDetailTx.raw_data?.validation_errors?.length > 0 ? (
                  errorDetailTx.raw_data.validation_errors.map((err, idx) => (
                    <li key={idx} className="text-sm text-red-700">{err}</li>
                  ))
                ) : (
                  <li className="text-sm text-red-700">No specific validation errors found. Check flow configuration or file content.</li>
                )}
              </ul>
            </div>
            <div className="mt-6 flex justify-end">
              <button 
                onClick={() => setErrorDetailTx(null)}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Transactions;