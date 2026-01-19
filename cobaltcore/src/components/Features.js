import React from 'react';
import { Clock, DollarSign, BarChart3, Eye, TrendingUp, Shield } from 'lucide-react';

export default function Features() {
  const features = [
    {
      icon: <Clock className="w-10 h-10" />,
      title: 'Investments matching your time horizon.',
      description: 'Private credit can be a short- or long-term strategy. Potentially earn 12%+ coupon with investments that can mature in as little as three months or as long as a few years.'
    },
    {
      icon: <DollarSign className="w-10 h-10" />,
      title: 'Knowledge is power.',
      description: 'Indicate your target credit rating, and research options to reach it. Knowing your target makes it possible to improve funding.'
    },
    {
      icon: <BarChart3 className="w-10 h-10" />,
      title: 'Diversification by design.',
      description: 'Gain understanding of your exposure due to credit ratings for individual deals.'
    },
    {
      icon: <Eye className="w-10 h-10" />,
      title: 'Understand market impact.',
      description: 'With our proprietary technology, research how credit rating can react to market conditions. Access comprehensive market and economics scenario database.'
    },
    // {
    //   icon: <TrendingUp className="w-10 h-10" />,
    //   title: 'A recurring income stream',
    //   description: 'Deals on our marketplace generally offer monthly income potential. These investments generate passive income throughout the lifetime of the deal.'
    // },
    // {
    //   icon: <Shield className="w-10 h-10" />,
    //   title: 'Expert support from professionals.',
    //   description: 'Our knowledgeable Investor Relations team is available to answer your questions – just call or email us.'
    // }
  ];

  return (
    <section className="py-28 bg-gray-50 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <p className="text-xs font-semibold text-gray-400 mb-6 tracking-wider uppercase">
            BUILT FOR MODERN ECONOMY  |
          </p>
          <h2 className="text-5xl font-bold text-gray-900 mb-8 leading-tight max-w-4xl mx-auto">
            Funding is hard. We make it easier.
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
            Compass innovative platform empowers investors to assess quality of investments, improving investing quality.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
          {features.map((feature, idx) => (
            <div key={idx} className="bg-white p-10 rounded-xl shadow-sm hover:shadow-md transition-shadow">
              <div className="text-gray-900 mb-6">{feature.icon}</div>
              <h3 className="text-xl font-bold text-gray-900 mb-4">{feature.title}</h3>
              <p className="text-gray-600 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}