import React from 'react';

export default function CTA() {
  return (
    <section className="py-28 bg-black px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-5xl md:text-6xl font-bold text-white mb-8 leading-tight">
          Sign up, and get up to $500 in Free Credit Rating Services.
        </h2>
        <p className="text-xl text-gray-300 mb-10 leading-relaxed">
          Get free access to public companies' valuation after you sign up.
        </p>
        <button className="bg-white text-black px-10 py-4 rounded-md text-base font-bold hover:bg-gray-100 transition-all hover:shadow-xl uppercase tracking-wide">
          View Available Credit Ratings
        </button>
      </div>
    </section>
  );
}