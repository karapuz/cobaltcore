import React, { useState } from 'react';
import { Menu, X, ChevronDown, User, LogOut, BarChart3, Activity } from 'lucide-react';

export default function Header({ onSignUpClick, user, onLogout, onNavigate }) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [servicesMenuOpen, setServicesMenuOpen] = useState(false);

  return (
    <header className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b border-gray-100 z-50 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <div className="flex items-center">
            <button onClick={() => onNavigate('home')} className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
              COMPASS
            </button>
          </div>
          
          {/* Desktop Navigation */}
          <nav className="hidden md:flex space-x-10 items-center">
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

            {/* Services Menu - only visible when logged in */}
            {user && (
              <div className="relative">
                <button
                  onClick={() => setServicesMenuOpen(!servicesMenuOpen)}
                  className="text-gray-900 font-semibold flex items-center gap-1 bg-gray-100 px-4 py-2 rounded-lg hover:bg-gray-200 transition"
                >
                  Services <ChevronDown className={`w-4 h-4 transition-transform ${servicesMenuOpen ? 'rotate-180' : ''}`} />
                </button>

                {servicesMenuOpen && (
                  <>
                    {/* Backdrop */}
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setServicesMenuOpen(false)}
                    ></div>

                    {/* Dropdown */}
                    <div className="absolute top-full left-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-100 py-2 z-20">
                      <button
                        onClick={() => {
                          onNavigate('portfolio');
                          setServicesMenuOpen(false);
                        }}
                        className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition flex items-center gap-3"
                      >
                        <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
                          <BarChart3 className="w-4 h-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Portfolio</p>
                          <p className="text-xs text-gray-500">Credit Ratings</p>
                        </div>
                      </button>
                      <button
                        onClick={() => {
                          onNavigate('scenarios');
                          setServicesMenuOpen(false);
                        }}
                        className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-gray-50 transition flex items-center gap-3"
                      >
                        <div className="w-8 h-8 bg-purple-50 rounded-lg flex items-center justify-center">
                          <Activity className="w-4 h-4 text-purple-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">Scenarios</p>
                          <p className="text-xs text-gray-500">Run Simulations</p>
                        </div>
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}
          </nav>

          {/* Desktop Auth Section */}
          <div className="hidden md:flex items-center space-x-4">
            {user ? (
              <div className="relative">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="flex items-center gap-2 px-4 py-2 hover:bg-gray-100 rounded-lg transition"
                >
                  <div className="w-8 h-8 bg-gray-900 rounded-full flex items-center justify-center">
                    <User className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-medium text-gray-900">{user.name}</span>
                  <ChevronDown className="w-4 h-4 text-gray-600" />
                </button>
                
                {/* User Dropdown Menu */}
                {userMenuOpen && (
                  <>
                    <div 
                      className="fixed inset-0 z-10"
                      onClick={() => setUserMenuOpen(false)}
                    ></div>
                    
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-100 py-2 z-20">
                      <div className="px-4 py-3 border-b border-gray-100">
                        <p className="text-sm font-semibold text-gray-900">{user.name}</p>
                        <p className="text-xs text-gray-500 mt-1">{user.email}</p>
                      </div>
                      
                      <div className="py-1">
                        <button
                          onClick={() => {
                            setUserMenuOpen(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition flex items-center gap-2"
                        >
                          <User className="w-4 h-4" />
                          My Profile
                        </button>
                        <button
                          onClick={() => {
                            onNavigate('portfolio');
                            setUserMenuOpen(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition flex items-center gap-2"
                        >
                          <BarChart3 className="w-4 h-4" />
                          My Investments
                        </button>
                        <button
                          onClick={() => {
                            setUserMenuOpen(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-50 transition flex items-center gap-2"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          Settings
                        </button>
                      </div>
                      
                      <div className="border-t border-gray-100 mt-1 pt-1">
                        <button
                          onClick={() => {
                            onLogout();
                            setUserMenuOpen(false);
                          }}
                          className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2 transition"
                        >
                          <LogOut className="w-4 h-4" />
                          Logout
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            ) : (
              <>
                <button 
                  onClick={onSignUpClick}
                  className="text-gray-700 hover:text-gray-900 font-medium px-4 py-2"
                >
                  sign in
                </button>
                <button 
                  onClick={onSignUpClick}
                  className="bg-black text-white px-6 py-3 rounded-md hover:bg-gray-800 font-medium transition-all hover:shadow-lg"
                >
                  Sign up
                </button>
              </>
            )}
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
            
            {user ? (
              <div className="pt-4 border-t border-gray-100 space-y-3">
                {/* User Info */}
                <div className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg">
                  <div className="w-10 h-10 bg-gray-900 rounded-full flex items-center justify-center">
                    <User className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-gray-900">{user.name}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                </div>

                {/* Services Section */}
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 mb-2">Services</p>
                  <button
                    onClick={() => {
                      onNavigate('portfolio');
                      setMobileMenuOpen(false);
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition"
                  >
                    <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
                      <BarChart3 className="w-4 h-4 text-blue-600" />
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-medium text-gray-900">Portfolio</p>
                      <p className="text-xs text-gray-500">Credit Ratings</p>
                    </div>
                  </button>
                  <button
                    onClick={() => {
                      onNavigate('scenarios');
                      setMobileMenuOpen(false);
                    }}
                    className="w-full flex items-center gap-3 px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-lg transition"
                  >
                    <div className="w-8 h-8 bg-purple-50 rounded-lg flex items-center justify-center">
                      <Activity className="w-4 h-4 text-purple-600" />
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-medium text-gray-900">Scenarios</p>
                      <p className="text-xs text-gray-500">Run Simulations</p>
                    </div>
                  </button>
                </div>

                {/* Account Section */}
                <div>
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-3 mb-2">Account</p>
                  <a href="#" className="block px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-lg">
                    My Profile
                  </a>
                  <a href="#" className="block px-3 py-2 text-gray-700 hover:bg-gray-50 rounded-lg">
                    Settings
                  </a>
                </div>
                
                <button 
                  onClick={() => {
                    onLogout();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full bg-red-50 text-red-600 px-6 py-3 rounded-md font-medium flex items-center justify-center gap-2 hover:bg-red-100 transition"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            ) : (
              <button 
                onClick={() => {
                  onSignUpClick();
                  setMobileMenuOpen(false);
                }}
                className="w-full bg-black text-white px-6 py-3 rounded-md font-medium mt-4"
              >
                Sign up
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
}