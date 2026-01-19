import React from 'react';

export default function RecentDeals() {
  const deals = [
    { rating: "BBB+", type: 'US SMB Financing', category: 'Asset Based', coupon: '14.50%', amount: '$7.61M', term: '12 months', img: 'bg-gradient-to-br from-blue-400 to-blue-600' },
    { rating: "BBB+", type: 'US Consumer Loans', category: 'Asset Based', coupon: '14.00%', amount: '$2.31M', term: '14 months', img: 'bg-gradient-to-br from-purple-400 to-purple-600' },
    { rating: "BBB+", type: 'Supply Chain Finance', category: 'Asset Based', coupon: '16.00%', amount: '$4.00M', term: '9 months', img: 'bg-gradient-to-br from-green-400 to-green-600' },
    { rating: "BBB+", type: 'Litigation Funding', category: 'Asset Based', coupon: '17.00%', amount: '$7.27M', term: '24 months', img: 'bg-gradient-to-br from-orange-400 to-orange-600' }
  ];

  return (
    <section className="py-28 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <p className="text-xs font-semibold text-gray-400 mb-6 tracking-wider uppercase">
            RECENT RATINGS  |
          </p>
          <h2 className="text-5xl font-bold text-gray-900">
            Investment opportunities
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {deals.map((deal, idx) => (
            <div key={idx} className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-all group">
              <div className={`h-32 ${deal.img}`}></div>
              <div className="p-6">
                <div className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">
                  {deal.category}
                </div>

                <h3 className="font-bold text-green-900 mb-6 text-lg">{deal.rating}</h3>
                <h3 className="font-bold text-gray-900 mb-6 text-lg">{deal.type}</h3>

                <div className="space-y-3 mb-6">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Coupon</span>
                    <span className="font-bold text-gray-900 text-lg">{deal.coupon}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Amount</span>
                    <span className="font-bold text-gray-900">{deal.amount}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-500 text-sm">Term</span>
                    <span className="font-bold text-gray-900">{deal.term}</span>
                  </div>
                </div>
                <button className="w-full text-gray-900 border-2 border-gray-900 py-3 rounded-lg hover:bg-gray-900 hover:text-white transition-all font-semibold text-sm uppercase tracking-wide">
                  view deals
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}