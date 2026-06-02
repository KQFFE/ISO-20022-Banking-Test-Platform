import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { API_BASE_URL, fetchWithRetry } from '../utils/api';


function Dashboard() {
  const [stats, setStats] = useState({ total_transactions: 0, active_flows: 0, executed_transactions: 0 });

  const fetchStats = async () => {
    try {
      const response = await fetchWithRetry(`${API_BASE_URL}/stats`);
      setStats(response.data);
    } catch (err) {
      console.error("Error fetching dashboard stats:", err);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleClearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear all transaction history? This action cannot be undone.")) return;
    try {
      await axios.delete(`${API_BASE_URL}/transactions/`);
      await fetchStats();
    } catch (err) {
      console.error("Error clearing history:", err);
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Overview</h1>
        <button 
          onClick={handleClearHistory}
          className="px-4 py-2 bg-red-600 text-white text-sm font-semibold rounded-md hover:bg-red-700 transition-all shadow-sm focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
        >
          Clear History
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-white shadow rounded-lg">
          <h3 className="text-gray-500 text-sm font-medium">Total Transactions</h3>
          <p className="text-2xl font-semibold">{stats.total_transactions}</p>
        </div>
        <div className="p-4 bg-white shadow rounded-lg">
          <h3 className="text-gray-500 text-sm font-medium">Active Flows</h3>
          <p className="text-2xl font-semibold">{stats.active_flows}</p>
        </div>
        <div className="p-4 bg-white shadow rounded-lg">
          <h3 className="text-gray-500 text-sm font-medium">Executed Transactions</h3>
          <p className="text-2xl font-semibold">{stats.executed_transactions}</p>
        </div>
        <div className="p-4 bg-white shadow rounded-lg">
          <h3 className="text-gray-500 text-sm font-medium">Success Rate</h3>
          <p className="text-2xl font-semibold">
            {stats.total_transactions > 0 
              ? ((stats.executed_transactions / stats.total_transactions) * 100).toFixed(1) 
              : 100}%
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;