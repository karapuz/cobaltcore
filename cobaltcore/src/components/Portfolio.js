import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ArrowLeft, TrendingUp, TrendingDown, BarChart3, RefreshCw, AlertCircle, Loader, X, FileText, Download } from 'lucide-react';
import authService from '../services/authService';

// ─────────────────────────────────────
// Helper functions
// ─────────────────────────────────────
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
  if (!rating) return 'bg-gray-100 text-gray-600';
  if (rating.startsWith('BBB') || rating.startsWith('A')) return 'bg-green-100 text-green-800';
  if (rating.startsWith('BB') || rating === 'B+') return 'bg-yellow-100 text-yellow-800';
  if (rating === 'B') return 'bg-orange-100 text-orange-800';
  return 'bg-red-100 text-red-800';
}

// ─────────────────────────────────────
// Column definitions
// ─────────────────────────────────────
const COLUMNS = [
  { key: 'dateCreated',      label: 'Date Created' },
  { key: 'id',               label: 'Computation ID' },
  { key: 'creditRating',     label: 'Rating' },
  { key: 'revenue',          label: 'Revenue' },
  { key: 'ebitdaMargin',     label: 'EBITDA Margin' },
  { key: 'fcfToDebt',        label: 'FCF / Total Debt' },
  { key: 'debtToEbitda',     label: 'Total Debt / EBITDA' },
  { key: 'netDebtToEbitda',  label: 'Net Debt / EBITDA' },
  { key: 'ebitdaToInterest', label: 'EBITDA / Interest' },
  { key: 'roce',             label: 'ROCE' },
  { key: 'interestCoverage', label: 'Interest Coverage' }
];

