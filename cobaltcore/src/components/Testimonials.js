import React from 'react';

export default function Testimonials() {
  const testimonials = [
    {
      quote: "When we opened our account, we didn't know how easy it was to investigate credit formation the platform. We have been very pleased with the tools offered and have increased our investments significantly this year.",
      author: "Tom L.",
      role: "Client since 2026"
    },
    {
      quote: "This platform fits my investing strategy. Not only can I can check credit, but can analyze my portfolio, allowing me to further diversify across multiple asset classes.",
      author: "Drew M.",
      role: "Investor since 2026"
    },
    {
      quote: "They are one of the only platforms I've dealt with that have real people on the other end of their customer service line. Talking to a human being regarding my portfolio and investments is instrumental in this digital world we live in.",
      author: "Daniel C.",
      role: "Investment Professional"
    }
  ];

  return (
    <section className="py-28 bg-gray-50 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-20">
          <p className="text-xs font-semibold text-gray-400 mb-6 tracking-wider uppercase">
            WHAT OUR CLIENTS ARE SAYING  |
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, idx) => (
            <div key={idx} className="bg-white p-10 rounded-xl shadow-sm">
              <div className="text-6xl text-gray-200 mb-6 font-serif">"</div>
              <p className="text-gray-700 mb-8 leading-relaxed italic">{testimonial.quote}</p>
              <div className="border-t border-gray-100 pt-6">
                <div className="font-bold text-gray-900">{testimonial.author}</div>
                <div className="text-sm text-gray-500 mt-1">{testimonial.role}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}