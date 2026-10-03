import React, { useState, useEffect, useCallback } from 'react';
import { ArrowLeft, Calendar, Download, BarChart3 } from 'lucide-react';
import authService from '../services/authService';

// Pillar ids in display order, with short headers for the per-pillar view.
const PILLARS = [
  { id: 'revenue_scale', short: 'REV' },
  { id: 'ebitda_margin', short: 'MARGIN' },
  { id: 'fcf_debt', short: 'FCF/TD' },
  { id: 'td_ebitda', short: 'TD/EB' },
  { id: 'nd_ebitda', short: 'ND/EB' },
  { id: 'ebitda_interest', short: 'COVER' },
];

function getRatingColor(rating) {
  if (!rating) return 'bg-gray-100 text-gray-800';
  // Longest prefix first: 'BBB'.startsWith('BB') is true.
  if (rating.startsWith('AAA')) return 'bg-emerald-100 text-emerald-800';
  if (rating.startsWith('AA')) return 'bg-green-100 text-green-800';
  if (rating.startsWith('A')) return 'bg-lime-100 text-lime-800';
  if (rating.startsWith('BBB')) return 'bg-yellow-100 text-yellow-800';
  if (rating.startsWith('BB')) return 'bg-amber-100 text-amber-800';
  if (rating.startsWith('B')) return 'bg-orange-100 text-orange-800';
  if (rating.startsWith('CCC')) return 'bg-red-100 text-red-800';
  return 'bg-red-200 text-red-900';
}

// What the grid shows. The payload carries all three, so switching is a
// client-side toggle rather than another 150-cell request.
const VIEWS = [
  { key: 'rating', label: 'Compass Rating' },
  { key: 'dscr', label: 'DSCR' },
  { key: 'score', label: 'Base Score' },
];

// A negative notch improves the rating, a positive one worsens it — so the
// signed integer reads backwards. Show the direction.
function notchLabel(notch) {
  if (notch < 0) return 'Notch Up';
  if (notch > 0) return 'Notch Down';
  return 'No Change';
}

function notchColor(notch) {
  if (notch < 0) return 'text-green-600';
  if (notch > 0) return 'text-red-600';
  return 'text-gray-400';
}

// The bands calculate_dscr_notch applies: >= 1.8 up, < 1.0 down.
function dscrColor(notch) {
  if (notch < 0) return 'bg-green-100 text-green-800';
  if (notch > 0) return 'bg-red-100 text-red-800';
  return 'bg-gray-100 text-gray-700';
}

