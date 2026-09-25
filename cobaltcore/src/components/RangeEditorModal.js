import React, { useState } from 'react';
import { X } from 'lucide-react';

// The grade each bucket earns, best to worst. Mirrors BREAKPOINT_TO_RATING
// in model_data/model_store.py: N breakpoints give N+1 buckets, so this has
// one more entry than a pillar has breakpoints — the last one is the bucket
// below every breakpoint.
//
// This is NOT the full rating ladder. The breakpoints land on whole grades;
// the +/- variants are only reachable by the weighted score and the DSCR
// notch, never by a single pillar.
const BREAKPOINT_RATINGS = ['AAA', 'AA', 'A', 'BBB', 'BB', 'B', 'CCC', 'CC'];

function getRatingColor(rating) {
  if (!rating) return 'bg-gray-100 text-gray-800';
  // Longest prefix first: 'BBB'.startsWith('BB') is true, so the order of
  // these checks is load-bearing.
  if (rating.startsWith('AAA')) return 'bg-emerald-100 text-emerald-800';
  if (rating.startsWith('AA')) return 'bg-green-100 text-green-800';
  if (rating.startsWith('A')) return 'bg-lime-100 text-lime-800';
  if (rating.startsWith('BBB')) return 'bg-yellow-100 text-yellow-800';
  if (rating.startsWith('BB')) return 'bg-amber-100 text-amber-800';
  if (rating.startsWith('B')) return 'bg-orange-100 text-orange-800';
  if (rating.startsWith('CCC')) return 'bg-red-100 text-red-800';
  return 'bg-red-200 text-red-900';
}

export default function RangeEditorModal({ pillar, currentRanges, onSave, onClose }) {
  const [ranges, setRanges] = useState([...currentRanges]);
  const isIncreasing = pillar.is_increasing !== false;

  const handleRangeChange = (index, value) => {
    const newRanges = [...ranges];
    newRanges[index] = parseFloat(value) || 0;
    setRanges(newRanges);
  };

  const handleSave = () => {
    onSave(ranges);
  };

  // idx === ranges.length is the "below every breakpoint" bucket.
  const getRating = (idx) => BREAKPOINT_RATINGS[idx] ?? '?';
  const worstRating = getRating(ranges.length);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h3 className="text-lg font-bold text-gray-900">Edit Ranges: {pillar.name}</h3>
            <p className="text-sm text-gray-500">
              Type: {isIncreasing ? 'Increasing (higher = better)' : 'Decreasing (lower = better)'}
            </p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Current Value Indicator */}
        <div className="px-6 py-4 bg-blue-50 border-b border-blue-100">
          <p className="text-sm text-blue-800">
            Current Value: <span className="font-bold">{pillar.formatted_value}</span> → Rating: <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold ${getRatingColor(pillar.rank)}`}>{pillar.rank}</span>
          </p>
        </div>

        {/* Range Editor */}
        <div className="px-6 py-4 max-h-80 overflow-y-auto">
          <table className="w-full">
            <thead>
              <tr className="text-sm text-gray-500">
                <th className="text-left py-2">Rating</th>
                <th className="text-left py-2">Range</th>
                <th className="text-left py-2">Breakpoint</th>
              </tr>
            </thead>
            <tbody>
              {ranges.map((breakpoint, idx) => (
                <tr key={idx} className="border-t border-gray-100">
                  <td className="py-2">
                    <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getRatingColor(getRating(idx))}`}>
                      {getRating(idx)}
                    </span>
                  </td>
                  <td className="py-2 text-sm text-gray-600">
                    {isIncreasing
                      ? (idx === 0 ? `≥ ${breakpoint}` : `${ranges[idx]} - ${ranges[idx - 1]}`)
                      : (idx === 0 ? `≤ ${breakpoint}` : `${ranges[idx - 1]} - ${ranges[idx]}`)
                    }
                  </td>
                  <td className="py-2">
                    <input
                      type="number"
                      step="any"
                      value={breakpoint}
                      onChange={(e) => handleRangeChange(idx, e.target.value)}
                      className="w-24 px-2 py-1 border border-gray-300 rounded text-right"
                    />
                  </td>
                </tr>
              ))}
              <tr className="border-t border-gray-100">
                <td className="py-2">
                  <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getRatingColor(worstRating)}`}>
                    {worstRating}
                  </span>
                </td>
                <td className="py-2 text-sm text-gray-600">
                  {isIncreasing ? `< ${ranges[ranges.length - 1]}` : `> ${ranges[ranges.length - 1]}`}
                </td>
                <td className="py-2 text-sm text-gray-400">Worst</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-4 px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-100 transition"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Apply Changes
          </button>
        </div>
      </div>
    </div>
  );
}