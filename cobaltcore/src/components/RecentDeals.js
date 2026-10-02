import React from 'react';

// Figures are trailing-twelve-month, taken from stockanalysis.com statistics
// pages (retrieved 2026-10-02) so all three companies are on one basis and
// one definition of total debt.
//
// FCF / Total Debt is computed from the two reported figures rather than
// copied, so it always agrees with what is displayed beside it.
//
// These are static marketing figures. They are NOT produced by the rating
// engine and will go stale. Wiring this panel to /v0/pillar/values/historical
// would keep it current and make the numbers match the product.
const COMPANIES = [
  {
    name: 'Apple Inc.',
    ticker: 'AAPL',
    compassRating: 'AAA',
    sector: 'Technology',
    revenue: 466.82e9,
    ebitdaMargin: 0.3598,
    freeCashFlow: 136.68e9,
    totalDebt: 84.34e9,
    gradient: 'bg-gradient-to-br from-slate-500 to-slate-700',
  },
  {
    name: 'Microsoft Corporation',
    ticker: 'MSFT',
    compassRating: 'AA+',
    sector: 'Technology',
    revenue: 331.84e9,
    ebitdaMargin: 0.5854,
    freeCashFlow: 66.99e9,
    totalDebt: 128.81e9,
    gradient: 'bg-gradient-to-br from-blue-500 to-blue-700',
  },
  {
    name: 'Johnson & Johnson',
    ticker: 'JNJ',
    compassRating: 'AA-',
    sector: 'Healthcare',
    revenue: 97.93e9,
    ebitdaMargin: 0.3561,
    freeCashFlow: 22.24e9,
    totalDebt: 49.04e9,
    gradient: 'bg-gradient-to-br from-red-400 to-red-600',
  },
];

function getRatingColor(rating) {
  if (!rating) return 'bg-gray-100 text-gray-800';
  if (rating.startsWith('AAA')) return 'bg-emerald-100 text-emerald-800';
  if (rating.startsWith('AA')) return 'bg-green-100 text-green-800';
  if (rating.startsWith('A')) return 'bg-lime-100 text-lime-800';
  if (rating.startsWith('BBB')) return 'bg-yellow-100 text-yellow-800';
  if (rating.startsWith('BB')) return 'bg-amber-100 text-amber-800';
  if (rating.startsWith('B')) return 'bg-orange-100 text-orange-800';
  if (rating.startsWith('CCC')) return 'bg-red-100 text-red-800';
  return 'bg-red-200 text-red-900';
}

function formatBillions(value) {
  return `$${(value / 1e9).toFixed(1)}B`;
}

function formatPercent(fraction) {
  return `${(fraction * 100).toFixed(1)}%`;
}

export default function RecentDeals() {
  return (
    <section className="py-28 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <p className="text-xs font-semibold text-gray-400 mb-6 tracking-wider uppercase">
            RECENT RATINGS  |
          </p>
          <h2 className="text-5xl font-bold text-gray-900">
            Recent Credit Ratings Actions
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {COMPANIES.map((company) => (
            <div
              key={company.ticker}
              className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-all group"
            >
              <div className={`h-32 ${company.gradient} flex items-center justify-center`}>
                <span className="font-mono font-bold text-white text-4xl tracking-wider">
                  {company.ticker}
                </span>
              </div>
              <div className="p-6">
                <div className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">
                  {company.sector}
                </div>

                <h3 className="font-bold text-gray-900 mb-6 text-lg">{company.name}</h3>

                <div className="space-y-3 mb-6">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Compass Rating</span>
                    <span className={`inline-block px-3 py-1 rounded text-sm font-bold ${getRatingColor(company.compassRating)}`}>
                      {company.compassRating}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Revenue</span>
                    <span className="font-bold text-gray-900 text-lg">
                      {formatBillions(company.revenue)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">EBITDA Margin</span>
                    <span className="font-bold text-gray-900">
                      {formatPercent(company.ebitdaMargin)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">FCF / Total Debt</span>
                    <span className="font-bold text-gray-900">
                      {formatPercent(company.freeCashFlow / company.totalDebt)}
                    </span>
                  </div>
                </div>

                <button className="w-full text-gray-900 border-2 border-gray-900 py-3 rounded-lg hover:bg-gray-900 hover:text-white transition-all font-semibold text-sm uppercase tracking-wide">
                  Report
                </button>
              </div>
            </div>
          ))}
        </div>

        <p className="text-center text-xs text-gray-400 mt-10">
          Trailing twelve months. Source: company filings via stockanalysis.com, retrieved October 2026.
        </p>
      </div>
    </section>
  );
}