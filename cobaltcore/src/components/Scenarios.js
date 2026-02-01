import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, Activity, CheckCircle, XCircle, Loader, RefreshCw, AlertCircle } from 'lucide-react';
import authService from '../services/authService';

// ─────────────────────────────────────
// Editable field validation rules
// ─────────────────────────────────────
const EDITABLE_FIELDS = {
  revenue:          { min: 0,    max: null,  step: 1 },
  ebitdaMargin:     { min: -100, max: 100,   step: 0.1 },
  fcfToDebt:        { min: -10,  max: 10,    step: 0.01 },
  debtToEbitda:     { min: 0,    max: 100,   step: 0.1 },
  netDebtToEbitda:  { min: -100, max: 100,   step: 0.1 },
  ebitdaToInterest: { min: 0,    max: 1000,  step: 0.1 },
  roce:             { min: -100, max: 100,   step: 0.1 },
  interestCoverage: { min: 0,    max: 1000,  step: 0.1 }
};

const COLUMNS = [
  { key: 'dateCreated',      label: 'Date Created',        editable: false },
  { key: 'id',               label: 'Computation ID',      editable: false },
  { key: 'revenue',          label: 'Revenue',             editable: true,  suffix: '' },
  { key: 'ebitdaMargin',     label: 'EBITDA Margin %',     editable: true,  suffix: '%' },
  { key: 'fcfToDebt',        label: 'FCF / Total Debt',    editable: true,  suffix: '' },
  { key: 'debtToEbitda',     label: 'Total Debt / EBITDA', editable: true,  suffix: 'x' },
  { key: 'netDebtToEbitda',  label: 'Net Debt / EBITDA',   editable: true,  suffix: 'x' },
  { key: 'ebitdaToInterest', label: 'EBITDA / Interest',   editable: true,  suffix: 'x' },
  { key: 'roce',             label: 'ROCE %',              editable: true,  suffix: '%' },
  { key: 'interestCoverage', label: 'Interest Coverage',   editable: true,  suffix: 'x' },
  { key: 'submit',           label: 'Submit',              editable: false }
];

