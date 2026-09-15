import React, { useState } from 'react';
import { X, RotateCcw } from 'lucide-react';

// Projection velocity fields, in editor order.
export const VELOCITY_FIELDS = [
  { key: 'revenue', label: 'Revenue' },
  { key: 'ebitda', label: 'EBITDA' },
  { key: 'free_cash_flow', label: 'Free Cash Flow' },
  { key: 'operating_cash_flow', label: 'Operating Cash Flow' },
  { key: 'debt', label: 'Debt' },
  { key: 'total_debt', label: 'Total Debt' },
  { key: 'net_debt', label: 'Net Debt' },
  { key: 'short_term_debt', label: 'Short Term Debt' },
  { key: 'interest', label: 'Interest' },
];

// Mirrors velocity_store.MIN_VELOCITY / MAX_VELOCITY so a typo is caught
// before the round trip. The server still validates; this is not the check.
export const MIN_VELOCITY = 0.5;
export const MAX_VELOCITY = 2.0;

export function velocityError(value) {
  if (value === '' || value === null || value === undefined) return 'required';
  const num = Number(value);
  if (Number.isNaN(num)) return 'not a number';
  if (num < MIN_VELOCITY || num > MAX_VELOCITY) {
    return `must be ${MIN_VELOCITY}–${MAX_VELOCITY}`;
  }
  return null;
}

// 1.03 -> "+3.0%/yr". The stored value is a multiplier; growth is what an
// analyst actually reasons about.
export function asAnnualGrowth(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return '—';
  const pct = (num - 1) * 100;
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(1)}%/yr`;
}

export default function VelocityEditorModal({
  tickerLabel,
  velocity,
  revision,
  isDefault,
  loading,
  onCommit,
  onReset,
  onClose,
}) {
  const [edited, setEdited] = useState({ ...(velocity || {}) });
  const [note, setNote] = useState('');

  const errors = VELOCITY_FIELDS
    .map(f => ({ ...f, error: velocityError(edited[f.key]) }))
    .filter(f => f.error);
  const valid = errors.length === 0;
  const dirty = VELOCITY_FIELDS.some(
    f => Number(edited[f.key]) !== Number((velocity || {})[f.key])
  );

  const handleChange = (key, value) => {
    setEdited(prev => ({ ...prev, [key]: value }));
  };

  const handleCommit = () => {
    const numeric = Object.fromEntries(
      VELOCITY_FIELDS.map(f => [f.key, Number(edited[f.key])])
    );
    onCommit(numeric, note.trim() || null);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] flex flex-col">

        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-bold text-gray-900">
              Projection Velocity: {tickerLabel}
            </h3>
            <p className="text-sm text-gray-500">
              {isDefault ? 'Defaults — never customised' : `Revision ${revision}`}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-6 py-3 bg-blue-50 border-b border-blue-100">
          <p className="text-sm text-blue-800">
            Per-year multiplier, compounded across each forecast horizon.
            1.00 holds flat; 1.03 grows 3% a year.
          </p>
        </div>

        <div className="px-6 py-4 overflow-y-auto">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {VELOCITY_FIELDS.map(field => {
              const value = edited[field.key];
              const fieldError = velocityError(value);
              const changed = Number(value) !== Number((velocity || {})[field.key]);
              return (
                <div key={field.key}>
                  <label className="block text-xs text-gray-500 mb-1">{field.label}</label>
                  <input
                    type="number"
                    step="0.01"
                    min={MIN_VELOCITY}
                    max={MAX_VELOCITY}
                    value={value ?? ''}
                    onChange={(e) => handleChange(field.key, e.target.value)}
                    className={`w-full px-2 py-1 border rounded font-mono text-sm ${
                      fieldError
                        ? 'border-red-400 bg-red-50'
                        : changed
                          ? 'border-blue-400 bg-blue-50'
                          : 'border-gray-300'
                    }`}
                  />
                  <p className={`text-xs mt-1 ${fieldError ? 'text-red-600' : 'text-gray-400'}`}>
                    {fieldError || asAnnualGrowth(value)}
                  </p>
                </div>
              );
            })}
          </div>

          <div className="mt-6">
            <label className="block text-xs text-gray-500 mb-1">
              Note (stored with the revision)
            </label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. bull case, post-earnings revision"
              className="w-full px-3 py-2 border border-gray-300 rounded text-sm"
            />
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
          <p className="text-xs text-gray-500 mb-3">
            Commit writes a new revision to the model store. Unlike weights and
            ranges, this is persisted and applies to every later run for this
            entity — closing without committing discards the edit.
          </p>
          <div className="flex justify-between items-center">
            <button
              onClick={onReset}
              disabled={loading || isDefault}
              className="flex items-center gap-2 px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 disabled:opacity-40 disabled:cursor-not-allowed transition"
            >
              <RotateCcw className="w-3 h-3" />
              Reset to Defaults
            </button>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
              >
                Cancel
              </button>
              <button
                onClick={handleCommit}
                disabled={!valid || !dirty || loading}
                className={`px-6 py-2 rounded-lg font-semibold transition ${
                  valid && dirty && !loading
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                {loading ? 'Committing...' : 'Commit'}
              </button>
            </div>
          </div>
          {!valid && (
            <p className="text-right text-sm text-red-600 mt-3">
              {errors.map(f => `${f.label} (${f.error})`).join(', ')}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}