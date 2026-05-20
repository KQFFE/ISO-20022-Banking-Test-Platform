import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Flows from './pages/Flows';

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
          <Link to="/transactions" className="text-gray-600 hover:text-blue-500">Transactions</Link>
          <Link to="/flows" className="text-gray-600 hover:text-blue-500">Flow Definitions</Link>
        </nav>

        <main className="container mx-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/transactions" element={<Transactions />} />
            <Route path="/flows" element={<Flows />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;