import React, { useState } from 'react';
import { Menu, X, ChevronDown } from 'lucide-react';
import LoginModal from './LoginModal';

export default function Header() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  return (
    <>
      <header className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b border-gray-100 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center">
              <div className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
                Compass Analytics
              </div>
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
              <button 
                onClick={() => setLoginModalOpen(true)}
                className="text-gray-700 hover:text-gray-900 font-medium px-4 py-2"
              >
                sign in
              </button>
              <button 
                onClick={() => setLoginModalOpen(true)}
                className="bg-black text-white px-6 py-3 rounded-md hover:bg-gray-800 font-medium transition-all hover:shadow-lg"
              >
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
              <button 
                onClick={() => {
                  setLoginModalOpen(true);
                  setMobileMenuOpen(false);
                }}
                className="w-full bg-black text-white px-6 py-3 rounded-md font-medium mt-4"
              >
                Sign up
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Login Modal */}
      <LoginModal isOpen={loginModalOpen} onClose={() => setLoginModalOpen(false)} />
    </>
  );
}