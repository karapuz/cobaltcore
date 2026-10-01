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

// A negative notch IMPROVES the rating and a positive one worsens it, so the
// signed integer reads backwards. Show the direction instead. Same wording as
// the DSCR panel in TickerAnalysis.
function csvCell(value) {
  const text = String(value ?? '');
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

// The nine/ten basic figures, in the order the estimator collects them.
const BASIC_ROWS = [
  ['revenue', 'Revenue'],
  ['ebitda', 'EBITDA'],
  ['short_term_debt', 'Short Term Debt'],
  ['debt', 'Debt'],
  ['total_debt', 'Total Debt'],
  ['net_debt', 'Net Debt'],
  ['free_cash_flow', 'Free Cash Flow'],
  ['operating_cash_flow', 'Operating Cash Flow'],
  ['interest', 'Interest Expense'],
  ['income_tax_expense', 'Income Tax Expense'],
];

// Values arrive in absolute currency; the form collects millions, so show
// millions and keep the raw figure available in the CSV.
function asMillions(value) {
  if (value === undefined || value === null) return '—';
  return `${(value / 1e6).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function notchLabel(notch) {
  if (notch < 0) return 'Notch Up';
  if (notch > 0) return 'Notch Down';
  return 'No Change';
}

function notchColor(notch) {
  if (notch < 0) return 'text-green-600';
  if (notch > 0) return 'text-red-600';
  return 'text-gray-600';
}

export default function CreditScoreResults({ user, onBack, onNavigate, resultData }) {
  // Extract results from nested structure or use defaults
  const apiResults = resultData?.results || resultData || {};
  
  const data = {
    sector: apiResults.sector || resultData?.sector || 'Industrials',
    industry: apiResults.industry || resultData?.industry || 'Cotton',
    compassRating: apiResults.compassRating || apiResults.compass_rating || 'BB+',
    dscr: apiResults.dscr,
    baseScore: apiResults.base_score,
    baseRating: apiResults.base_rating,
    scoreBlend: apiResults.score_blend,
    pillars: apiResults.pillars,
    horizons: apiResults.forecast_horizons || [
      { key: 'forecast_1y', label: '1Y FORECAST' },
      { key: 'forecast_2y', label: '2Y FORECAST' },
    ],
    basics: apiResults.basic_financials,
    basicUnits: apiResults.basic_units,
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
      // Pillar table: actual, each forecast horizon, and the blended figure
      // that actually feeds the score.
      ...(data.pillars
        ? [
            ['Pillar', 'Value', 'Rank',
              ...data.horizons.flatMap(h => [`${h.label} Value`, `${h.label} Rank`]),
              'Blended Value', 'Score Rank', 'Weight'].join(','),
            ...data.pillars.map(p => [
              csvCell(p.name), csvCell(p.formatted_value), p.rank,
              ...data.horizons.flatMap(h => [
                csvCell(p[`${h.key}_formatted_value`]), p[`${h.key}_rank`]]),
              csvCell(p.blended_formatted_value), p.blended_numeric_rank,
              `${Math.round(p.weight * 100)}%`,
            ].join(',')),
          ]
        : [
            'Financial Pillar Rating,Industry Weights,Forecast Weighted Metrics,Factor Letter Score',
            ...(data.factors || []).map(f => `${f.name},${f.weight},${f.metric},${f.score}`),
          ]),
      '',
      // Raw inputs, so a surprising rating can be traced to what went in.
      ...(data.basics
        ? [
            `Basic values (${data.basicUnits || 'absolute currency units'})`,
            ['Financial', 'Trailing 12M',
              ...data.horizons.map(h => h.label)].join(','),
            ...BASIC_ROWS
              .filter(([field]) => data.basics.actual
                && data.basics.actual[field] !== undefined)
              .map(([field, label]) => [
                csvCell(label),
                data.basics.actual[field],
                ...data.horizons.map(h => (data.basics[h.key] || {})[field] ?? ''),
              ].join(',')),
            '',
          ]
        : []),
      ...(data.baseScore !== undefined && data.baseScore !== null
        ? [`Base Score,${data.baseScore.toFixed(2)}`, `Base Rating,${data.baseRating}`]
        : []),
      ...(data.dscr
        ? [`DSCR,${data.dscr.formatted_value}`,
           `DSCR Notch,${notchLabel(data.dscr.notch)} (${data.dscr.notch_reason})`]
        : []),
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

        {/* Financial Pillar Ratings — same columns as the index screen */}
        <div className="bg-white border border-gray-300 rounded-lg overflow-x-auto mb-8">
          {data.pillars ? (
            <table className="w-full">
              <thead>
                <tr className="bg-gray-900 text-white">
                  <th className="text-left px-4 py-4 font-bold text-sm">PILLAR</th>
                  <th className="text-right px-4 py-4 font-bold text-sm">VALUE</th>
                  <th className="text-center px-4 py-4 font-bold text-sm">RANK</th>
                  {data.horizons.map(h => (
                    <React.Fragment key={h.key}>
                      <th className="text-right px-4 py-4 font-bold text-sm bg-blue-900">{h.label}</th>
                      <th className="text-center px-4 py-4 font-bold text-sm bg-blue-900">
                        {h.label.replace(' FORECAST', '')} RANK
                      </th>
                    </React.Fragment>
                  ))}
                  <th className="text-right px-4 py-4 font-bold text-sm">BLENDED</th>
                  <th className="text-center px-4 py-4 font-bold text-sm">SCORE RANK</th>
                  <th className="text-center px-4 py-4 font-bold text-sm">WEIGHT</th>
                </tr>
              </thead>
              <tbody>
                {data.pillars.map((pillar, idx) => (
                  <tr key={pillar.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-3 font-semibold text-gray-900">{pillar.name}</td>
                    <td className="px-4 py-3 text-right font-mono text-sm">{pillar.formatted_value}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getRatingColor(pillar.rank)}`}>
                        {pillar.rank}
                      </span>
                    </td>
                    {data.horizons.map(h => (
                      <React.Fragment key={h.key}>
                        <td className="px-4 py-3 text-right font-mono text-sm bg-blue-50">
                          {pillar[`${h.key}_formatted_value`]}
                        </td>
                        <td className="px-4 py-3 text-center bg-blue-50">
                          <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getRatingColor(pillar[`${h.key}_rank`])}`}>
                            {pillar[`${h.key}_rank`]}
                          </span>
                        </td>
                      </React.Fragment>
                    ))}
                    <td className="px-4 py-3 text-right font-mono text-sm">{pillar.blended_formatted_value}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-1 rounded text-xs font-bold ${getRatingColor(pillar.blended_rank)}`}>
                        {pillar.blended_rank}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">{Math.round(pillar.weight * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            // Older payloads only carried the four-column factor summary.
            <table className="w-full">
              <thead>
                <tr className="bg-gray-900 text-white">
                  <th className="text-left px-6 py-4 font-bold text-sm">Financial Pillar Rating</th>
                  <th className="text-left px-6 py-4 font-bold text-sm">Industry Weights</th>
                  <th className="text-left px-6 py-4 font-bold text-sm">FORECAST WEIGHTED<br />METRICS</th>
                  <th className="text-left px-6 py-4 font-bold text-sm">FACTOR LETTER SCORE</th>
                </tr>
              </thead>
              <tbody>
                {(data.factors || []).map((factor, idx) => (
                  <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-6 py-3 font-semibold text-gray-900 border-t border-gray-200">{factor.name}</td>
                    <td className="px-6 py-3 text-center border-t border-gray-200">{factor.weight}</td>
                    <td className="px-6 py-3 text-center font-bold border-t border-gray-200">{factor.metric}</td>
                    <td className="px-6 py-3 border-t border-gray-200">
                      <span className={`inline-block px-3 py-1 rounded text-sm font-semibold ${getRatingColor(factor.score)}`}>
                        {factor.score}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Basic financials the engine was handed */}
        {data.basics && (
          <div className="bg-white border border-gray-300 rounded-lg overflow-x-auto mb-8">
            <div className="bg-gray-800 text-white px-4 py-3 flex items-center justify-between">
              <h3 className="font-bold text-sm">BASIC VALUES ($ millions)</h3>
              <span className="text-xs text-gray-300">as received by the rating engine</span>
            </div>
            <table className="w-full">
              <thead>
                <tr className="bg-gray-100">
                  <th className="text-left px-4 py-3 font-bold text-sm text-gray-700">FINANCIAL</th>
                  <th className="text-right px-4 py-3 font-bold text-sm text-gray-700">TRAILING 12M</th>
                  {data.horizons.map(h => (
                    <th key={h.key} className="text-right px-4 py-3 font-bold text-sm text-gray-700">
                      {h.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {BASIC_ROWS.filter(([field]) => data.basics.actual
                  && data.basics.actual[field] !== undefined).map(([field, label], idx) => (
                  <tr key={field} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-4 py-2 font-medium text-gray-900 border-t border-gray-200">{label}</td>
                    <td className="px-4 py-2 text-right font-mono text-sm border-t border-gray-200">
                      {asMillions(data.basics.actual[field])}
                    </td>
                    {data.horizons.map(h => (
                      <td key={h.key} className="px-4 py-2 text-right font-mono text-sm border-t border-gray-200">
                        {asMillions((data.basics[h.key] || {})[field])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* DSCR Notching — only when the engine reported it */}
        {data.dscr && (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-6">
            <div className="bg-gray-800 text-white px-4 py-3">
              <h3 className="font-bold text-sm">DSCR NOTCHING</h3>
            </div>
            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500 mb-1">Debt Service Coverage Ratio</p>
                <p className="text-xl font-bold text-gray-900">{data.dscr.formatted_value}</p>
                <p className="text-xs text-gray-400 mt-1">
                  DSCR = (EBITDA - Income Tax Expense) / (Interest Expense + Short Term Debt)
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-1">Notch Adjustment</p>
                <p className={`text-xl font-bold ${notchColor(data.dscr.notch)}`}>
                  {notchLabel(data.dscr.notch)}
                </p>
                <p className="text-xs text-gray-400 mt-1">{data.dscr.notch_reason}</p>
              </div>
            </div>
          </div>
        )}

        {/* Compass Rating */}
        <div className="flex justify-center mb-12">
          <div className="bg-white rounded-lg border border-gray-200 px-10 py-6 text-center min-w-[320px]">
            <p className="text-sm text-gray-500 mb-4">COMPASS RATING</p>

            {data.baseScore !== undefined && data.baseScore !== null && (
              <div className="space-y-3 mb-4">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Base Score:</span>
                  <span className="font-mono text-sm">{data.baseScore.toFixed(2)}</span>
                </div>
                {data.scoreBlend && (
                  <p className="text-xs text-gray-400 text-left">
                    Blend: {Math.round(data.scoreBlend.actual * 100)}% pillar
                    {` · ${Math.round((data.scoreBlend.forecast_1y || 0) * 100)}% 1Y`}
                    {` · ${Math.round((data.scoreBlend.forecast_2y || 0) * 100)}% 2Y`}
                  </p>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Base Rating:</span>
                  <span className={`px-2 py-1 rounded text-xs font-bold ${getRatingColor(data.baseRating)}`}>
                    {data.baseRating}
                  </span>
                </div>
                {data.dscr && (
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">DSCR Notch:</span>
                    <span className={`text-sm font-bold ${notchColor(data.dscr.notch)}`}>
                      {notchLabel(data.dscr.notch)}
                    </span>
                  </div>
                )}
              </div>
            )}

            <div className="border-t border-gray-200 pt-4">
              <p className="text-xs text-gray-500 mb-2">FINAL RATING</p>
              <span className={`inline-block px-6 py-3 rounded-lg text-3xl font-bold ${getRatingColor(data.compassRating)}`}>
                {data.compassRating}
              </span>
            </div>
          </div>
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