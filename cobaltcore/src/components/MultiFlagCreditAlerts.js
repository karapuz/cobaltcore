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
    subtitle: 'aka "marketed EBITDA"',
    body: [
      'FMP EBITDA API conservative version: netIncome + depreciationAndAmortization + incomeTaxExpense + interestExpense, compared against the "market normalization" EBITDA adjusted (add-backs).',
      'If the discrepancy is 20% or greater between these two, we flag this metric for the investor who inputted that ticker or private credit data into our portal (or holds it within their portfolio).',
    ],
    note: 'Team owner to opine on add-backs that can potentially inflate EBITDA performance.',
  },
  {
    id: 2,
    icon: UserX,
    accent: 'bg-orange-50 text-orange-600',
    title: 'Founder-owned and operated business with a history of fraud allegations',
    subtitle: 'including recently filed accusations',
    body: [
      'As part of this investor protection service, install an AI/agent or news alert tracker on (A) the name of the C-suite executive(s), and (B) the rated entity / company.',
    ],
  },
  {
    id: 3,
    icon: Layers,
    accent: 'bg-amber-50 text-amber-600',
    title: 'Special Purpose Vehicles (SPVs) used to keep debt off balance sheet',
    subtitle: 'detection',
    body: [
      'As above, develop an AI/agent or EDGAR LLM alert/tracker on SEC filings that suggest SPVs and debt consolidations.',
    ],
  },
  {
    id: 4,
    icon: FileText,
    accent: 'bg-blue-50 text-blue-600',
    title: 'Capital and finance lease obligations added to total debt exposure',
    subtitle: 'ASC 842',
    body: [
      'To discuss as a team given ASC 842: is there business value in tracking and documenting when certain capital or finance lease obligations are material to future debt loads?',
      'There is, if you take the AI hyperscaler lease obligations as an example, which measure in the trillions. This is straightforward to pull from the FMP API. We would duplicate our IADOW model but add capital lease obligations to debt (long, short, net, total).',
    ],
    note: 'Team to discuss whether we should include "Unrecorded Contractual Purchase Commitments", given the rise of AI hyperscaler credits that some feel are future debt obligations.',
  },
  {
    id: 5,
    icon: Receipt,
    accent: 'bg-purple-50 text-purple-600',
    title: 'Accounts payable changes that may reflect erosion of core cash flow',
    subtitle: 'payment timing',
    body: [
      'For publicly traded companies, we can pull the FMP API and track if and when accounts payable (or receivable) abruptly extend.',
      'We do NOT need to conduct the actual analysis. Ideally this monitoring flag is for investors to ask their corporate credit analysts to examine payment timing, underlying operating performance, and the source of reported cash generation together.',
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
                This service line is the brainchild of the Case Study of First Brands authored by Prof. Michael Gatto.
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
                          <span className="font-semibold text-gray-700">To discuss: </span>
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