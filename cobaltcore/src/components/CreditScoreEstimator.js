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
  { key: 'debt', label: 'Long Term Debt', prefix: '$ ', suffix: ' M' },
  { key: 'totalDebt', label: 'Total Debt', prefix: '$ ', suffix: ' M' },
  // Net Debt is not collected — it is derived as Total Debt - Cash &
  // Equivalents, so the two figures can never disagree.
  { key: 'cashEquivalents', label: 'Cash & Equivalents', prefix: '$ ', suffix: ' M' },
  { key: 'freeCashFlow', label: 'Free Cash Flow', prefix: '$ ', suffix: ' M' },
  { key: 'operatingCashFlow', label: 'Operating Cash Flow', prefix: '$ ', suffix: ' M' },
  // Interest expense feeds the EBITDA / Interest pillar, which carries real
  // weight in the rating. It used to be assumed at 5% of total debt; it is
  // collected now so the figure is the user's, not a guess.
  { key: 'interest', label: 'Interest Expense', prefix: '$ ', suffix: ' M' },
  // DSCR = (EBITDA - income tax expense) / (interest + short term debt).
  { key: 'incomeTaxExpense', label: 'Income Tax Expense', prefix: '$ ', suffix: ' M' },
];

const TIME_PERIODS = [
  { key: 'trailing12', label: 'TRAILING\n12 MONTHS' },
  { key: 'oneYearForward', label: 'ONE YEAR\nFORWARD' },
  { key: 'twoYearsForward', label: 'TWO YEARS\nFORWARD' },
];

// ─────────────────────────────────────
// CSV import
// ─────────────────────────────────────

// Row labels carrying the scenario's classification, written above the
// factor table by the template and read back on import.
const SECTOR_ROW_LABEL = 'Sector';
const INDUSTRY_ROW_LABEL = 'Industry';

// Minimal RFC-4180 reader: handles quoted fields, embedded commas, escaped
// quotes and CRLF. Small enough not to warrant a dependency, and the files
// this reads are ones we also write.
function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (inQuotes) {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i += 1; }
        else inQuotes = false;
      } else field += ch;
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ',') {
      row.push(field); field = '';
    } else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i += 1;
      row.push(field); field = '';
      rows.push(row); row = [];
    } else {
      field += ch;
    }
  }
  if (field !== '' || row.length) { row.push(field); rows.push(row); }
  return rows.filter(r => r.some(c => c.trim() !== ''));
}

