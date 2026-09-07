import React, { useState, useEffect } from 'react';
import { ArrowLeft, Download, Settings, RotateCcw } from 'lucide-react';
import authService from '../services/authService';
import RangeEditorModal from './RangeEditorModal';

// Forecast columns rendered after VALUE / RANK. Field names match the
// `forecast_*` keys returned by /v0/pillar/values/historical.
const FORECAST_HORIZONS = [
  { key: 'forecast_1y', label: '1Y FORECAST', rankLabel: '1Y RANK' },
  { key: 'forecast_2y', label: '2Y FORECAST', rankLabel: '2Y RANK' },
];

function getRatingColor(rating) {
  if (!rating) return 'bg-gray-100 text-gray-800';
  if (rating.startsWith('AAA')) return 'bg-emerald-100 text-emerald-800';
  if (rating.startsWith('AA')) return 'bg-green-100 text-green-800';
  if (rating.startsWith('A')) return 'bg-lime-100 text-lime-800';
  if (rating.startsWith('BBB')) return 'bg-yellow-100 text-yellow-800';
  if (rating.startsWith('BB')) return 'bg-orange-100 text-orange-800';
  if (rating.startsWith('B')) return 'bg-orange-200 text-orange-900';
  return 'bg-red-100 text-red-800';
}

