import React from 'react';

export default function CTA({ onSignUpClick }) {
  return (
    <section className="py-28 bg-black px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto text-center">
        <h2 className="text-5xl md:text-6xl font-bold text-white mb-8 leading-tight">
          Make your first investment and get up to $500.
        </h2>
        <p className="text-xl text-gray-300 mb-10 leading-relaxed">
          Get $500 in your account after you make your first investment.
        </p>
        <button 
          onClick={onSignUpClick}
          className="bg-white text-black px-10 py-4 rounded-md text-base font-bold hover:bg-gray-100 transition-all hover:shadow-xl uppercase tracking-wide"
        >
          View Available Deals
        </button>
      </div>
    </section>
  );
}