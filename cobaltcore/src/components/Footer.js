import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-16">
          <div>
            <h3 className="font-bold mb-6 text-white">Invest</h3>
            <ul className="space-y-3 text-gray-400 text-sm">
              <li><button className="hover:text-white transition text-left">Getting Started</button></li>
              <li><button className="hover:text-white transition text-left">Asset Classes</button></li>
              <li><button className="hover:text-white transition text-left">Performance</button></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold mb-6 text-white">About</h3>
            <ul className="space-y-3 text-gray-400 text-sm">
              <li><button className="hover:text-white transition text-left">About Us</button></li>
              <li><button className="hover:text-white transition text-left">Careers</button></li>
              <li><button className="hover:text-white transition text-left">Contact</button></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold mb-6 text-white">Resources</h3>
            <ul className="space-y-3 text-gray-400 text-sm">
              <li><button className="hover:text-white transition text-left">Blog</button></li>
              <li><button className="hover:text-white transition text-left">FAQ</button></li>
              <li><button className="hover:text-white transition text-left">Glossary</button></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold mb-6 text-white">Legal</h3>
            <ul className="space-y-3 text-gray-400 text-sm">
              <li><button className="hover:text-white transition text-left">Terms of Use</button></li>
              <li><button className="hover:text-white transition text-left">Privacy Policy</button></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-800 pt-10">
          <p className="text-gray-400 text-sm">
            © 2026 Compass Analytics. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}