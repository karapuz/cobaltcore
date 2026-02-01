import React from 'react';

export default function Hero({ onSignUpClick }) {
  const stats = [
    { label: 'Total Market Size', value: '$54B+' },
    { label: 'Active Investors', value: '100,000+' },
    { label: 'Average Return', value: '14.5%' }
  ];

  return (
    <section className="pt-36 pb-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center max-w-5xl mx-auto">
          <h1 className="text-6xl md:text-8xl font-bold text-gray-900 mb-8 leading-tight">
            Private credit. <span className="italic">Simplified.</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-10 leading-relaxed max-w-4xl mx-auto">
            Join thousands of investors who have improve their chances to fund by using Compass. Start your journey in private credit investing today.
          </p>
          
          <div className="text-left max-w-2xl mx-auto mb-12 space-y-3">
            <div className="flex items-start text-gray-700 text-lg">
              <span className="mr-3">•</span>
              <span>Improving quality of your funding.</span>
            </div>
            <div className="flex items-start text-gray-700 text-lg">
              <span className="mr-3">•</span>
              <span>Diversification through an asset that can be less tied to public market fluctuations.</span>
            </div>
            <div className="flex items-start text-gray-700 text-lg">
              <span className="mr-3">•</span>
              <span>Timelines that fit your investment horizons with deals maturing from 6-36 months.</span>
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-5 mb-10 max-w-2xl mx-auto">
            <p className="text-blue-900 font-semibold text-base">
              New Investor Bonus: Recieve up to $500 in credits when start using Compass Platform*
            </p>
          </div>

          <button 
            onClick={onSignUpClick}
            className="bg-black text-white px-10 py-4 rounded-md text-base font-bold hover:bg-gray-800 transition-all hover:shadow-xl uppercase tracking-wide"
          >
            SIGN UP FOR FREE
          </button>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 mt-20 pt-12 border-t border-gray-200">
            {stats.map((stat, idx) => (
              <div key={idx} className="text-center">
                <div className="text-5xl font-bold text-gray-900 mb-3">{stat.value}</div>
                <div className="text-gray-600 text-lg">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}