import React from 'react';

export default function FeaturedIn() {
  return (
    <section className="py-16 bg-white border-y border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center text-xs font-semibold text-gray-400 mb-10 tracking-wider uppercase">
          Featured In  |
        </p>
        <div className="flex flex-wrap justify-center items-center gap-16 opacity-30">
          <div className="text-2xl font-bold tracking-tight">FINTECH MAG</div>
          <div className="text-2xl font-bold tracking-tight">NASDAQ</div>
          <div className="text-2xl font-bold tracking-tight">BLOOMBERG</div>
          <div className="text-2xl font-bold tracking-tight">TECHCRUNCH</div>
        </div>
      </div>
    </section>
  );
}