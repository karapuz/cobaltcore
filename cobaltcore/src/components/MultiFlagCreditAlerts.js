import React from 'react';
import {
  ArrowLeft, Flag, ShieldAlert, UserX, Layers, FileText,
  Receipt, Upload, Info
} from 'lucide-react';

const FLAGS = [
  {
    id: 1,
    icon: ShieldAlert,
    accent: 'bg-red-50 text-red-600',
    title: 'EBITDA core vs EBITDA adjusted discrepancies',
    subtitle: '',
    body: [
      'EBITDA: netIncome + depreciationAndAmortization + incomeTaxExpense + interestExpense, compared against the "market normalization" EBITDA adjusted (add-backs).',
      'If EBITDA discrepancy is 20% or greater, we flag this metric for the investor who inputted that ticker or private credit data into our portal.',
    ],
    note: 'Team owner to opine on add-backs that can potentially inflate EBITDA performance.',
  },
  {
    id: 2,
    icon: UserX,
    accent: 'bg-orange-50 text-orange-600',
    title: 'Founder-owned and operated business with a history of fraud allegations',
    subtitle: '',
    body: [
      'As part of this investor protection service, Compass AI-agent and news alert tracks the names of the C-suite executive(s), and the rated entity / company. In the instance of a match alleging fraud allegations, Compass flags this as part of its MFCA system and alerts the investor(s) who review the alert as material or not applicable.',
    ],
  },
  {
    id: 3,
    icon: Layers,
    accent: 'bg-amber-50 text-amber-600',
    title: 'Special Purpose Vehicles (SPVs) used to keep debt off balance sheet',
    subtitle: 'detection',
    body: [
      'As above, Compass AI-agent reviews EDGAR/SEC filings (or audited financials) and sends an alert to the subscriber when filings suggest the appearance of SPVs being used to keep debt off balance sheets.',
    ],
  },
  {
    id: 4,
    icon: FileText,
    accent: 'bg-blue-50 text-blue-600',
    title: 'Capital and finance lease obligations added to total debt exposure',
    subtitle: 'ASC 842',
    body: [
      'ASC 842: Compass tracks and documents when certain capital or financial obligations are material to future debt loads',
      'AI hyperscaler future compute commitments measure in the trillions.',
    ],
    note: 'AI hyperscaler include "Unrecorded Contractual Purchase Commitments", which leads to future debt obligations. Compass believes there are corporates that hold off-balance sheet leverage that has not been realized due to ASC 842, and tracks these commitments when they reach thresholds of greater than $100B',
  },
  {
    id: 5,
    icon: Receipt,
    accent: 'bg-purple-50 text-purple-600',
    title: 'Accounts payable changes that may reflect erosion of core cash flow',
    subtitle: 'payment timing',
    body: [
      'For publicly traded companies, Compass tracks when accounts payable (or receivable) abruptly extend.',
    ],
  },
];

export default function MultiFlagCreditAlerts({ user, onBack }) {
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
                <Flag className="w-5 h-5 text-red-600" />
                <h1 className="text-lg font-bold text-gray-900">Multi-Flag Credit Alerts (MFCA)</h1>
              </div>
            </div>
            {user && (
              <span className="text-sm text-gray-500">
                Welcome, <span className="font-semibold text-gray-800">{user.name}</span>
              </span>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero */}
        <div className="bg-gradient-to-br from-gray-900 to-gray-700 rounded-2xl p-8 md:p-12 text-white mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-4 rounded-full bg-white/10 text-xs font-semibold tracking-wide uppercase">
            Investor protection service line
          </div>
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Multi-Flag Credit Alerts</h2>
          <p className="text-lg text-gray-100 leading-relaxed">
            Investors who hold a credit rating from another credit firm can insert any ticker or private company
            data into a "Flag" surveillance service line that tracks five warning flags.
          </p>
        </div>

        {/* How data gets in */}
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center flex-shrink-0">
              <Upload className="w-6 h-6 text-gray-700" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-3">How data enters the service</h3>
              <p className="text-gray-700 leading-relaxed">
                Any ticker or private company data can be submitted by quarterly upload or hard key-in through the
                portal. Submitted names are then monitored against the five flags below.
              </p>
              <p className="text-sm text-gray-500 mt-4">
                This service line is based on the Case Study of First Brands which was, in Compass' opinion, detectable had investors enrolled with our Multi-Flag Credit Alert monitoring service.
              </p>
            </div>
          </div>
        </section>

        {/* Flags */}
        <h3 className="text-sm font-bold uppercase tracking-wider text-gray-500 mb-4 px-1">
          Surveillance flags
        </h3>

        <div className="space-y-6">
          {FLAGS.map((flag) => {
            const Icon = flag.icon;
            return (
              <section
                key={flag.id}
                className="bg-white rounded-xl border border-gray-200 shadow-sm p-8"
              >
                <div className="flex items-start gap-4">
                  <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${flag.accent}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline gap-2 flex-wrap mb-1">
                      <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
                        Flag {flag.id}
                      </span>
                      {flag.subtitle && (
                        <span className="text-xs text-gray-400 italic">{flag.subtitle}</span>
                      )}
                    </div>
                    <h4 className="text-xl font-bold text-gray-900 mb-3">{flag.title}</h4>
                    <div className="space-y-3 text-gray-700 leading-relaxed">
                      {flag.body.map((para, i) => (
                        <p key={i}>{para}</p>
                      ))}
                    </div>
                    {flag.note && (
                      <div className="mt-4 flex items-start gap-2 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                        <Info className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-gray-600">
                          <span className="font-semibold text-gray-700"> </span>
                          {flag.note}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );
}