import React, { useState } from 'react';
import { ArrowLeft, TrendingUp, TrendingDown, BarChart3, RefreshCw } from 'lucide-react';

// Demo data
const DEMO_PORTFOLIO = [
  {
    id: 'CR-2024-001',
    dateCreated: '2024-01-15',
    revenue: 45200000,
    ebitdaMargin: 23.5,
    fcfToDebt: 0.42,
    debtToEbitda: 3.2,
    netDebtToEbitda: 2.8,
    ebitdaToInterest: 4.5,
    roce: 18.3,
    interestCoverage: 4.5,
    creditRating: 'BB+'
  },
  {
    id: 'CR-2024-002',
    dateCreated: '2024-02-20',
    revenue: 128000000,
    ebitdaMargin: 31.2,
    fcfToDebt: 0.68,
    debtToEbitda: 1.8,
    netDebtToEbitda: 1.5,
    ebitdaToInterest: 7.2,
    roce: 24.7,
    interestCoverage: 7.2,
    creditRating: 'BBB-'
  },
  {
    id: 'CR-2024-003',
    dateCreated: '2024-03-10',
    revenue: 8750000,
    ebitdaMargin: 15.8,
    fcfToDebt: 0.21,
    debtToEbitda: 5.1,
    netDebtToEbitda: 4.6,
    ebitdaToInterest: 2.8,
    roce: 9.1,
    interestCoverage: 2.8,
    creditRating: 'B'
  },
  {
    id: 'CR-2024-004',
    dateCreated: '2024-04-05',
    revenue: 67300000,
    ebitdaMargin: 28.9,
    fcfToDebt: 0.55,
    debtToEbitda: 2.4,
    netDebtToEbitda: 2.1,
    ebitdaToInterest: 5.9,
    roce: 21.4,
    interestCoverage: 5.9,
    creditRating: 'BBB-'
  },
  {
    id: 'CR-2024-005',
    dateCreated: '2024-05-18',
    revenue: 3200000,
    ebitdaMargin: 10.2,
    fcfToDebt: 0.12,
    debtToEbitda: 7.3,
    netDebtToEbitda: 6.8,
    ebitdaToInterest: 1.5,
    roce: 4.2,
    interestCoverage: 1.5,
    creditRating: 'CCC+'
  },
  {
    id: 'CR-2024-006',
    dateCreated: '2024-06-22',
    revenue: 89500000,
    ebitdaMargin: 34.1,
    fcfToDebt: 0.78,
    debtToEbitda: 1.2,
    netDebtToEbitda: 0.9,
    ebitdaToInterest: 9.8,
    roce: 28.5,
    interestCoverage: 9.8,
    creditRating: 'BBB'
  },
  {
    id: 'CR-2024-007',
    dateCreated: '2024-07-14',
    revenue: 22100000,
    ebitdaMargin: 19.4,
    fcfToDebt: 0.33,
    debtToEbitda: 4.0,
    netDebtToEbitda: 3.6,
    ebitdaToInterest: 3.5,
    roce: 13.8,
    interestCoverage: 3.5,
    creditRating: 'BB'
  },
  {
    id: 'CR-2024-008',
    dateCreated: '2024-08-30',
    revenue: 156000000,
    ebitdaMargin: 37.5,
    fcfToDebt: 0.85,
    debtToEbitda: 0.9,
    netDebtToEbitda: 0.6,
    ebitdaToInterest: 12.3,
    roce: 32.1,
    interestCoverage: 12.3,
    creditRating: 'BBB+'
  }
];

