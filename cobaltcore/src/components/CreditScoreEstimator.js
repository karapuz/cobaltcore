import React, { useState } from 'react';
import { ArrowLeft, Download, Upload, Calculator } from 'lucide-react';
import authService from '../services/authService';

// Sector and Industry options
const SECTORS = [
  'Industrials',
  'Technology',
  'Healthcare',
  'Consumer Discretionary',
  'Consumer Staples',
  'Energy',
  'Materials',
  'Financials',
  'Utilities',
  'Real Estate',
  'Communication Services'
];

const INDUSTRIES_BY_SECTOR = {
  'Industrials': ['Cotton', 'Aerospace & Defense', 'Building Products', 'Construction & Engineering', 'Electrical Equipment', 'Industrial Conglomerates', 'Machinery', 'Trading Companies'],
  'Technology': ['Software', 'IT Services', 'Semiconductors', 'Hardware', 'Electronic Equipment'],
  'Healthcare': ['Pharmaceuticals', 'Biotechnology', 'Medical Devices', 'Healthcare Providers', 'Life Sciences'],
  'Consumer Discretionary': ['Automobiles', 'Hotels & Restaurants', 'Household Durables', 'Leisure Products', 'Textiles & Apparel', 'Retail'],
  'Consumer Staples': ['Beverages', 'Food Products', 'Household Products', 'Personal Products', 'Food & Staples Retailing'],
  'Energy': ['Oil & Gas Exploration', 'Oil & Gas Equipment', 'Oil & Gas Refining', 'Oil & Gas Storage'],
  'Materials': ['Chemicals', 'Construction Materials', 'Containers & Packaging', 'Metals & Mining', 'Paper & Forest Products'],
  'Financials': ['Banks', 'Capital Markets', 'Consumer Finance', 'Insurance', 'Mortgage REITs'],
  'Utilities': ['Electric Utilities', 'Gas Utilities', 'Multi-Utilities', 'Water Utilities', 'Independent Power'],
  'Real Estate': ['Equity REITs', 'Real Estate Management', 'Real Estate Development'],
  'Communication Services': ['Diversified Telecom', 'Wireless Telecom', 'Media', 'Entertainment', 'Interactive Media']
};

// Financial assessment factors
const FINANCIAL_FACTORS = [
  { key: 'revenueScale', label: 'Revenue Scale ($ millions)', prefix: '$ ', suffix: ' M' },
  { key: 'ebitda', label: 'EBITDA', prefix: '$ ', suffix: ' M' },
  { key: 'shortTermDebt', label: 'Short Term Debt', prefix: '$ ', suffix: ' M' },
  { key: 'debt', label: 'Debt', prefix: '$ ', suffix: ' M' },
  { key: 'totalDebt', label: 'Total Debt', prefix: '$ ', suffix: ' M' },
  { key: 'netDebt', label: 'Net Debt', prefix: '$ ', suffix: ' M' },
  { key: 'freeCashFlow', label: 'Free Cash Flow', prefix: '$ ', suffix: ' M' },
  { key: 'operatingCashFlow', label: 'Operating Cash Flow', prefix: '$ ', suffix: ' M' },
];

const TIME_PERIODS = [
  { key: 'trailing12', label: 'TRAILING\n12 MONTHS' },
  { key: 'oneYearForward', label: 'ONE YEAR\nFORWARD' },
  { key: 'twoYearsForward', label: 'TWO YEARS\nFORWARD' },
];

