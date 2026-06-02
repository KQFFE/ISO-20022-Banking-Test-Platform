import React from 'react';

function Mandates() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Mandates and Direct Debits</h1>
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
        <div className="flex">
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              Testing for <strong>Direct Debits (pain.008)</strong> and <strong>Mandate Management (pain.009/010)</strong> is currently in development.
            </p>
          </div>
        </div>
      </div>
      
      <div className="p-8 border-2 border-dashed border-gray-300 rounded-lg text-center text-gray-500">
        Workflow tools for Mandate initiation and DD sequence testing will appear here.
      </div>
    </div>
  );
}

export default Mandates;