export default function AnnualIndexAnalysis({ user, onBack, onNavigate }) {
  const [indices, setIndices] = useState([]);
  const [indexId, setIndexId] = useState('');
  const currentYear = new Date().getFullYear();
  const [startYear, setStartYear] = useState(currentYear - 4);
  const [endYear, setEndYear] = useState(currentYear);
  const [tickers, setTickers] = useState([]);
  const [selectedIds, setSelectedIds] = useState([]);
  const [tickerSearch, setTickerSearch] = useState('');
  const [view, setView] = useState('rating');
  const [loadingTickers, setLoadingTickers] = useState(false);
  const [matrix, setMatrix] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadIndices = useCallback(async () => {
    try {
      const response = await authService.getIndices();
      const list = response.indices || [];
      setIndices(list);
      if (list.length && !indexId) setIndexId(list[0].index_id);
    } catch (err) {
      setError(err.message);
    }
    // indexId is deliberately not a dependency: this seeds the default once
    // and must not re-run when the user changes the selection.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    loadIndices();
  }, [loadIndices]);

  const loadTickers = useCallback(async () => {
    if (!indexId) return;
    setLoadingTickers(true);
    setError(null);
    try {
      const response = await authService.getIndexTickers(indexId);
      setTickers(response.tickers || []);
    } catch (err) {
      setError(err.message);
      setTickers([]);
    } finally {
      setLoadingTickers(false);
    }
  }, [indexId]);

  // Changing the index invalidates the selection and any table built from it.
  useEffect(() => {
    setSelectedIds([]);
    setMatrix(null);
    loadTickers();
  }, [loadTickers]);

  const yearsValid = startYear <= endYear;
  const yearCount = yearsValid ? endYear - startYear + 1 : 0;
  const plannedCells = selectedIds.length * yearCount;
  // Mirrors MAX_CELLS in rating_matrix.py, so the limit is visible before
  // the request rather than arriving as a 400.
  const MAX_CELLS = 150;
  const withinLimit = plannedCells > 0 && plannedCells <= MAX_CELLS;
  const cellCount = matrix ? matrix.entities.length * matrix.years.length : 0;

  const visibleTickers = tickers.filter(t => {
    const needle = tickerSearch.toLowerCase();
    return !needle
      || (t.ticker_symbol || '').toLowerCase().includes(needle)
      || (t.ticker_name || '').toLowerCase().includes(needle);
  });

  const toggleTicker = (id) => {
    setSelectedIds(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const selectVisible = () => {
    setSelectedIds(prev => [
      ...prev,
      ...visibleTickers.map(t => t.ticker_id).filter(id => !prev.includes(id)),
    ]);
  };

  const handleRun = async () => {
    if (!yearsValid) {
      setError('Start year must not be after end year.');
      return;
    }
    if (!selectedIds.length) {
      setError('Select at least one ticker.');
      return;
    }
    setLoading(true);
    setError(null);
    setMatrix(null);
    try {
      const response = await authService.getRatingMatrix(
        indexId, startYear, endYear, selectedIds);
      setMatrix(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const cellFor = (entityId, year) =>
    (matrix && matrix.cells[entityId] && matrix.cells[entityId][year]) || null;

  const handleDownloadCSV = () => {
    if (!matrix) return;
    const esc = (value) => {
      const text = String(value ?? '');
      return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
    };

    const lines = [
      `Annual Index Analysis,${matrix.index_id || ''}`,
      `Years,${matrix.years.join(' - ')}`,
      `Rated,${matrix.rated},Failed,${matrix.failed}`,
      '',
      ['Ticker', 'Company', 'Year', 'Compass Rating', 'Base Rating',
        'Base Score', 'DSCR', 'DSCR Notch', 'DSCR Notch Reason',
        ...PILLARS.map(p => `${p.short} rank`), 'Error'].join(','),
    ];

    matrix.entities.forEach(entity => {
      matrix.years.forEach(year => {
        const cell = cellFor(entity.entity_id, year) || {};
        lines.push([
          esc(entity.ticker), esc(entity.name), year,
          esc(cell.compass_rating), esc(cell.base_rating),
          cell.base_score !== undefined ? cell.base_score.toFixed(2) : '',
          esc(cell.dscr), esc(notchLabel(cell.dscr_notch)), esc(cell.dscr_notch_reason),
          ...PILLARS.map(p => (cell.pillar_ranks || {})[p.id] ?? ''),
          esc(cell.error),
        ].join(','));
      });
    });

    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `annual_index_analysis_${matrix.index_id}_${matrix.years[0]}_${matrix.years[matrix.years.length - 1]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="px-8 flex items-center justify-between h-16">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-900 text-sm font-medium"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <span className="h-6 w-px bg-gray-300"></span>
            <div className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-600" />
              <h1 className="text-lg font-bold text-gray-900">Annual Index Analysis</h1>
            </div>
          </div>
          <span className="text-sm text-gray-500">
            Welcome, <span className="font-semibold text-gray-800">{user?.name || user?.username}</span>
          </span>
        </div>
      </div>

      <div className="px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            Ratings across an index and a range of years
          </h2>
          <p className="text-gray-600">
            Every cell is a full rating run on that company&apos;s annual filings for that year.
          </p>
        </div>

        {/* Selection */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-8">
          <div className="flex flex-wrap items-end gap-6">
            <div>
              <label className="block text-xs text-gray-500 mb-1 uppercase tracking-wide">Index</label>
              <select
                value={indexId}
                onChange={(e) => setIndexId(e.target.value)}
                className="px-4 py-2 border-2 border-gray-800 rounded-lg font-medium bg-white min-w-[260px]"
              >
                {indices.map(index => (
                  <option key={index.index_id} value={index.index_id}>
                    {index.index_name}{index.complete ? '' : ' (partial)'}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1 uppercase tracking-wide">From year</label>
              <input
                type="number"
                value={startYear}
                min={1990}
                max={currentYear + 1}
                onChange={(e) => setStartYear(Number(e.target.value))}
                className={`w-28 px-3 py-2 border-2 rounded-lg font-mono ${
                  yearsValid ? 'border-gray-800' : 'border-red-400 bg-red-50'
                }`}
              />
            </div>

            <div>
              <label className="block text-xs text-gray-500 mb-1 uppercase tracking-wide">To year</label>
              <input
                type="number"
                value={endYear}
                min={1990}
                max={currentYear + 1}
                onChange={(e) => setEndYear(Number(e.target.value))}
                className={`w-28 px-3 py-2 border-2 rounded-lg font-mono ${
                  yearsValid ? 'border-gray-800' : 'border-red-400 bg-red-50'
                }`}
              />
            </div>

            <button
              onClick={handleRun}
              disabled={!indexId || !yearsValid || !withinLimit || loading}
              className={`px-8 py-2.5 rounded-lg font-semibold transition ${
                indexId && yearsValid && withinLimit && !loading
                  ? 'bg-gray-900 text-white hover:bg-gray-800'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {loading ? 'Rating...' : 'Run Analysis'}
            </button>

            {matrix && (
              <button
                onClick={handleDownloadCSV}
                className="flex items-center gap-2 px-5 py-2.5 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition"
              >
                <Download className="w-4 h-4" />
                Download CSV
              </button>
            )}
          </div>

          {!yearsValid && (
            <p className="text-sm text-red-600 mt-3">
              Start year must not be after end year.
            </p>
          )}

          {/* Ticker selection — nothing runs until at least one is chosen,
              because a whole index across several years is a large job and
              should be an explicit choice rather than a default. */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-3">
                <label className="text-xs text-gray-500 uppercase tracking-wide">Tickers</label>
                <span className="text-sm text-gray-600">
                  {selectedIds.length} of {tickers.length} selected
                </span>
                {plannedCells > 0 && (
                  <span className={`text-sm ${withinLimit ? 'text-gray-500' : 'text-red-600'}`}>
                    · {plannedCells} cells{!withinLimit && ` (limit ${MAX_CELLS})`}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={tickerSearch}
                  onChange={(e) => setTickerSearch(e.target.value)}
                  placeholder="Filter..."
                  className="px-3 py-1.5 border border-gray-300 rounded text-sm w-40"
                />
                <button
                  onClick={selectVisible}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50"
                >
                  Select shown
                </button>
                <button
                  onClick={() => setSelectedIds([])}
                  disabled={!selectedIds.length}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-40"
                >
                  Clear
                </button>
              </div>
            </div>

            {loadingTickers ? (
              <p className="text-sm text-gray-500 py-4">Loading tickers...</p>
            ) : (
              <div className="max-h-56 overflow-y-auto border border-gray-200 rounded-lg">
                {visibleTickers.length === 0 ? (
                  <p className="text-sm text-gray-500 p-4">
                    {tickers.length ? 'No tickers match the filter.' : 'No tickers in this index.'}
                  </p>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
                    {visibleTickers.map(ticker => {
                      const checked = selectedIds.includes(ticker.ticker_id);
                      return (
                        <label
                          key={ticker.ticker_id}
                          className={`flex items-center gap-3 px-4 py-2 cursor-pointer border-b border-gray-100 ${
                            checked ? 'bg-blue-50' : 'hover:bg-gray-50'
                          }`}
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleTicker(ticker.ticker_id)}
                            className="w-4 h-4"
                          />
                          <span className="font-mono font-bold text-blue-600 w-16">
                            {ticker.ticker_symbol}
                          </span>
                          <span className="text-sm text-gray-700 truncate">
                            {ticker.ticker_name}
                          </span>
                        </label>
                      );
                    })}
                  </div>
                )}
              </div>
            )}

            {plannedCells > MAX_CELLS && (
              <p className="text-sm text-red-600 mt-3">
                {selectedIds.length} tickers x {yearCount} years is {plannedCells} ratings,
                over the {MAX_CELLS} limit. Select fewer tickers or a shorter range.
              </p>
            )}
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            {error}
          </div>
        )}

        {loading && (
          <div className="text-center py-16 text-gray-500">
            <Calendar className="w-6 h-6 mx-auto mb-3 animate-pulse" />
            Running one rating per company per year. This can take a moment.
          </div>
        )}

        {matrix && !loading && (
          <>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                {VIEWS.map(option => (
                  <button
                    key={option.key}
                    onClick={() => setView(option.key)}
                    className={`px-4 py-1.5 rounded-lg text-sm font-medium border transition ${
                      view === option.key
                        ? 'bg-gray-900 text-white border-gray-900'
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex items-center gap-6 mb-4 text-sm text-gray-600">
              <span>{matrix.entities.length} companies</span>
              <span>{matrix.years.length} years</span>
              <span>{cellCount} cells</span>
              <span className="text-green-700">{matrix.rated} rated</span>
              {matrix.failed > 0 && (
                <span className="text-red-600">{matrix.failed} without data</span>
              )}
            </div>

            <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-900 text-white">
                    <th className="text-left px-4 py-3 font-bold text-sm sticky left-0 bg-gray-900">
                      COMPANY
                    </th>
                    {matrix.years.map(year => (
                      <th key={year} className="text-center px-4 py-3 font-bold text-sm">
                        {year}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {matrix.entities.map((entity, idx) => (
                    <tr key={entity.entity_id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className={`px-4 py-3 sticky left-0 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                        <span className="font-mono font-bold text-blue-600 mr-3">{entity.ticker}</span>
                        <span className="text-gray-700 text-sm">{entity.name}</span>
                      </td>
                      {matrix.years.map(year => {
                        const cell = cellFor(entity.entity_id, year);
                        if (!cell || cell.error) {
                          return (
                            <td key={year} className="px-4 py-3 text-center" title={cell?.error || 'No data'}>
                              <span className="text-gray-300 text-sm">—</span>
                            </td>
                          );
                        }
                        // getdata falls forward when a year has no filings,
                        // so a cell can be showing a different year. Flag it
                        // rather than letting it pass as this year's figures.
                        const fellBack = cell.data_year
                          && String(cell.data_year) !== String(year);
                        const dscrTitle = `DSCR ${cell.dscr} — ${cell.dscr_notch_reason || ''} (${notchLabel(cell.dscr_notch)})`;
                        return (
                          <td key={year} className="px-4 py-3 text-center">
                            {view === 'rating' && (
                              <>
                                <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getRatingColor(cell.compass_rating)}`}>
                                  {cell.compass_rating}
                                </span>
                                {/* The notch is what separates the base rating
                                    from the final one, so it is shown beside
                                    it rather than hidden in a tooltip. */}
                                <p
                                  className={`text-xs mt-1 font-mono ${notchColor(cell.dscr_notch)}`}
                                  title={dscrTitle}
                                >
                                  {cell.base_score.toFixed(2)}
                                  {cell.dscr_notch !== 0 && (cell.dscr_notch < 0 ? ' ▲' : ' ▼')}
                                </p>
                              </>
                            )}

                            {view === 'dscr' && (
                              <>
                                <span
                                  className={`inline-block px-2 py-1 rounded text-xs font-bold ${dscrColor(cell.dscr_notch)}`}
                                  title={dscrTitle}
                                >
                                  {cell.dscr}
                                </span>
                                <p className={`text-xs mt-1 ${notchColor(cell.dscr_notch)}`}>
                                  {notchLabel(cell.dscr_notch)}
                                </p>
                              </>
                            )}

                            {view === 'score' && (
                              <>
                                <span className="font-mono text-sm text-gray-900">
                                  {cell.base_score.toFixed(2)}
                                </span>
                                <p className="text-xs text-gray-400 mt-1">
                                  {cell.base_rating}
                                </p>
                              </>
                            )}
                            {fellBack && (
                              <p
                                className="text-xs text-amber-600 mt-0.5"
                                title={`No ${year} filings; showing ${cell.data_year}`}
                              >
                                FY{cell.data_year}
                              </p>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <p className="text-xs text-gray-400 mt-4">
              {view === 'rating' && 'Badge is the Compass rating after DSCR notching; beneath it the base score, with ▲/▼ where the notch moved the rating.'}
              {view === 'dscr' && 'DSCR = (EBITDA - income tax expense) / (interest + short term debt), on the blended figures. Green notches up at ≥ 1.8, red notches down below 1.0.'}
              {view === 'score' && 'Weighted blended rank before notching, with the rating it falls in.'}
              {' '}A dash means no annual filings were available for that year — hover for the reason.
            </p>
          </>
        )}
      </div>
    </div>
  );
}