function formatCurrency(value) {
  if (value >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

function formatDate(dateStr) {
  const date = new Date(dateStr + 'T00:00:00');
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

// ─────────────────────────────────────
// Shared sub-header
// ─────────────────────────────────────
function ScenariosHeader({ onBack, user }) {
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
              <Activity className="w-5 h-5 text-gray-700" />
              <h1 className="text-lg font-bold text-gray-900">Scenarios</h1>
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
// Main Scenarios component
// ─────────────────────────────────────
export default function Scenarios({ user, onBack }) {
  // Server data (source of truth for "original" values)
  const [serverData, setServerData] = useState([]);
  // Local editable copy
  const [rows, setRows] = useState([]);
  // Loading / error states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // Track modified rows
  const [dirtyRows, setDirtyRows] = useState(new Set());
  // Track submit status per row: 'submitting' | 'success' | 'error'
  const [submitStatus, setSubmitStatus] = useState({});
  // Track validation errors per row
  const [errors, setErrors] = useState({});
  // Track focused cell
  const [activeCell, setActiveCell] = useState(null);

  // ─────────────────────────────────
  // Fetch scenarios from backend
  // ─────────────────────────────────
  const fetchScenarios = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await authService.getScenarios();
      setServerData(result.items);
      setRows(result.items.map(r => ({ ...r })));
      setDirtyRows(new Set());
      setSubmitStatus({});
      setErrors({});
    } catch (err) {
      setError(err.message || 'Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  // ─────────────────────────────────
  // Input change handler
  // ─────────────────────────────────
  const handleChange = (rowId, field, value) => {
    setRows(prev =>
      prev.map(row => (row.id === rowId ? { ...row, [field]: value } : row))
    );
    setDirtyRows(prev => new Set(prev).add(rowId));
    // Clear field error
    setErrors(prev => {
      const updated = { ...prev };
      if (updated[rowId]) {
        delete updated[rowId][field];
        if (Object.keys(updated[rowId]).length === 0) delete updated[rowId];
      }
      return updated;
    });
    // Clear submit status so button reactivates
    setSubmitStatus(prev => {
      const updated = { ...prev };
      delete updated[rowId];
      return updated;
    });
  };

  // ─────────────────────────────────
  // Validation
  // ─────────────────────────────────
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

  // ─────────────────────────────────
  // Submit: calls backend PUT endpoint
  // ─────────────────────────────────
  const handleSubmit = async (rowId) => {
    const row = rows.find(r => r.id === rowId);
    const rowErrors = validateRow(row);

    if (Object.keys(rowErrors).length > 0) {
      setErrors(prev => ({ ...prev, [rowId]: rowErrors }));
      return;
    }

    setSubmitStatus(prev => ({ ...prev, [rowId]: 'submitting' }));

    try {
      // Build payload with only editable fields (parsed as numbers)
      const payload = {};
      Object.keys(EDITABLE_FIELDS).forEach(field => {
        payload[field] = parseFloat(row[field]);
      });

      // Call backend
      const updated = await authService.updateScenario(rowId, payload);

      // Update serverData so the row is no longer "dirty"
      setServerData(prev =>
        prev.map(r => (r.id === rowId ? { ...updated } : r))
      );

      setSubmitStatus(prev => ({ ...prev, [rowId]: 'success' }));
      setDirtyRows(prev => {
        const s = new Set(prev);
        s.delete(rowId);
        return s;
      });
    } catch (err) {
      setSubmitStatus(prev => ({ ...prev, [rowId]: 'error' }));
    }
  };

  // ─────────────────────────────────
  // Reset a single row to server state
  // ─────────────────────────────────
  const handleReset = (rowId) => {
    const original = serverData.find(r => r.id === rowId);
    if (original) {
      setRows(prev => prev.map(row => (row.id === rowId ? { ...original } : row)));
    }
    setDirtyRows(prev => { const s = new Set(prev); s.delete(rowId); return s; });
    setErrors(prev => { const u = { ...prev }; delete u[rowId]; return u; });
    setSubmitStatus(prev => { const u = { ...prev }; delete u[rowId]; return u; });
  };

  // ─────────────────────────────────
  // Render submit button per row
  // ─────────────────────────────────
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
          <button onClick={() => handleReset(row.id)} className="text-xs text-gray-500 hover:text-gray-700 underline">
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
          <button onClick={() => handleSubmit(row.id)} className="text-xs text-blue-600 hover:text-blue-800 underline">
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

  // ─────────────────────────────────
  // Render individual cell
  // ─────────────────────────────────
  const renderCell = (row, col) => {
    if (col.key === 'dateCreated') return <span className="text-gray-600 text-xs">{formatDate(row.dateCreated)}</span>;
    if (col.key === 'id')          return <span className="text-gray-800 text-xs font-mono">{row.id}</span>;
    if (col.key === 'submit')      return renderSubmitButton(row);

    // Editable cell
    const rules = EDITABLE_FIELDS[col.key];
    const hasError = errors[row.id]?.[col.key];
    const isActive = activeCell?.rowId === row.id && activeCell?.field === col.key;
    const originalValue = serverData.find(r => r.id === row.id)?.[col.key];
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
          {col.suffix && <span className="ml-1 text-xs text-gray-400 whitespace-nowrap">{col.suffix}</span>}
        </div>
        {hasError && (
          <span className="absolute -bottom-4 left-0 text-xs text-red-500 whitespace-nowrap z-10">
            {hasError}
          </span>
        )}
      </div>
    );
  };

  // ─────────────────────────────────
  // Loading state
  // ─────────────────────────────────
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col" style={{ paddingTop: '80px' }}>
        <ScenariosHeader onBack={onBack} user={user} />
        <div className="flex-1 flex flex-col items-center justify-center gap-4">
          <Loader className="w-10 h-10 text-gray-400 animate-spin" />
          <p className="text-gray-500 text-sm">Loading scenarios...</p>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────
  // Error state
  // ─────────────────────────────────
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col" style={{ paddingTop: '80px' }}>
        <ScenariosHeader onBack={onBack} user={user} />
        <div className="flex-1 flex items-center justify-center px-4">
          <div className="bg-white rounded-xl border border-red-200 shadow-sm p-8 max-w-md w-full text-center">
            <div className="w-14 h-14 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="w-7 h-7 text-red-500" />
            </div>
            <h2 className="text-lg font-bold text-gray-900 mb-2">Failed to load data</h2>
            <p className="text-sm text-gray-500 mb-6">{error}</p>
            <button
              onClick={fetchScenarios}
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

  // ─────────────────────────────────
  // Main render
  // ─────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50" style={{ paddingTop: '80px' }}>
      <ScenariosHeader onBack={onBack} user={user} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Instructions */}
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 mb-6">
          <div className="flex items-start gap-3">
            <Activity className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-blue-900">How to use Scenarios</h3>
              <p className="text-sm text-blue-700 mt-1">
                Edit any financial metric directly in the table below to run a credit rating scenario.
                Modified fields are highlighted in yellow. Click <strong>Submit</strong> on any row to save
                your changes to the server. Use <strong>Reset</strong> to revert a row back to its last saved values.
              </p>
            </div>
          </div>
        </div>

        {/* Legend + row counter */}
        <div className="flex items-center gap-6 mb-4 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded border border-gray-200 bg-gray-50"></div>
            <span className="text-xs text-gray-500">Saved value</span>
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
          <div className="ml-auto flex items-center gap-4">
            <span className="text-xs text-gray-400">
              {dirtyRows.size} row{dirtyRows.size !== 1 ? 's' : ''} modified
            </span>
            <button
              onClick={fetchScenarios}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Refresh
            </button>
          </div>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  {COLUMNS.map((col) => (
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
                    {COLUMNS.map((col) => (
                      <td key={col.key} className="px-3 py-3 whitespace-nowrap">
                        {renderCell(row, col)}
                      </td>
                    ))}
                  </tr>
                ))}

                {rows.length === 0 && (
                  <tr>
                    <td colSpan={COLUMNS.length} className="px-4 py-12 text-center">
                      <p className="text-gray-500 text-sm">No scenarios found</p>
                    </td>
                  </tr>
                )}
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
                setRows(serverData.map(r => ({ ...r })));
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