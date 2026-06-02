import React, { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL, fetchWithRetry } from '../utils/api';

function Batches() {
  const [batches, setBatches] = useState([]);
  const [error, setError] = useState('');

  const fetchBatches = useCallback(async () => {
    try {
      const response = await fetchWithRetry(`${API_BASE_URL}/transactions/`);
      // In this context, each Transaction record in the DB represents an uploaded Batch
      setBatches(response.data);
    } catch (err) {
      console.error("Error fetching batches:", err);
      setError("Failed to load batch data.");
    }
  }, []);

  useEffect(() => {
    fetchBatches();
  }, [fetchBatches]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Message Batches</h1>
      <p className="text-gray-600 mb-6">Overview of grouped ISO 20022 message instructions and their processing status.</p>

      {error && <p className="text-red-500 mb-4">{error}</p>}

      <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Message ID</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Transactions</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Amount</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {batches.map((batch) => (
              <tr key={batch.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-blue-600">{batch.instruction_id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {batch.raw_data?.message_type || 'pain.001'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {batch.raw_data?.batch_count || 1}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {(batch.raw_data?.batch_total || batch.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })} {batch.currency}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    batch.status === 'Executed' ? 'bg-green-100 text-green-800' : 
                    batch.status === 'Validation Failed' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {batch.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date().toLocaleDateString()}
                </td>
              </tr>
            ))}
            {batches.length === 0 && (
              <tr>
                <td colSpan="6" className="px-6 py-10 text-center text-gray-500">
                  No batches found. Go to the Payments tab to upload a file.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
          <h3 className="font-bold text-blue-800 mb-2">Reconciliation Logic</h3>
          <p className="text-sm text-blue-700">
            Batches are automatically reconciled based on the <code>&lt;MsgId&gt;</code> element. Duplicate Message IDs within a 24-hour window are flagged for review.
          </p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg border border-green-100">
          <h3 className="font-bold text-green-800 mb-2">Multi-Entry Support</h3>
          <p className="text-sm text-green-700">
            Grouped instructions are processed as a single unit to ensure atomic execution of payment files.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Batches;