export default function CreditScoreEstimator({ user, onBack, onNavigate }) {
  const [sector, setSector] = useState('');
  const [industry, setIndustry] = useState('');
  const [isComputing, setIsComputing] = useState(false);
  const [error, setError] = useState(null);

  // Initialize form data for all factors across all time periods
  const [formData, setFormData] = useState(() => {
    const initial = {};
    FINANCIAL_FACTORS.forEach(factor => {
      TIME_PERIODS.forEach(period => {
        initial[`${factor.key}_${period.key}`] = 85; // Default value
      });
    });
    // Set some different defaults for revenue scale
    initial['revenueScale_trailing12'] = 95;
    initial['revenueScale_oneYearForward'] = 120;
    initial['revenueScale_twoYearsForward'] = 145;
    return initial;
  });

  const handleInputChange = (factorKey, periodKey, value) => {
    const key = `${factorKey}_${periodKey}`;
    setFormData(prev => ({
      ...prev,
      [key]: value === '' ? '' : parseFloat(value)
    }));
  };

  const handleSectorChange = (newSector) => {
    setSector(newSector);
    setIndustry(''); // Reset industry when sector changes
  };

  const handleCompute = async () => {
    if (!sector || !industry) {
      setError('Please select both Sector and Industry before computing.');
      return;
    }

    setIsComputing(true);
    setError(null);

    try {
      // Submit to API and get results
      const response = await authService.computeCreditScore({
        sector,
        industry,
        financialData: formData
      });

      // Navigate to results page with the response data
      onNavigate('credit-score-results', {
        sector,
        industry,
        financialData: formData,
        results: response
      });
    } catch (err) {
      setError(err.message || 'Failed to compute credit score');
    } finally {
      setIsComputing(false);
    }
  };

  const handleDownloadTemplate = () => {
    // Generate CSV template
    const headers = ['Financial Assessment Factor', ...TIME_PERIODS.map(p => p.label.replace('\n', ' '))];
    const rows = FINANCIAL_FACTORS.map(factor => [
      factor.label,
      formData[`${factor.key}_trailing12`] || '',
      formData[`${factor.key}_oneYearForward`] || '',
      formData[`${factor.key}_twoYearsForward`] || ''
    ]);

    const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'credit_score_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleLoadFromExcel = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.csv,.xlsx,.xls';
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        // For now, just show a message - full implementation would parse the file
        alert(`File "${file.name}" selected. CSV parsing would be implemented here.`);
      }
    };
    input.click();
  };

  const availableIndustries = sector ? INDUSTRIES_BY_SECTOR[sector] || [] : [];

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
                <Calculator className="w-5 h-5 text-gray-700" />
                <h1 className="text-lg font-bold text-gray-900">Credit Score Estimator</h1>
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
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Financial Scenario Analysis - Base Model Inputs
          </h2>
          <p className="text-gray-600">
            Scenario Modeling Ratings Engine Service: Tweak deal terms and preview rating impact in real time.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4 mb-8">
          <button
            onClick={handleDownloadTemplate}
            className="flex items-center gap-2 px-6 py-3 border-2 border-gray-800 rounded-lg text-gray-800 font-semibold hover:bg-gray-50 transition"
          >
            <Download className="w-4 h-4" />
            DOWNLOAD TEMPLATE
          </button>
          <button
            onClick={handleLoadFromExcel}
            className="flex items-center gap-2 px-6 py-3 border-2 border-gray-800 rounded-lg text-gray-800 font-semibold hover:bg-gray-50 transition"
          >
            <Upload className="w-4 h-4" />
            LOAD FROM EXCEL
          </button>
        </div>

        {/* Sector/Industry Selection */}
        <div className="flex items-center gap-6 mb-8">
          <span className="text-gray-500 font-medium">Identify Sector/Industry</span>
          
          <select
            value={sector}
            onChange={(e) => handleSectorChange(e.target.value)}
            className="px-6 py-3 border-2 border-gray-800 rounded-lg text-gray-800 font-medium bg-white min-w-[200px]"
          >
            <option value="">Select/Type Sector</option>
            {SECTORS.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
            disabled={!sector}
            className={`px-6 py-3 border-2 border-gray-800 rounded-lg font-medium bg-white min-w-[200px] ${
              !sector ? 'opacity-50 cursor-not-allowed' : 'text-gray-800'
            }`}
          >
            <option value="">Select/Type Industry</option>
            {availableIndustries.map(i => (
              <option key={i} value={i}>{i}</option>
            ))}
          </select>
        </div>

        {/* Financial Assessment Table */}
        <div className="bg-white border border-gray-300 rounded-lg overflow-hidden mb-8">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-900 text-white">
                <th className="text-left px-6 py-4 font-bold text-sm">
                  FINANCIAL ASSESSMENT<br />FACTORS
                </th>
                {TIME_PERIODS.map(period => (
                  <th key={period.key} className="text-left px-6 py-4 font-bold text-sm whitespace-pre-line">
                    {period.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {FINANCIAL_FACTORS.map((factor, idx) => (
                <tr key={factor.key} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-6 py-4 font-semibold text-gray-900 text-right border-r border-gray-200">
                    {factor.label}
                  </td>
                  {TIME_PERIODS.map(period => (
                    <td key={period.key} className="px-6 py-4 text-center border-r border-gray-200 last:border-r-0">
                      <div className="flex items-center justify-center">
                        <span className="text-gray-600 mr-1">{factor.prefix}</span>
                        <input
                          type="number"
                          step="0.01"
                          value={formData[`${factor.key}_${period.key}`]}
                          onChange={(e) => handleInputChange(factor.key, period.key, e.target.value)}
                          className="w-24 px-2 py-1 border border-gray-300 rounded text-center focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <span className="text-gray-600 ml-1">{factor.suffix}</span>
                      </div>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {/* Compute Button */}
        <div className="flex justify-end">
          <button
            onClick={handleCompute}
            disabled={isComputing}
            className={`px-8 py-4 rounded-lg text-white font-bold text-lg transition ${
              isComputing
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-gray-900 hover:bg-gray-800'
            }`}
          >
            {isComputing ? 'Computing...' : 'Compute\nCompass Rate'}
          </button>
        </div>
      </div>
    </div>
  );
}
