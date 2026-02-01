import React, { useState } from 'react';
import { ArrowLeft, Activity, CheckCircle, XCircle, Loader } from 'lucide-react';

// Same demo data structure as Portfolio
const DEMO_SCENARIOS = [
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
    interestCoverage: 4.5
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
    interestCoverage: 7.2
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
    interestCoverage: 2.8
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
    interestCoverage: 5.9
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
    interestCoverage: 1.5
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
    interestCoverage: 9.8
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
    interestCoverage: 3.5
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
    interestCoverage: 12.3
  }
];

// Editable field definitions with validation rules
const EDITABLE_FIELDS = {
  revenue:          { min: 0,    max: null,  step: 1,    placeholder: '0' },
  ebitdaMargin:     { min: -100, max: 100,   step: 0.1,  placeholder: '0.0' },
  fcfToDebt:        { min: -10,  max: 10,    step: 0.01, placeholder: '0.00' },
  debtToEbitda:     { min: 0,    max: 100,   step: 0.1,  placeholder: '0.0' },
  netDebtToEbitda:  { min: -100, max: 100,   step: 0.1,  placeholder: '0.0' },
  ebitdaToInterest: { min: 0,    max: 1000,  step: 0.1,  placeholder: '0.0' },
  roce:             { min: -100, max: 100,   step: 0.1,  placeholder: '0.0' },
  interestCoverage: { min: 0,    max: 1000,  step: 0.1,  placeholder: '0.0' }
};

