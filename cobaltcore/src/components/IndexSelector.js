import React, { useState, useEffect } from 'react';
import { ArrowLeft, ChevronRight, Search, TrendingUp } from 'lucide-react';
import authService from '../services/authService';

export default function IndexSelector({ user, onBack, onNavigate }) {
  const [indices, setIndices] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(null);
  const [tickers, setTickers] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load indices on mount
  useEffect(() => {
    loadIndices();
  }, []);

  const loadIndices = async () => {
    setLoading(true);
    try {
      const response = await authService.getIndices();
      setIndices(response.indices || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectIndex = async (index) => {
    setSelectedIndex(index);
    setLoading(true);
    setError(null);
    try {
      const response = await authService.getIndexTickers(index.index_id);
      setTickers(response.tickers || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectTicker = (ticker) => {
    onNavigate('ticker-analysis', {
      index: selectedIndex,
      ticker: ticker
    });
  };

  const filteredTickers = tickers.filter(t =>
    t.ticker_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    t.ticker_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingTop: '80px' }}>
      {/* Sub-header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button onClick={selectedIndex ? () => setSelectedIndex(null) : onBack} className="flex items-center text-gray-600 hover:text-gray-900 transition">
                <ArrowLeft className="w-5 h-5 mr-1" />
                <span className="text-sm font-medium">{selectedIndex ? 'Back to Indices' : 'Back'}</span>
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <h1 className="text-lg font-bold text-gray-900">Index Analysis</h1>
              </div>
            </div>
            {user && (
              <span className="text-sm text-gray-500">
                Welcome, <span className="font-semibold text-gray-800">{user.name}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {!selectedIndex ? (
          /* Step 1: Select Index */
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Select an Index</h2>
            <p className="text-gray-600 mb-8">Choose an index to view its constituent tickers</p>

            {loading ? (
              <div className="text-center py-12 text-gray-500">Loading indices...</div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200">
                {indices.map((index) => (
                  <button
                    key={index.index_id}
                    onClick={() => handleSelectIndex(index)}
                    className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition text-left"
                  >
                    <div>
                      <p className="font-semibold text-gray-900">{index.index_name}</p>
                      <p className="text-sm text-gray-500">{index.index_id}</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          /* Step 2: Select Ticker */
          <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{selectedIndex.index_name}</h2>
            <p className="text-gray-600 mb-6">Select a ticker to view credit analysis</p>

            {/* Search */}
            <div className="relative mb-6">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search tickers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            {loading ? (
              <div className="text-center py-12 text-gray-500">Loading tickers...</div>
            ) : (
              <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200 max-h-[500px] overflow-y-auto">
                {filteredTickers.map((ticker) => (
                  <button
                    key={ticker.ticker_id}
                    onClick={() => handleSelectTicker(ticker)}
                    className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition text-left"
                  >
                    <div className="flex items-center gap-4">
                      <span className="font-mono font-bold text-blue-600 w-16">{ticker.ticker_id}</span>
                      <span className="text-gray-900">{ticker.ticker_name}</span>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </button>
                ))}
                {filteredTickers.length === 0 && (
                  <div className="px-6 py-8 text-center text-gray-500">
                    No tickers found matching "{searchTerm}"
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}