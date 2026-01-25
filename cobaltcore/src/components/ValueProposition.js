import React from 'react';
import { ArrowRight } from 'lucide-react';

export default function ValueProposition() {
  return (
    <section className="py-28 px-4 sm:px-6 lg:px-8 bg-white">
      <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
        <div>
          <h2 className="text-5xl font-bold text-gray-900 mb-8 leading-tight">
            Unlock Private Value with Private Credit Ratings!
          </h2>
          <p className="text-xl text-gray-600 mb-6 leading-relaxed">
            Private Credit is an alternative asset class that may offer higher yields and shorter duration investments that are largely uncorrelated to the stock market. That's why institutional investors are increasingly allocating to the $3.14 trillion sector.
          </p>
          <p className="text-xl text-gray-600 mb-8 leading-relaxed">
            Now, Compass Analytics provides tools for participants in these opportunities too.
          </p>
          <button className="text-gray-900 font-bold flex items-center hover:gap-4 transition-all gap-2">
            Learn more <ArrowRight className="w-5 h-5" />
          </button>
        </div>
        <div className="bg-gradient-to-br from-gray-100 to-gray-50 rounded-2xl p-12 aspect-square flex items-center justify-center">
          <div className="text-center">
            <div className="text-8xl font-bold text-gray-300 mb-4">$3.14T</div>
            <div className="text-xl text-gray-500">Market Size</div>
          </div>
        </div>
      </div>
    </section>
  );
}