function csvCell(value) {
  const text = String(value ?? '');
  return /[",\n\r]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

// Row labels are matched loosely so a file that has been through Excel still
// lines up: case, spacing, currency symbols and units are all ignored.
function normalizeLabel(text) {
  return String(text || '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

// "$ 1,234.50 M", "(500)" and "1 234" all parse. Returns null if it isn't a
// number, so the caller can report the row rather than storing NaN.
function parseAmount(raw) {
  let text = String(raw ?? '').trim();
  if (text === '') return null;
  let negative = false;
  if (/^\(.*\)$/.test(text)) { negative = true; text = text.slice(1, -1); }
  text = text.replace(/[$,\s]/g, '').replace(/[mM]$/, '');
  if (text.startsWith('-')) { negative = true; text = text.slice(1); }
  if (!/^\d*\.?\d+$/.test(text)) return null;
  const value = parseFloat(text);
  if (Number.isNaN(value)) return null;
  return negative ? -value : value;
}

export default function CreditScoreEstimator({ user, onBack, onNavigate }) {
  const [sector, setSector] = useState('');
  const [industry, setIndustry] = useState('');
  const [isComputing, setIsComputing] = useState(false);
  const [error, setError] = useState(null);
  const [importNotice, setImportNotice] = useState(null);

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
    // Interest at the blanket 85 would mean EBITDA / Interest of 1.0, which
    // rates CC and makes the untouched form look like a distressed issuer.
    // 5% of the default total debt matches the assumption this row replaces.
    TIME_PERIODS.forEach(period => {
      initial[`interest_${period.key}`] = 4.25;
      // Zero cash keeps Net Debt equal to Total Debt, which is what the
      // old Net Debt default produced.
      initial[`cashEquivalents_${period.key}`] = 0;
      // The blanket 85 here would make DSCR zero and notch every untouched
      // form down a grade; 15 is a plausible tax charge against EBITDA 85.
      initial[`incomeTaxExpense_${period.key}`] = 15;
    });
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
      setError('Sector and Industry are required. Load a file that includes them, or pick them above.');
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
    // Sector and industry travel with the file so a loaded scenario is
    // complete on its own and does not depend on what is selected on screen.
    // They sit under the caption row; the reader matches on the label, so
    // their position is presentational only.
    const meta = [
      [SECTOR_ROW_LABEL, sector],
      [INDUSTRY_ROW_LABEL, industry],
      [],
    ];
    const rows = FINANCIAL_FACTORS.map(factor => [
      factor.label,
      formData[`${factor.key}_trailing12`] || '',
      formData[`${factor.key}_oneYearForward`] || '',
      formData[`${factor.key}_twoYearsForward`] || ''
    ]);

    const csvContent = [headers, ...meta, ...rows]
      .map(row => row.map(csvCell).join(','))
      .join('\n');
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
    input.accept = '.csv,text/csv';
    input.onchange = (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;

      if (/\.xlsx?$/i.test(file.name)) {
        setError('Excel workbooks are not supported. Save the sheet as CSV and load that.');
        return;
      }

      const reader = new FileReader();
      reader.onerror = () => setError(`Could not read "${file.name}".`);
      reader.onload = () => {
        try {
          applyImportedCsv(String(reader.result), file.name);
        } catch (err) {
          setError(err.message || 'Could not parse the file.');
        }
      };
      reader.readAsText(file);
    };
    input.click();
  };

  // Reads the same shape handleDownloadTemplate writes: one row per factor,
  // three period columns. Rows are matched on the label rather than position,
  // so reordered or partial files still load.
  const applyImportedCsv = (text, fileName) => {
    const rows = parseCsv(text);
    if (!rows.length) throw new Error(`"${fileName}" is empty.`);

    const byLabel = {};
    FINANCIAL_FACTORS.forEach(factor => {
      byLabel[normalizeLabel(factor.label)] = factor.key;
      byLabel[normalizeLabel(factor.key)] = factor.key;   // accept raw keys too
    });

    const updates = {};
    const loaded = [];
    const unknown = [];
    const badValues = [];
    const notes = [];
    let importedSector = null;
    let importedIndustry = null;

    rows.forEach((row, index) => {
      const label = normalizeLabel(row[0]);

      if (label === normalizeLabel(SECTOR_ROW_LABEL)) {
        importedSector = String(row[1] || '').trim();
        return;
      }
      if (label === normalizeLabel(INDUSTRY_ROW_LABEL)) {
        importedIndustry = String(row[1] || '').trim();
        return;
      }

      const key = byLabel[label];
      if (!key) {
        // The header row is expected; anything else unmatched is reported.
        if (index > 0 && label !== normalizeLabel('Financial Assessment Factor')) {
          if (String(row[0] || '').trim()) unknown.push(String(row[0]).trim());
        }
        return;
      }

      TIME_PERIODS.forEach((period, column) => {
        const raw = row[column + 1];
        if (raw === undefined || String(raw).trim() === '') return;
        const value = parseAmount(raw);
        if (value === null) {
          badValues.push(`${row[0]} / ${period.label.replace('\n', ' ')}: "${String(raw).trim()}"`);
          return;
        }
        updates[`${key}_${period.key}`] = value;
      });
      loaded.push(key);
    });

    if (!loaded.length) {
      throw new Error(
        `No recognised rows in "${fileName}". Download the template to see the expected format.`
      );
    }

    // Sector and industry come from the file; the dropdowns follow it rather
    // than the other way round. Unknown values are still applied — the engine
    // takes them as free text — but they are called out.
    if (importedSector) {
      const match = Object.keys(INDUSTRIES_BY_SECTOR)
        .find(name => normalizeLabel(name) === normalizeLabel(importedSector));
      setSector(match || importedSector);
      if (!match) notes.push(`Sector "${importedSector}" is not one of the known sectors.`);

      if (importedIndustry) {
        const list = INDUSTRIES_BY_SECTOR[match] || [];
        const industryMatch = list
          .find(name => normalizeLabel(name) === normalizeLabel(importedIndustry));
        setIndustry(industryMatch || importedIndustry);
        if (match && !industryMatch) {
          notes.push(`Industry "${importedIndustry}" is not listed under ${match}.`);
        }
      }
    } else if (importedIndustry) {
      setIndustry(importedIndustry);
    }

    setFormData(prev => ({ ...prev, ...updates }));
    setError(null);

    // Say what landed and what did not, rather than silently partially
    // loading — a quietly skipped row becomes a wrong rating.
    const missing = FINANCIAL_FACTORS
      .filter(factor => !loaded.includes(factor.key))
      .map(factor => factor.label);
    const parts = [`Loaded ${loaded.length} of ${FINANCIAL_FACTORS.length} rows from "${fileName}".`];
    if (importedSector || importedIndustry) {
      parts.push(`Sector/industry from file: ${importedSector || '—'} / ${importedIndustry || '—'}.`);
    } else {
      parts.push('No Sector or Industry rows in the file; the current selection is unchanged.');
    }
    notes.forEach(note => parts.push(note));
    if (missing.length) parts.push(`Not in the file (kept current values): ${missing.join(', ')}.`);
    if (unknown.length) parts.push(`Unrecognised rows ignored: ${unknown.join(', ')}.`);
    if (badValues.length) parts.push(`Skipped non-numeric cells: ${badValues.join('; ')}.`);
    setImportNotice(parts.join(' '));
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

        {/* CSV import summary */}
        {importNotice && (
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-800 flex items-start justify-between gap-4">
            <p className="text-sm">{importNotice}</p>
            <button
              onClick={() => setImportNotice(null)}
              className="text-blue-500 hover:text-blue-700 text-sm font-semibold"
            >
              Dismiss
            </button>
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