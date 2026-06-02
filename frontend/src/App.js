import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Payments from './pages/Payments';
import Mandates from './pages/Mandates';
import Batches from './pages/Batches';
import Flows from './pages/Flows';
import TestFiles from './pages/TestFiles';
import MarketRules from './pages/MarketRules';

function App() {
  return (
    <Router 
      future={{ 
        v7_startTransition: true, 
        v7_relativeSplatPath: true 
      }}
    >
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow-sm p-4 flex gap-6">
          <Link to="/" className="font-bold text-blue-600">Banking Test App</Link>
          <Link to="/" className="text-gray-600 hover:text-blue-500">Overview</Link>
          <Link to="/payments" className="text-gray-600 hover:text-blue-500">Payments</Link>
          <Link to="/transactions" className="text-gray-600 hover:text-blue-500">Transactions</Link>
          <Link to="/mandates" className="text-gray-600 hover:text-blue-500">Mandates and DD</Link>
          <Link to="/batches" className="text-gray-600 hover:text-blue-500">Batches</Link>
          <Link to="/flows" className="text-gray-600 hover:text-blue-500">Flow Definitions</Link>
          <Link to="/test-files" className="text-gray-600 hover:text-blue-500 ml-auto">Test Files</Link>
          <Link to="/market-rules" className="text-gray-600 hover:text-blue-500">Market Rules</Link>
        </nav>

        <main className="container mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/payments" element={<Payments />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/mandates" element={<Mandates />} />
            <Route path="/batches" element={<Batches />} />
            <Route path="/flows" element={<Flows />} />
            <Route path="/test-files" element={<TestFiles />} />
            <Route path="/market-rules" element={<MarketRules />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;