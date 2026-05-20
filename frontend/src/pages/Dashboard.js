import React, { useState, useEffect } from 'react';
import { API_BASE_URL, fetchWithRetry } from '../utils/api';


function Dashboard() {
  const [stats, setStats] = useState({ total_transactions: 0, active_flows: 0, executed_transactions: 0 });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetchWithRetry(`${API_BASE_URL}/stats`);
        setStats(response.data);
      } catch (err) {
        console.error("Error fetching dashboard stats:", err);
      }
    };
    fetchStats();
  }, []);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Overview</h1>
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
              : 0}%
          </p>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;