function formatCurrency(value) {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

function formatDate(dateStr) {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

export default function Scenarios({ user, onBack }) {
  // Deep copy of demo data used as editable state
  const [rows, setRows] = useState(() => DEMO_SCENARIOS.map(r => ({ ...r })));
  // Track which rows have been modified
  const [dirtyRows, setDirtyRows] = useState(new Set());
  // Track which rows have been submitted: id -> 'submitting' | 'success' | 'error'
  const [submitStatus, setSubmitStatus] = useState({});
  // Track validation errors: { rowId: { field: errorMsg } }
  const [errors, setErrors] = useState({});
  // Active/focused cell
  const [activeCell, setActiveCell] = useState(null);

  // Handle input change
  const handleChange = (rowId, field, value) => {
    setRows(prev =>
      prev.map(row => (row.id === rowId ? { ...row, [field]: value } : row))
    );
    setDirtyRows(prev => new Set(prev).add(rowId));
    // Clear any existing error on this cell
    setErrors(prev => {
      const updated = { ...prev };
      if (updated[rowId]) {
        delete updated[rowId][field];
        if (Object.keys(updated[rowId]).length === 0) delete updated[rowId];
      }
      return updated;
    });
    // Clear previous submit status for this row when editing again
    setSubmitStatus(prev => {
      const updated = { ...prev };
      delete updated[rowId];
      return updated;
    });
  };

  // Validate a single row
  const validateRow = (row) => {
    const rowErrors = {};
    Object.keys(EDITABLE_FIELDS).forEach(field => {
      const val = parseFloat(row[field]);
      const rules = EDITABLE_FIELDS[field];
      if (isNaN(val)) {
        rowErrors[field] = 'Must be a number';
      } else if (rules.min !== null && val < rules.min) {
        rowErrors[field] = `Min is ${rules.min}`;
      } else if (rules.max !== null && val > rules.max) {
        rowErrors[field] = `Max is ${rules.max}`;
      }
    });
    return rowErrors;
  };

  // Handle submit for a single row
  const handleSubmit = async (rowId) => {
    const row = rows.find(r => r.id === rowId);
    const rowErrors = validateRow(row);

    if (Object.keys(rowErrors).length > 0) {
      setErrors(prev => ({ ...prev, [rowId]: rowErrors }));
      return;
    }

    setSubmitStatus(prev => ({ ...prev, [rowId]: 'submitting' }));

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));

    // Simulate success (swap to 'error' randomly for demo)
    const success = Math.random() > 0.2;
    setSubmitStatus(prev => ({ ...prev, [rowId]: success ? 'success' : 'error' }));

    if (success) {
      setDirtyRows(prev => {
        const updated = new Set(prev);
        updated.delete(rowId);
        return updated;
      });
    }
  };

  // Reset a single row to original demo data
  const handleReset = (rowId) => {
    const original = DEMO_SCENARIOS.find(r => r.id === rowId);
    setRows(prev => prev.map(row => (row.id === rowId ? { ...original } : row)));
    setDirtyRows(prev => {
      const updated = new Set(prev);
      updated.delete(rowId);
      return updated;
    });
    setErrors(prev => {
      const updated = { ...prev };
      delete updated[rowId];
      return updated;
    });
    setSubmitStatus(prev => {
      const updated = { ...prev };
      delete updated[rowId];
      return updated;
    });
  };

  const columns = [
    { key: 'dateCreated', label: 'Date Created', editable: false },
    { key: 'id', label: 'Computation ID', editable: false },
    { key: 'revenue', label: 'Revenue', editable: true, suffix: '' },
    { key: 'ebitdaMargin', label: 'EBITDA Margin %', editable: true, suffix: '%' },
    { key: 'fcfToDebt', label: 'FCF / Total Debt', editable: true, suffix: '' },
    { key: 'debtToEbitda', label: 'Total Debt / EBITDA', editable: true, suffix: 'x' },
    { key: 'netDebtToEbitda', label: 'Net Debt / EBITDA', editable: true, suffix: 'x' },
    { key: 'ebitdaToInterest', label: 'EBITDA / Interest', editable: true, suffix: 'x' },
    { key: 'roce', label: 'ROCE %', editable: true, suffix: '%' },
    { key: 'interestCoverage', label: 'Interest Coverage', editable: true, suffix: 'x' },
    { key: 'submit', label: 'Submit', editable: false }
  ];

  const renderSubmitButton = (row) => {
    const status = submitStatus[row.id];
    const isDirty = dirtyRows.has(row.id);
    const hasError = errors[row.id] && Object.keys(errors[row.id]).length > 0;

    if (status === 'submitting') {
      return (
        <button disabled className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-200 text-gray-500 rounded-lg text-xs font-semibold cursor-not-allowed">
          <Loader className="w-3.5 h-3.5 animate-spin" />
          Sending...
        </button>
      );
    }

    if (status === 'success') {
      return (
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-green-600">
            <CheckCircle className="w-4 h-4" />
            <span className="text-xs font-semibold">Submitted</span>
          </div>
          <button
            onClick={() => handleReset(row.id)}
            className="text-xs text-gray-500 hover:text-gray-700 underline"
          >
            Reset
          </button>
        </div>
      );
    }

    if (status === 'error') {
      return (
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1 text-red-600">
            <XCircle className="w-4 h-4" />
            <span className="text-xs font-semibold">Failed</span>
          </div>
          <button
            onClick={() => handleSubmit(row.id)}
            className="text-xs text-blue-600 hover:text-blue-800 underline"
          >
            Retry
          </button>
        </div>
      );
    }

    return (
      <button
        onClick={() => handleSubmit(row.id)}
        disabled={!isDirty || hasError}
        className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition
          ${isDirty && !hasError
            ? 'bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md'
            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
      >
        Submit
      </button>
    );
  };

  const renderCell = (row, col) => {
    // Read-only columns
    if (col.key === 'dateCreated') return <span className="text-gray-600 text-xs">{formatDate(row.dateCreated)}</span>;
    if (col.key === 'id') return <span className="text-gray-800 text-xs font-mono">{row.id}</span>;
    if (col.key === 'submit') return renderSubmitButton(row);

    // Editable columns
    const rules = EDITABLE_FIELDS[col.key];
    const hasError = errors[row.id]?.[col.key];
    const isActive = activeCell?.rowId === row.id && activeCell?.field === col.key;
    const isDirty = dirtyRows.has(row.id);
    const originalValue = DEMO_SCENARIOS.find(r => r.id === row.id)?.[col.key];
    const valueChanged = parseFloat(row[col.key]) !== originalValue;

    return (
      <div className="relative">
        <div className="flex items-center">
          <input
            type="number"
            value={row[col.key]}
            min={rules.min}
            max={rules.max}
            step={rules.step}
            onChange={(e) => handleChange(row.id, col.key, e.target.value)}
            onFocus={() => setActiveCell({ rowId: row.id, field: col.key })}
            onBlur={() => setActiveCell(null)}
            className={`
              w-full px-2 py-1 text-xs rounded-md outline-none transition
              ${hasError
                ? 'border border-red-400 bg-red-50 focus:ring-1 focus:ring-red-400'
                : isActive
                  ? 'border border-blue-400 bg-white focus:ring-1 focus:ring-blue-400'
                  : valueChanged
                    ? 'border border-yellow-300 bg-yellow-50'
                    : 'border border-gray-200 bg-gray-50 hover:border-gray-300'
              }
            `}
          />
          {col.suffix && (
            <span className="ml-1 text-xs text-gray-400 whitespace-nowrap">{col.suffix}</span>
          )}
        </div>
        {hasError && (
          <span className="absolute -bottom-4 left-0 text-xs text-red-500 whitespace-nowrap z-10">
            {hasError}
          </span>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Bar */}
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
                <Activity className="w-5 h-5 text-gray-700" />
                <h1 className="text-lg font-bold text-gray-900">Scenarios</h1>
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
        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 mb-6">
          <div className="flex items-start gap-3">
            <Activity className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-blue-900">How to use Scenarios</h3>
              <p className="text-sm text-blue-700 mt-1">
                Edit any financial metric directly in the table below to run a credit rating scenario. 
                Modified fields are highlighted in yellow. Click <strong>Submit</strong> on any row to publish 
                your scenario. Use <strong>Reset</strong> to revert a row back to its original values.
              </p>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-6 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-gray-200 bg-gray-50"></div>
            <span className="text-xs text-gray-500">Original value</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-yellow-300 bg-yellow-50"></div>
            <span className="text-xs text-gray-500">Modified</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-blue-400 bg-white"></div>
            <span className="text-xs text-gray-500">Active</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-red-400 bg-red-50"></div>
            <span className="text-xs text-gray-500">Error</span>
          </div>
          <span className="text-xs text-gray-400 ml-auto">
            {dirtyRows.size} row{dirtyRows.size !== 1 ? 's' : ''} modified
          </span>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {columns.map((col) => (
                    <th key={col.key} className="px-3 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
                      <div className="flex items-center gap-1">
                        {col.label}
                        {col.editable && <span className="text-blue-400">✎</span>}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, idx) => (
                  <tr
                    key={row.id}
                    className={`
                      border-b border-gray-100 transition
                      ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
                      ${dirtyRows.has(row.id) ? 'ring-1 ring-inset ring-yellow-200' : ''}
                    `}
                  >
                    {columns.map((col) => (
                      <td key={col.key} className="px-3 py-3 whitespace-nowrap">
                        {renderCell(row, col)}
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
              {rows.length} scenarios available
            </span>
            <button
              onClick={() => {
                setRows(DEMO_SCENARIOS.map(r => ({ ...r })));
                setDirtyRows(new Set());
                setErrors({});
                setSubmitStatus({});
              }}
              className="text-xs text-gray-500 hover:text-gray-700 underline"
            >
              Reset all rows
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}