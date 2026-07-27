import React from 'react';
import { ArrowLeft, Download, CheckCircle } from 'lucide-react';

// Rating badge color helper
function getRatingColor(rating) {
  if (!rating) return 'bg-gray-100 text-gray-800';
  if (rating.startsWith('AAA') || rating.startsWith('AA')) return 'bg-green-100 text-green-800';
  if (rating.startsWith('A')) return 'bg-green-50 text-green-700';
  if (rating.startsWith('BBB')) return 'bg-yellow-100 text-yellow-800';
  if (rating.startsWith('BB')) return 'bg-orange-100 text-orange-800';
  if (rating.startsWith('B')) return 'bg-orange-200 text-orange-900';
  return 'bg-red-100 text-red-800';
}

export default function CreditScoreResults({ user, onBack, onNavigate, resultData }) {
  // Extract results from nested structure or use defaults
  const apiResults = resultData?.results || resultData || {};
  
  const data = {
    sector: apiResults.sector || resultData?.sector || 'Industrials',
    industry: apiResults.industry || resultData?.industry || 'Cotton',
    compassRating: apiResults.compassRating || 'BB+',
    factors: apiResults.factors || [
      { name: 'Revenue Scale ($ millions)', weight: '15.00%', metric: '$115.00M', score: 'AA' },
      { name: 'EBITDA Margin', weight: '15.00%', metric: '30%', score: 'AA' },
      { name: 'Free Cash Flow / Debt', weight: '25.00%', metric: '30%', score: 'BBB-' },
      { name: 'Total Debt / EBITDA', weight: '25.00%', metric: '1.2 x', score: 'BB' },
      { name: 'Net Debt / EBITDA', weight: '10.00%', metric: '1.2 x', score: 'BB' },
      { name: 'EBITDA / Interest', weight: '10.00%', metric: '1.2 x', score: 'BB' },
    ]
  };

  const handleDownloadCSV = () => {
    // Generate CSV content
    const lines = [
      'Financial Scenario Analysis - Base Model Results',
      '',
      `Sector,${data.sector}`,
      `Industry,${data.industry}`,
      '',
      'Financial Pillar Rating,Industry Weights,Forecast Weighted Metrics,Factor Letter Score',
      ...(data.factors || []).map(f => `${f.name},${f.weight},${f.metric},${f.score}`),
      '',
      `Compass Rating,${data.compassRating}`
    ];

    const csvContent = lines.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'credit_score_results.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDone = () => {
    onNavigate('home');
  };

  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingTop: '80px' }}>
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
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <h1 className="text-lg font-bold text-gray-900">Credit Score Results</h1>
              </div>
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Title Section */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 italic">
            Financial Scenario Analysis - Base Model Results
          </h2>
        </div>

        {/* Download Button */}
        <div className="mb-8">
          <button
            onClick={handleDownloadCSV}
            className="flex items-center gap-2 px-6 py-3 border-2 border-gray-800 rounded-full text-gray-800 font-semibold hover:bg-gray-50 transition"
          >
            <Download className="w-4 h-4" />
            DOWNLOAD AS CSV
          </button>
        </div>

        {/* Sector/Industry Info */}
        <div className="mb-8">
          <table className="border border-gray-300">
            <tbody>
              <tr>
                <td className="bg-gray-900 text-white font-bold px-6 py-2 border border-gray-300">Sector</td>
                <td className="px-8 py-2 border border-gray-300 bg-white">{data.sector}</td>
              </tr>
              <tr>
                <td className="bg-gray-900 text-white font-bold px-6 py-2 border border-gray-300">Industry</td>
                <td className="px-8 py-2 border border-gray-300 bg-white">{data.industry}</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Financial Pillar Ratings Table */}
        <div className="bg-white border border-gray-300 rounded-lg overflow-hidden mb-8">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-900 text-white">
                <th className="text-left px-6 py-4 font-bold text-sm">
                  Financial Pillar Rating
                </th>
                <th className="text-left px-6 py-4 font-bold text-sm">
                  Industry Weights
                </th>
                <th className="text-left px-6 py-4 font-bold text-sm">
                  FORECAST WEIGHTED<br />METRICS
                </th>
                <th className="text-left px-6 py-4 font-bold text-sm">
                  FACTOR LETTER SCORE
                </th>
              </tr>
            </thead>
            <tbody>
              {(data.factors || []).map((factor, idx) => (
                <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-3 font-semibold text-gray-900 border-t border-gray-200">
                    {factor.name}
                  </td>
                  <td className="px-6 py-3 text-center border-t border-gray-200">
                    {factor.weight}
                  </td>
                  <td className="px-6 py-3 text-center font-bold border-t border-gray-200">
                    {factor.metric}
                  </td>
                  <td className="px-6 py-3 border-t border-gray-200">
                    <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${getRatingColor(factor.score)}`}>
                      {factor.score}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Compass Rating */}
        <div className="mb-12">
          <table className="border border-gray-300">
            <tbody>
              <tr>
                <td className="bg-gray-900 text-white font-bold px-6 py-3 border border-gray-300 text-lg">
                  Compass Rating
                </td>
                <td className="px-8 py-3 border border-gray-300 bg-white">
                  <span className={`inline-block px-4 py-2 rounded-lg text-xl font-bold ${getRatingColor(data.compassRating)}`}>
                    {data.compassRating}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center">
          <button
            onClick={onBack}
            className="px-10 py-4 bg-gray-900 text-white font-bold text-lg rounded-full hover:bg-gray-800 transition"
          >
            Back
          </button>
          <button
            onClick={handleDone}
            className="px-10 py-4 bg-gray-900 text-white font-bold text-lg rounded-full hover:bg-gray-800 transition"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}