function formatCellValue(key, value) {
  switch (key) {
    case 'dateCreated':      return formatDate(value);
    case 'revenue':          return formatCurrency(value);
    case 'ebitdaMargin':     return `${value}%`;
    case 'fcfToDebt':        return value.toFixed(2);
    case 'debtToEbitda':     return `${value.toFixed(1)}x`;
    case 'netDebtToEbitda':  return `${value.toFixed(1)}x`;
    case 'ebitdaToInterest': return `${value.toFixed(1)}x`;
    case 'roce':             return `${value}%`;
    case 'interestCoverage': return `${value.toFixed(1)}x`;
    case 'creditRating':
      return (
        <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold ${getRatingColor(value)}`}>
          {value || 'N/A'}
        </span>
      );
    default: return value;
  }
}

// ─────────────────────────────────────
// Summary card component
// ─────────────────────────────────────
function SummaryCard({ title, value, trend, trendLabel }) {
  const isPositive = trend === 'up';
  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">{title}</p>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <div className="flex items-center mt-2">
        {isPositive
          ? <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
          : <TrendingDown className="w-4 h-4 text-green-500 mr-1" />
        }
        <span className="text-xs text-green-600 font-medium">{trendLabel}</span>
      </div>
    </div>
  );
}

// ─────────────────────────────────────
// Shared sub-header
// ─────────────────────────────────────
function PortfolioHeader({ onBack, user }) {
  return (
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
              <BarChart3 className="w-5 h-5 text-gray-700" />
              <h1 className="text-lg font-bold text-gray-900">Portfolio</h1>
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
  );
}

// ─────────────────────────────────────
// PDF Side Panel
// ─────────────────────────────────────
function PdfPanel({ row, onClose }) {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const urlRef = useRef(null); // track the blob URL so we can revoke it on unmount

  const fetchPdf = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const blobUrl = await authService.getCreditRatingPdf(row.id);
      urlRef.current = blobUrl;
      setPdfUrl(blobUrl);
    } catch (err) {
      setError(err.message || 'Failed to load PDF');
    } finally {
      setLoading(false);
    }
  }, [row.id]);

  useEffect(() => {
    fetchPdf();

    // Cleanup: revoke blob URL when panel unmounts or row changes
    return () => {
      if (urlRef.current) {
        URL.revokeObjectURL(urlRef.current);
        urlRef.current = null;
      }
    };
  }, [fetchPdf]);

  // ── Loading state ──
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 bg-gray-50">
        <Loader className="w-8 h-8 text-gray-400 animate-spin" />
        <p className="text-sm text-gray-500">Loading PDF report...</p>
      </div>
    );
  }

  // ── Error state ──
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 bg-gray-50 px-6">
        <div className="w-14 h-14 bg-red-50 rounded-full flex items-center justify-center">
          <AlertCircle className="w-7 h-7 text-red-500" />
        </div>
        <div className="text-center">
          <h3 className="text-sm font-semibold text-gray-900 mb-1">Failed to load PDF</h3>
          <p className="text-xs text-gray-500">{error}</p>
        </div>
        <button
          onClick={fetchPdf}
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-gray-900 text-white rounded-lg text-xs font-semibold hover:bg-gray-800 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry
        </button>
      </div>
    );
  }

  // ── PDF loaded ──
  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200 flex-shrink-0">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-gray-600" />
          <div>
            <p className="text-sm font-semibold text-gray-900">{row.id}</p>
            <p className="text-xs text-gray-500">
              Rating: <span className={`inline-block px-1.5 py-0.5 rounded-full text-xs font-semibold ${getRatingColor(row.creditRating)}`}>{row.creditRating}</span>
              <span className="ml-2">·</span> {formatDate(row.dateCreated)}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Download button */}
          <a
            href={pdfUrl}
            download={`${row.id}.pdf`}
            className="flex items-center gap-1 px-3 py-1.5 text-xs font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition"
          >
            <Download className="w-3.5 h-3.5" />
            Download
          </a>
          {/* Close button */}
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* PDF iframe */}
      <div className="flex-1 bg-gray-100">
        <iframe
          src={pdfUrl}
          title={`Credit Rating Report ${row.id}`}
          className="w-full h-full border-0"
          style={{ minHeight: '0' }} // needed so flex child doesn't blow past container
        />
      </div>
    </div>
  );
}

// ─────────────────────────────────────
// Main Portfolio component
// ─────────────────────────────────────
export default function Portfolio({ user, onBack }) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortConfig, setSortConfig] = useState({ key: 'dateCreated', direction: 'desc' });
  const [selectedRow, setSelectedRow] = useState(null); // the full row object (or null)

  const fetchPortfolio = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await authService.getPortfolio();
      setData(result.items);
    } catch (err) {
      setError(err.message || 'Failed to load portfolio data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPortfolio();
  }, [fetchPortfolio]);

  // Sorting
  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const sortedData = [...data].sort((a, b) => {
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
  const totalRevenue    = data.reduce((s, d) => s + d.revenue, 0);
  const avgEbitdaMargin = data.length ? (data.reduce((s, d) => s + d.ebitdaMargin, 0) / data.length).toFixed(1) : '0';
  const avgDebtToEbitda = data.length ? (data.reduce((s, d) => s + d.debtToEbitda, 0) / data.length).toFixed(1) : '0';
  const avgRoce         = data.length ? (data.reduce((s, d) => s + d.roce, 0) / data.length).toFixed(1) : '0';

  // ─────────────────────────────────────
  // Loading state
  // ─────────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col" style={{ paddingTop: '80px' }}>
        <PortfolioHeader onBack={onBack} user={user} />
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <Loader className="w-10 h-10 text-gray-400 animate-spin" />
          <p className="text-gray-500 text-sm">Loading portfolio data...</p>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────
  // Error state
  // ─────────────────────────────────────
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col" style={{ paddingTop: '80px' }}>
        <PortfolioHeader onBack={onBack} user={user} />
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="bg-white rounded-xl border border-red-200 shadow-sm p-8 max-w-md w-full text-center">
            <div className="w-14 h-14 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-7 h-7 text-red-500" />
            </div>
            <h2 className="text-lg font-bold text-gray-900 mb-2">Failed to load data</h2>
            <p className="text-sm text-gray-500 mb-6">{error}</p>
            <button
              onClick={fetchPortfolio}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-900 text-white rounded-lg text-sm font-semibold hover:bg-gray-800 transition"
            >
              <RefreshCw className="w-4 h-4" />
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────
  // Main render
  // ─────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingTop: '80px' }}>
      <PortfolioHeader onBack={onBack} user={user} />

      {/* Two-column layout when a PDF panel is open; single column otherwise */}
      <div className="flex h-[calc(100vh-144px)]">  {/* 144px = 80px header + 64px sub-header */}

        {/* ── Left column: summary cards + table ── */}
        <div className={`flex flex-col overflow-y-auto transition-all duration-300 ${selectedRow ? 'w-1/2' : 'w-full'}`}>
          <div className="max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1">
            {/* Summary Cards – hide on mobile when PDF is open to save space */}
            <div className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 ${selectedRow ? 'hidden lg:grid' : ''}`}>
              <SummaryCard title="Total Revenue"     value={formatCurrency(totalRevenue)} trend="up"   trendLabel="+12.5% this quarter" />
              <SummaryCard title="Avg EBITDA Margin" value={`${avgEbitdaMargin}%`}       trend="up"   trendLabel="+2.3% vs last month" />
              <SummaryCard title="Avg Debt / EBITDA" value={`${avgDebtToEbitda}x`}       trend="down" trendLabel="-0.4x vs last month" />
              <SummaryCard title="Avg ROCE"          value={`${avgRoce}%`}               trend="up"   trendLabel="+1.8% vs last month" />
            </div>

            {/* Table Header */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-gray-900">Credit Ratings</h2>
                <p className="text-sm text-gray-500">{data.length} records found</p>
              </div>
              <button
                onClick={fetchPortfolio}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition"
              >
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
                      {COLUMNS.map((col) => (
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
                    {sortedData.map((row, idx) => {
                      const isSelected = selectedRow?.id === row.id;
                      return (
                        <tr
                          key={row.id}
                          onClick={() => setSelectedRow(isSelected ? null : row)}
                          className={`
                            border-b border-gray-100 cursor-pointer transition
                            ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                            ${isSelected
                              ? 'bg-blue-50 ring-1 ring-inset ring-blue-300'
                              : 'hover:bg-blue-50'
                            }
                          `}
                        >
                          {COLUMNS.map((col) => (
                            <td key={col.key} className="px-4 py-3 text-sm text-gray-700 whitespace-nowrap">
                              {formatCellValue(col.key, row[col.key])}
                            </td>
                          ))}
                        </tr>
                      );
                    })}

                    {sortedData.length === 0 && (
                      <tr>
                        <td colSpan={COLUMNS.length} className="px-4 py-12 text-center">
                          <p className="text-gray-500 text-sm">No credit ratings found</p>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Table Footer */}
              <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                <span className="text-xs text-gray-500">
                  Showing {data.length} of {data.length} records
                </span>
                <span className="text-xs text-gray-400">
                  Last updated: {formatDate(new Date().toISOString().split('T')[0])}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Right column: PDF panel ── */}
        {selectedRow && (
          <div className="w-1/2 border-l border-gray-200 bg-white flex flex-col">
            <PdfPanel row={selectedRow} onClose={() => setSelectedRow(null)} />
          </div>
        )}
      </div>
    </div>
  );
}