// Helper functions
function formatCurrency(value) {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

function formatDate(dateStr) {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function getRatingColor(rating) {
  if (rating.startsWith('BBB') || rating.startsWith('A') || rating.startsWith('AA') || rating.startsWith('AAA')) {
    return 'bg-green-100 text-green-800';
  } else if (rating.startsWith('BB') || rating.startsWith('B+')) {
    return 'bg-yellow-100 text-yellow-800';
  } else if (rating === 'B') {
    return 'bg-orange-100 text-orange-800';
  }
  return 'bg-red-100 text-red-800';
}

export default function Portfolio({ user, onBack }) {
  const [sortConfig, setSortConfig] = useState({ key: 'dateCreated', direction: 'desc' });
  const [selectedRow, setSelectedRow] = useState(null);

  // Sorting logic
  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const sortedData = [...DEMO_PORTFOLIO].sort((a, b) => {
    const dir = sortConfig.direction === 'asc' ? 1 : -1;
    if (a[sortConfig.key] < b[sortConfig.key]) return -1 * dir;
    if (a[sortConfig.key] > b[sortConfig.key]) return 1 * dir;
    return 0;
  });

  const SortIcon = ({ colKey }) => {
    if (sortConfig.key !== colKey) return <span className="ml-1 text-gray-300">↕</span>;
    return sortConfig.direction === 'asc' 
      ? <span className="ml-1 text-gray-900">↑</span> 
      : <span className="ml-1 text-gray-900">↓</span>;
  };

  // Summary stats
  const avgEbitdaMargin = (DEMO_PORTFOLIO.reduce((s, d) => s + d.ebitdaMargin, 0) / DEMO_PORTFOLIO.length).toFixed(1);
  const avgDebtToEbitda = (DEMO_PORTFOLIO.reduce((s, d) => s + d.debtToEbitda, 0) / DEMO_PORTFOLIO.length).toFixed(1);
  const totalRevenue = DEMO_PORTFOLIO.reduce((s, d) => s + d.revenue, 0);
  const avgRoce = (DEMO_PORTFOLIO.reduce((s, d) => s + d.roce, 0) / DEMO_PORTFOLIO.length).toFixed(1);

  const columns = [
    { key: 'dateCreated', label: 'Date Created' },
    { key: 'id', label: 'Computation ID' },
    { key: 'creditRating', label: 'Rating' },
    { key: 'revenue', label: 'Revenue' },
    { key: 'ebitdaMargin', label: 'EBITDA Margin' },
    { key: 'fcfToDebt', label: 'FCF / Total Debt' },
    { key: 'debtToEbitda', label: 'Total Debt / EBITDA' },
    { key: 'netDebtToEbitda', label: 'Net Debt / EBITDA' },
    { key: 'ebitdaToInterest', label: 'EBITDA / Interest' },
    { key: 'roce', label: 'ROCE' },
    { key: 'interestCoverage', label: 'Interest Coverage' }
  ];

  const formatCellValue = (key, value) => {
    switch (key) {
      case 'dateCreated': return formatDate(value);
      case 'revenue': return formatCurrency(value);
      case 'ebitdaMargin': return `${value}%`;
      case 'fcfToDebt': return value.toFixed(2);
      case 'debtToEbitda': return value.toFixed(1)+'x';
      case 'netDebtToEbitda': return value.toFixed(1)+'x';
      case 'ebitdaToInterest': return value.toFixed(1)+'x';
      case 'roce': return `${value}%`;
      case 'interestCoverage': return value.toFixed(1)+'x';
      case 'creditRating': return (
        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${getRatingColor(value)}`}>
          {value}
        </span>
      );
      default: return value;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="flex items-center text-gray-600 hover:text-gray-900 transition"
              >
                <ArrowLeft className="w-5 h-5 mr-1" />
                <span className="text-sm font-medium">Back</span>
              </button>
              <div className="h-6 w-px bg-gray-300"></div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-gray-700" />
                <h1 className="text-lg font-bold text-gray-900">Portfolio</h1>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-500">
                Welcome, <span className="font-semibold text-gray-800">{user?.name}</span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Total Revenue</p>
            <p className="text-2xl font-bold text-gray-900">{formatCurrency(totalRevenue)}</p>
            <div className="flex items-center mt-2">
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
              <span className="text-xs text-green-600 font-medium">+12.5% this quarter</span>
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Avg EBITDA Margin</p>
            <p className="text-2xl font-bold text-gray-900">{avgEbitdaMargin}%</p>
            <div className="flex items-center mt-2">
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
              <span className="text-xs text-green-600 font-medium">+2.3% vs last month</span>
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Avg Debt / EBITDA</p>
            <p className="text-2xl font-bold text-gray-900">{avgDebtToEbitda}x</p>
            <div className="flex items-center mt-2">
              <TrendingDown className="w-4 h-4 text-green-500 mr-1" />
              <span className="text-xs text-green-600 font-medium">-0.4x vs last month</span>
            </div>
          </div>
          <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Avg ROCE</p>
            <p className="text-2xl font-bold text-gray-900">{avgRoce}%</p>
            <div className="flex items-center mt-2">
              <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
              <span className="text-xs text-green-600 font-medium">+1.8% vs last month</span>
            </div>
          </div>
        </div>

        {/* Table Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-gray-900">Credit Ratings</h2>
            <p className="text-sm text-gray-500">{DEMO_PORTFOLIO.length} records found</p>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition">
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {columns.map((col) => (
                    <th
                      key={col.key}
                      onClick={() => handleSort(col.key)}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap cursor-pointer hover:text-gray-800 hover:bg-gray-100 transition"
                    >
                      {col.label}
                      <SortIcon colKey={col.key} />
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sortedData.map((row, idx) => (
                  <tr
                    key={row.id}
                    onClick={() => setSelectedRow(selectedRow === row.id ? null : row.id)}
                    className={`
                      border-b border-gray-100 cursor-pointer transition
                      ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                      ${selectedRow === row.id ? 'bg-blue-50 ring-1 ring-inset ring-blue-200' : 'hover:bg-blue-50'}
                    `}
                  >
                    {columns.map((col) => (
                      <td key={col.key} className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                        {formatCellValue(col.key, row[col.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Table Footer */}
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <span className="text-xs text-gray-500">
              Showing {DEMO_PORTFOLIO.length} of {DEMO_PORTFOLIO.length} records
            </span>
            <span className="text-xs text-gray-400">
              Last updated: {formatDate(new Date().toISOString().split('T')[0])}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}