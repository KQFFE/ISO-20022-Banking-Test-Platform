import React from 'react';

const FlowList = ({ flows }) => {
    return (
        <div className="overflow-x-auto p-4">
            <table className="min-w-full bg-white border border-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th className="px-4 py-2 border">Flow Name</th>
                        <th className="px-4 py-2 border">Direction</th>
                        <th className="px-4 py-2 border">Message Format</th>
                        <th className="px-4 py-2 border">BIC Codes</th>
                        <th className="px-4 py-2 border">IBANs</th>
                        <th className="px-4 py-2 border">Date Support</th>
                    </tr>
                </thead>
                <tbody>
                    {flows.map((flow) => (
                        <tr key={flow.id} className="hover:bg-gray-50">
                            <td className="px-4 py-2 border font-medium">{flow.name}</td>
                            <td className="px-4 py-2 border">
                                <span className={`px-2 py-1 rounded text-xs ${flow.direction === 'Inbound' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                                    {flow.direction}
                                </span>
                            </td>
                            <td className="px-4 py-2 border">{flow.message_format} ({flow.file_format})</td>
                            <td className="px-4 py-2 border text-sm">{flow.bic_codes.join(', ')}</td>
                            <td className="px-4 py-2 border text-sm">{flow.valid_ibans.join(', ')}</td>
                            <td className="px-4 py-2 border text-xs">
                                {flow.back_dated && <div>• Back Dated</div>}
                                {flow.future_dated && <div>• Future Dated</div>}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default FlowList;
