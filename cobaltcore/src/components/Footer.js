import React from 'react';

export default function Footer() {
  return (
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
            © 2026 Compass Analytics. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}