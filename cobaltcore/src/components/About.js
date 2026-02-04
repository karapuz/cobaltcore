import React from 'react';
import { ArrowLeft, TrendingUp, Users, Target, DollarSign, Award, AlertCircle } from 'lucide-react';

export default function About({ user, onBack }) {
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
              <h1 className="text-lg font-bold text-gray-900">About Compass</h1>
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

      {/* Main content */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Hero Section */}
        <div className="bg-gradient-to-br from-gray-900 to-gray-700 rounded-2xl p-8 md:p-12 text-white mb-8">
          <h2 className="text-3xl md:text-4xl font-bold mb-4">Compass Credit Ratings</h2>
          <p className="text-lg text-gray-100 leading-relaxed">
            The next generation credit rating business providing quant/AI-model based credit ratings in under 90 seconds, 
            resulting in dramatic reductions in both overhead costs and time compared to competitors.
          </p>
        </div>

        {/* Problem */}
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-red-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-3">Problem</h3>
              <div className="space-y-3 text-gray-700 leading-relaxed">
                <p>
                  Credit Rating Agencies, aka Nationally Recognized Statistical Rating Organizations (NRSROs), typically 
                  require weeks to issue a credit rating due to their reliance on hard keyed-in excel sheets and bloated 
                  back office operations.
                </p>
                <p>
                  NRSROs are slow and expensive, passing inefficiencies and overhead costs onto investors/issuers seeking 
                  a credit rating for regulatory capital relief or to meet mandate requirements and make deals eligible for 
                  insurance and pension capital.
                </p>
                <p>
                  NRSROs also have ignored the demand in a niche but growing US Middle Market (MMC) sector due to low 
                  profit margins.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Solution */}
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <Target className="w-6 h-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-3">Solution</h3>
              <p className="text-gray-700 leading-relaxed">
                Compass CR has developed a scalable platform that issues credit rating reports efficiently, utilizing a 
                quant/AI-driven model requiring minimal manual analytical oversight.
              </p>
            </div>
          </div>
        </section>

        {/* Market Size */}
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-3">Market Size</h3>
              <p className="text-gray-700 leading-relaxed">
                <strong>US Fixed Income market:</strong> $58T, growing 5.6% (10Y CAGR)
              </p>
            </div>
          </div>
        </section>

        {/* Competitive Advantage */}
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-purple-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <Award className="w-6 h-6 text-purple-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-3">Competitive Advantage</h3>
              <ul className="space-y-2 text-gray-700 leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Compass CR is a modern fintech that has built an efficient scalable credit rating platform that allows us to attain profit from underserved sectors</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Compass CR is a "De Novo" alternative, with a clean slate reputation, unburdened by legacy regulatory and technology issues</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-purple-600 mt-1">•</span>
                  <span>Compass CR is founded by SEC professionals with regulatory expertise and technologists with proven track records</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Products */}
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 mb-6">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-yellow-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <DollarSign className="w-6 h-6 text-yellow-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900 mb-3">Products</h3>
              <ul className="space-y-2 text-gray-700 leading-relaxed">
                <li className="flex items-start gap-2">
                  <span className="text-yellow-600 mt-1">•</span>
                  <span><strong>Subscription Services:</strong> $1K annual per Qualified Institutional Buyer (QIB)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-600 mt-1">•</span>
                  <span><strong>Private Placement Credit Analysis Services:</strong> $20K-30K per report</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-yellow-600 mt-1">•</span>
                  <span><strong>Flywheel business revenue model</strong> that generates sales leads from both its subscription and private placement (PP) fee-for-service services</span>
                </li>
              </ul>
            </div>
          </div>
        </section>

        {/* Founders & Key Team Members */}
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 mb-6">
          <div className="flex items-start gap-4 mb-6">
            <div className="w-12 h-12 bg-indigo-50 rounded-xl flex items-center justify-center flex-shrink-0">
              <Users className="w-6 h-6 text-indigo-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-xl font-bold text-gray-900">Founders & Key Team Members</h3>
            </div>
          </div>

          <div className="space-y-6">
            {/* Andrew Smith */}
            <div className="border-l-4 border-indigo-600 pl-6 py-2">
              <h4 className="text-lg font-bold text-gray-900 mb-1">Andrew Smith, CEO/Founder</h4>
              <p className="text-gray-700 leading-relaxed">
                15+ years experience in financial compliance and operations, Andrew helped build out SEC's Office of Credit 
                Ratings (OCR), as an Office of the US President, Presidential Management Fellow. After 9 years at the OCR, 
                Andrew led the US Compliance Program at Morningstar DBRS, the 4th largest NRSRO globally. Andrew was 
                board-appointed as Morningstar DBRS' top compliance manager (Designated Compliance Officer), before 
                establishing Compass CR. Previous to Morningstar DBRS, Andrew worked at CalPERS' Private Equity Program and 
                earned an MBA from Trinity College Dublin.
              </p>
            </div>

            {/* Ilya Presman */}
            <div className="border-l-4 border-indigo-600 pl-6 py-2">
              <h4 className="text-lg font-bold text-gray-900 mb-1">Ilya Presman, CTO/co-Founder</h4>
              <p className="text-gray-700 leading-relaxed">
                Ilya has more than 30+ years working in the finance sector (e.g., Bloomberg, Goldman Sachs, JPMorgan, Tudor 
                Investment), and fintech startups (Addepar, Carta). Ilya has extensive expertise in scalable architecture, 
                software design and financial modelling with graduate degrees in Computational Finance (CMU) and Information 
                Systems (NYU).
              </p>
            </div>

            {/* Chief Compliance Officer */}
            <div className="border-l-4 border-green-600 pl-6 py-2">
              <h4 className="text-lg font-bold text-gray-900 mb-1">Chief Compliance Officer (HIRED)</h4>
              <p className="text-gray-700 leading-relaxed">
                Compass CR has a soft commitment for this regulatory-required senior position. The candidate holds a MBA, CFA, 
                CPA and previously worked as a Managing Director at Rabobank and various roles at Merrill Lynch and Bear Stearns. 
                The candidate was the former CLO in-house expert at OCR for 10+ years.
              </p>
            </div>

            {/* MD, Analytical Head */}
            <div className="border-l-4 border-gray-300 pl-6 py-2">
              <h4 className="text-lg font-bold text-gray-900 mb-1">MD, Analytical Head/co-Founder (VACANT)</h4>
              <p className="text-gray-700 leading-relaxed">
                Compass CR is currently seeking an experienced analytical MD.
              </p>
            </div>
          </div>
        </section>

        {/* Advisors */}
        <section className="bg-white rounded-xl border border-gray-200 shadow-sm p-8">
          <h3 className="text-xl font-bold text-gray-900 mb-4">Advisors</h3>
          <div className="border-l-4 border-blue-600 pl-6 py-2">
            <h4 className="text-lg font-bold text-gray-900 mb-1">John Novak, PhD</h4>
            <p className="text-gray-700 leading-relaxed">
              Machine Learning/Deep Learning Expert, SEC Quant, Ronin Quantum Physicist and engineer, Y-combinator alum and 
              co-Founder for <a href="https://www.standard.ai" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">www.standard.AI</a> 
              {' '}(John led his AI startup from inception to Series B).
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}