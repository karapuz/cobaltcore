import React from 'react';
import { ArrowLeft, Wrench } from 'lucide-react';

export default function UnderConstruction({ user, onBack, industry }) {
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col" style={{ paddingTop: '80px' }}>
      {/* Sub-header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button onClick={onBack} className="flex items-center text-gray-600 hover:text-gray-900 transition">
                <ArrowLeft className="w-5 h-5 mr-1" />
                <span className="text-sm font-medium">Back</span>
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <h1 className="text-lg font-bold text-gray-900">{industry}</h1>
            </div>
            {user && (
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-500">
                  Welcome, <span className="font-semibold text-gray-800">{user.name}</span>
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex items-center justify-center px-4">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-yellow-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <Wrench className="w-10 h-10 text-yellow-600" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 mb-3">Under Construction</h2>
          <p className="text-gray-600 mb-2">
            We're working hard to bring you industry-specific insights for <strong>{industry}</strong>.
          </p>
          <p className="text-sm text-gray-500">
            Check back soon for detailed analysis, reports, and data.
          </p>
        </div>
      </div>
    </div>
  );
}
