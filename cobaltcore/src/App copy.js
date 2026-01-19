import React, { useState } from 'react';
import { Menu, X, ChevronDown, ArrowRight, TrendingUp, Shield, DollarSign, Clock, BarChart3, Eye } from 'lucide-react';

export default function LandingPage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const stats = [
    { label: 'Total Funded', value: '$2B+' },
    { label: 'Active Investors', value: '10,000+' },
    { label: 'Average Return', value: '14.5%' }
  ];

  const features = [
    {
      icon: <Clock className="w-10 h-10" />,
      title: 'Investments matching your time horizon.',
      description: 'Private credit can be a short- or long-term strategy. Potentially earn 12%+ coupon with investments that can mature in as little as three months or as long as a few years.'
    },
    {
      icon: <DollarSign className="w-10 h-10" />,
      title: 'Invest on your terms.',
      description: 'Specify your desired yield and minimum investment amount during syndication. Only invest if your parameters are met. For direct investing, fees apply only to interest earned.'
    },
    {
      icon: <BarChart3 className="w-10 h-10" />,
      title: 'Diversification by design.',
      description: 'Gain exposure to different asset classes and geographies with individual deals, or use Blended Notes to quickly achieve broad diversification.'
    },
    {
      icon: <Eye className="w-10 h-10" />,
      title: 'Transparency at every turn.',
      description: 'With our proprietary technology, see and compare available deals upfront. Access comprehensive borrower, deal, and market data.'
    },
    {
      icon: <TrendingUp className="w-10 h-10" />,
      title: 'A recurring income stream',
      description: 'Deals on our marketplace generally offer monthly income potential. These investments generate passive income throughout the lifetime of the deal.'
    },
    {
      icon: <Shield className="w-10 h-10" />,
      title: 'Expert support from professionals.',
      description: 'Our knowledgeable Investor Relations team is available to answer your questions – just call or email us.'
    }
  ];

  const deals = [
    { type: 'US SMB Financing', category: 'Asset Based', coupon: '14.50%', amount: '$7.61M', term: '12 months', img: 'bg-gradient-to-br from-blue-400 to-blue-600' },
    { type: 'US Consumer Loans', category: 'Asset Based', coupon: '14.00%', amount: '$2.31M', term: '14 months', img: 'bg-gradient-to-br from-purple-400 to-purple-600' },
    { type: 'Supply Chain Finance', category: 'Asset Based', coupon: '16.00%', amount: '$4.00M', term: '9 months', img: 'bg-gradient-to-br from-green-400 to-green-600' },
    { type: 'Litigation Funding', category: 'Asset Based', coupon: '17.00%', amount: '$7.27M', term: '24 months', img: 'bg-gradient-to-br from-orange-400 to-orange-600' }
  ];

  const testimonials = [
    {
      quote: "When we opened our account, we didn't know how much we would be investing on the platform. We have been very pleased with the opportunities and returns offered and have increased our investments significantly this year.",
      author: "Tom L.",
      role: "Investor since 2021"
    },
    {
      quote: "This platform fits my investing strategy perfectly. Not only can I diversify my portfolio with a shorter duration alternative investment like private credit, I can further diversify across multiple asset classes.",
      author: "Drew M.",
      role: "Investor since 2019"
    },
    {
      quote: "They are one of the only platforms I've dealt with that have real people on the other end of their customer service line. Talking to a human being regarding my portfolio and investments is instrumental in this digital world we live in.",
      author: "Daniel C.",
      role: "Investment Professional"
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b border-gray-100 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center">
              <div className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">PERCENT</div>
            </div>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-10">
              <div className="relative group">
                <button className="text-gray-700 hover:text-gray-900 font-medium flex items-center gap-1">
                  For Investors <ChevronDown className="w-4 h-4" />
                </button>
              </div>
              <div className="relative group">
                <button className="text-gray-700 hover:text-gray-900 font-medium flex items-center gap-1">
                  For Borrowers <ChevronDown className="w-4 h-4" />
                </button>
              </div>
              <div className="relative group">
                <button className="text-gray-700 hover:text-gray-900 font-medium flex items-center gap-1">
                  Company <ChevronDown className="w-4 h-4" />
                </button>
              </div>
              <div className="relative group">
                <button className="text-gray-700 hover:text-gray-900 font-medium flex items-center gap-1">
                  Resources <ChevronDown className="w-4 h-4" />
                </button>
              </div>
            </nav>

            <div className="hidden md:flex items-center space-x-4">
              <button className="text-gray-700 hover:text-gray-900 font-medium px-4 py-2">sign in</button>
              <button className="bg-black text-white px-6 py-3 rounded-md hover:bg-gray-800 font-medium transition-all hover:shadow-lg">
                Sign up
              </button>
            </div>

            {/* Mobile menu button */}
            <button 
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-100 bg-white">
            <div className="px-4 py-6 space-y-4">
              <a href="#" className="block text-gray-700 font-medium py-2">For Investors</a>
              <a href="#" className="block text-gray-700 font-medium py-2">For Borrowers</a>
              <a href="#" className="block text-gray-700 font-medium py-2">Company</a>
              <a href="#" className="block text-gray-700 font-medium py-2">Resources</a>
              <button className="w-full bg-black text-white px-6 py-3 rounded-md font-medium mt-4">
                Sign up
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Hero Section */}
      <section className="pt-36 pb-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-5xl mx-auto">
            <h1 className="text-6xl md:text-8xl font-bold text-gray-900 mb-8 leading-tight">
              Private credit. <span className="italic">Simplified.</span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-10 leading-relaxed max-w-4xl mx-auto">
              Join thousands of investors who have funded over $2 billion in deals on Percent. Start your journey in private credit investing today.
            </p>
            
            <div className="text-left max-w-2xl mx-auto mb-12 space-y-3">
              <div className="flex items-start text-gray-700 text-lg">
                <span className="mr-3">•</span>
                <span>Potential for up to 20% annualized returns.</span>
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
                New Investor Bonus: Earn up to $500 after making your first investment*
              </p>
            </div>

            <button className="bg-black text-white px-10 py-4 rounded-md text-base font-bold hover:bg-gray-800 transition-all hover:shadow-xl uppercase tracking-wide">
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

      {/* Featured In */}
      <section className="py-16 bg-white border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs font-semibold text-gray-400 mb-10 tracking-wider uppercase">Featured In  |</p>
          <div className="flex flex-wrap justify-center items-center gap-16 opacity-30">
            <div className="text-2xl font-bold tracking-tight">FINTECH MAG</div>
            <div className="text-2xl font-bold tracking-tight">NASDAQ</div>
            <div className="text-2xl font-bold tracking-tight">BLOOMBERG</div>
            <div className="text-2xl font-bold tracking-tight">TECHCRUNCH</div>
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="py-28 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto grid md:grid-cols-2 gap-16 items-center">
          <div>
            <h2 className="text-5xl font-bold text-gray-900 mb-8 leading-tight">
              Unlock value with private credit
            </h2>
            <p className="text-xl text-gray-600 mb-6 leading-relaxed">
              Private credit is an alternative asset class that may offer higher yields and shorter duration investments that are largely uncorrelated to the stock market. That's why institutional investors are increasingly allocating to the $3.14 trillion sector.
            </p>
            <p className="text-xl text-gray-600 mb-8 leading-relaxed">
              Now, Percent gives accredited investors these opportunities too.
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

      {/* Features Grid */}
      <section className="py-28 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <p className="text-xs font-semibold text-gray-400 mb-6 tracking-wider uppercase">BUILT FOR MODERN INVESTORS  |</p>
            <h2 className="text-5xl font-bold text-gray-900 mb-8 leading-tight max-w-4xl mx-auto">
              Finding the right opportunity is hard. We make it easier.
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Percent's innovative marketplace connects investors with corporate borrowers, simplifying investment and portfolio management.
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

      {/* Recent Deals */}
      <section className="py-28 px-4 sm:px-6 lg:px-8 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <p className="text-xs font-semibold text-gray-400 mb-6 tracking-wider uppercase">RECENT DEALS  |</p>
            <h2 className="text-5xl font-bold text-gray-900">
              Investment opportunities
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {deals.map((deal, idx) => (
              <div key={idx} className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-all group">
                <div className={`h-32 ${deal.img}`}></div>
                <div className="p-6">
                  <div className="text-xs font-semibold text-gray-400 mb-3 uppercase tracking-wider">{deal.category}</div>
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

      {/* Testimonials */}
      <section className="py-28 bg-gray-50 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-20">
            <p className="text-xs font-semibold text-gray-400 mb-6 tracking-wider uppercase">WHAT OUR INVESTORS ARE SAYING  |</p>
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

      {/* CTA Section */}
      <section className="py-28 bg-black px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-8 leading-tight">
            Make your first investment and get up to $500.
          </h2>
          <p className="text-xl text-gray-300 mb-10 leading-relaxed">
            Get $500 in your account after you make your first investment.
          </p>
          <button className="bg-white text-black px-10 py-4 rounded-md text-base font-bold hover:bg-gray-100 transition-all hover:shadow-xl uppercase tracking-wide">
            View Available Deals
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
            <div>
              <h3 className="font-bold mb-6 text-white">Invest</h3>
              <ul className="space-y-3 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition">Getting Started</a></li>
                <li><a href="#" className="hover:text-white transition">Asset Classes</a></li>
                <li><a href="#" className="hover:text-white transition">Performance</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold mb-6 text-white">About</h3>
              <ul className="space-y-3 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition">About Us</a></li>
                <li><a href="#" className="hover:text-white transition">Careers</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold mb-6 text-white">Resources</h3>
              <ul className="space-y-3 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">FAQ</a></li>
                <li><a href="#" className="hover:text-white transition">Glossary</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold mb-6 text-white">Legal</h3>
              <ul className="space-y-3 text-gray-400 text-sm">
                <li><a href="#" className="hover:text-white transition">Terms of Use</a></li>
                <li><a href="#" className="hover:text-white transition">Privacy Policy</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-10">
            <p className="text-gray-400 text-sm">
              © 2026 Investment Platform. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}