function getRatingBadge(rating) {
  return (
    <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getRatingColor(rating)}`}>
      {rating}
    </span>
  );
}

function formatNotch(notch) {
  if (notch === 0) return '0';
  if (notch > 0) return `+${notch}`;
  return `${notch}`;
}

export default function TickerAnalysis({ user, onBack, analysisData }) {
  const [data, setData] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editedWeights, setEditedWeights] = useState({});
  const [editedRanges, setEditedRanges] = useState({});
  const [rangeModalPillar, setRangeModalPillar] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { index, ticker } = analysisData || {};

  useEffect(() => {
    if (ticker) {
      loadPillarData();
    }
  }, [ticker]);

  const loadPillarData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await authService.getPillarValues(ticker.ticker_id);
      setData(response);
      const weights = {};
      const ranges = {};
      (response.pillars || []).forEach(p => {
        weights[p.id] = p.weight;
        ranges[p.id] = p.range_breakpoints;
      });
      setEditedWeights(weights);
      setEditedRanges(ranges);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleWeightChange = (pillarId, value) => {
    const numValue = parseFloat(value) / 100;
    setEditedWeights(prev => ({
      ...prev,
      [pillarId]: isNaN(numValue) ? 0 : numValue
    }));
  };

  const handleApplyChanges = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await authService.recalculatePillars(
        ticker.ticker_id,
        editedWeights,
        editedRanges
      );
      setData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    setEditMode(false);
    await loadPillarData();
  };

  const handleSaveRanges = async (pillarId, newRanges) => {
    const updatedRanges = {
      ...editedRanges,
      [pillarId]: newRanges
    };
    setEditedRanges(updatedRanges);
    setRangeModalPillar(null);

    setLoading(true);
    setError(null);
    try {
      const response = await authService.recalculatePillars(
        ticker.ticker_id,
        editedWeights,
        updatedRanges
      );
      setData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const totalWeight = Object.values(editedWeights).reduce((sum, w) => sum + (w || 0), 0);
  const weightsValid = Math.abs(totalWeight - 1) < 0.001;

  const handleDownloadCSV = () => {
    if (!data) return;
    const lines = [
      `Credit Analysis: ${ticker.ticker_name} (${ticker.ticker_id})`,
      `Index: ${index.index_name}`,
      '',
      ['Pillar', 'Value', 'Rank',
        ...FORECAST_HORIZONS.flatMap(h => [`${h.label} Value`, `${h.label} Rank`]),
        'Weight'].join(','),
      ...data.pillars.map(p =>
        [p.name, p.formatted_value, p.rank,
          ...FORECAST_HORIZONS.flatMap(h => [p[`${h.key}_formatted_value`], p[`${h.key}_rank`]]),
          `${(p.weight * 100).toFixed(0)}%`].join(',')
      ),
      '',
      `DSCR,${data.dscr.formatted_value}`,
      `DSCR Notch,${formatNotch(data.dscr.notch)} (${data.dscr.notch_reason})`,
      '',
      `Base Rating,${data.base_rating}`,
      `Compass Rating,${data.compass_rating}`
    ];
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${ticker.ticker_id}_credit_analysis.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!analysisData) {
    return <div className="p-8 text-center text-gray-500">No ticker selected</div>;
  }

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
              <div>
                <h1 className="text-lg font-bold text-gray-900">
                  {ticker.ticker_id} - {ticker.ticker_name}
                </h1>
                <p className="text-xs text-gray-500">{index.index_name}</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 text-sm">
                <span className="text-gray-600">Edit Mode</span>
                <button
                  onClick={() => setEditMode(!editMode)}
                  className={`relative w-12 h-6 rounded-full transition ${editMode ? 'bg-blue-600' : 'bg-gray-300'}`}
                >
                  <span className={`absolute top-1 w-4 h-4 bg-white rounded-full transition ${editMode ? 'left-7' : 'left-1'}`} />
                </button>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {loading && !data ? (
          <div className="text-center py-12 text-gray-500">Loading analysis...</div>
        ) : data ? (
          <>
            {/* Pillars Table */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6 overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-900 text-white">
                    <th className="text-left px-4 py-4 font-bold text-sm">PILLAR</th>
                    <th className="text-right px-4 py-4 font-bold text-sm">VALUE</th>
                    <th className="text-center px-4 py-4 font-bold text-sm">RANK</th>
                    {FORECAST_HORIZONS.map(h => (
                      <React.Fragment key={h.key}>
                        <th className="text-right px-4 py-4 font-bold text-sm bg-blue-900">{h.label}</th>
                        <th className="text-center px-4 py-4 font-bold text-sm bg-blue-900">{h.rankLabel}</th>
                      </React.Fragment>
                    ))}
                    <th className="text-center px-4 py-4 font-bold text-sm">WEIGHT</th>
                  </tr>
                </thead>
                <tbody>
                  {data.pillars.map((pillar, idx) => (
                    <tr key={pillar.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-4 py-4 font-semibold text-gray-900">
                        <div className="flex items-center gap-2">
                          {pillar.name}
                          {editMode && (
                            <button
                              onClick={() => setRangeModalPillar(pillar)}
                              className="p-1 text-gray-400 hover:text-blue-600 transition"
                              title="Edit ranges"
                            >
                              <Settings className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-4 text-right font-mono text-sm">{pillar.formatted_value}</td>
                      <td className="px-4 py-4 text-center">{getRatingBadge(pillar.rank)}</td>
                      {FORECAST_HORIZONS.map(h => (
                        <React.Fragment key={h.key}>
                          <td className="px-4 py-4 text-right font-mono text-sm bg-blue-50">
                            {pillar[`${h.key}_formatted_value`]}
                          </td>
                          <td className="px-4 py-4 text-center bg-blue-50">
                            {getRatingBadge(pillar[`${h.key}_rank`])}
                          </td>
                        </React.Fragment>
                      ))}
                      <td className="px-4 py-4 text-center">
                        {editMode ? (
                          <input
                            type="number"
                            min="0"
                            max="100"
                            step="1"
                            value={Math.round((editedWeights[pillar.id] || 0) * 100)}
                            onChange={(e) => handleWeightChange(pillar.id, e.target.value)}
                            className="w-16 px-2 py-1 border border-gray-300 rounded text-center"
                          />
                        ) : (
                          `${Math.round(pillar.weight * 100)}%`
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="bg-gray-100 font-bold">
                    <td colSpan={3 + FORECAST_HORIZONS.length * 2} className="px-4 py-4 text-right">TOTAL WEIGHT</td>
                    <td className={`px-4 py-4 text-center ${editMode && !weightsValid ? 'text-red-600' : ''}`}>
                      {editMode ? `${Math.round(totalWeight * 100)}%` : '100%'}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* DSCR Notching Section */}
            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
              <div className="bg-gray-800 text-white px-4 py-3">
                <h3 className="font-bold text-sm">DSCR NOTCHING</h3>
              </div>
              <div className="p-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Debt Service Coverage Ratio</p>
                    <p className="text-xl font-bold text-gray-900">{data.dscr.formatted_value}</p>
                    <p className="text-xs text-gray-400 mt-1">Operating Cash Flow / (Short Term Debt + Debt)</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Notch Adjustment</p>
                    <p className={`text-xl font-bold ${data.dscr.notch < 0 ? 'text-green-600' : data.dscr.notch > 0 ? 'text-red-600' : 'text-gray-900'}`}>
                      {formatNotch(data.dscr.notch)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">{data.dscr.notch_reason}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Compass Rating Card */}
            <div className="flex justify-center mb-8">
              <div className="bg-white rounded-lg border border-gray-200 px-10 py-6 text-center min-w-[320px]">
                <p className="text-sm text-gray-500 mb-4">COMPASS RATING</p>
                
                <div className="space-y-3 mb-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Base Score:</span>
                    <span className="font-mono text-sm">{data.base_score.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Base Rating:</span>
                    {getRatingBadge(data.base_rating)}
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">DSCR Notch:</span>
                    <span className={`font-mono text-sm font-bold ${data.dscr.notch < 0 ? 'text-green-600' : data.dscr.notch > 0 ? 'text-red-600' : 'text-gray-600'}`}>
                      {formatNotch(data.dscr.notch)}
                    </span>
                  </div>
                </div>
                
                <div className="border-t border-gray-200 pt-4">
                  <p className="text-xs text-gray-500 mb-2">FINAL RATING</p>
                  <span className={`inline-block px-6 py-3 rounded-lg text-3xl font-bold ${getRatingColor(data.compass_rating)}`}>
                    {data.compass_rating}
                  </span>
                </div>
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between items-center">
              <button
                onClick={handleDownloadCSV}
                className="flex items-center gap-2 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
              >
                <Download className="w-4 h-4" />
                Download CSV
              </button>

              {editMode && (
                <div className="flex gap-4">
                  <button
                    onClick={handleReset}
                    className="flex items-center gap-2 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
                  >
                    <RotateCcw className="w-4 h-4" />
                    Reset to Defaults
                  </button>
                  <button
                    onClick={handleApplyChanges}
                    disabled={!weightsValid || loading}
                    className={`px-8 py-3 rounded-lg font-semibold transition ${
                      weightsValid && !loading
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    {loading ? 'Applying...' : 'Apply Changes'}
                  </button>
                </div>
              )}
            </div>

            {editMode && !weightsValid && (
              <p className="text-center text-red-600 mt-4">
                Weights must sum to 100% (currently {Math.round(totalWeight * 100)}%)
              </p>
            )}
          </>
        ) : null}
      </div>

      {/* Range Editor Modal */}
      {rangeModalPillar && (
        <RangeEditorModal
          pillar={rangeModalPillar}
          currentRanges={editedRanges[rangeModalPillar.id] || rangeModalPillar.range_breakpoints}
          onSave={(newRanges) => handleSaveRanges(rangeModalPillar.id, newRanges)}
          onClose={() => setRangeModalPillar(null)}
        />
      )}
    </div>
  );
}