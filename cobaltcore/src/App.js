import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import FeaturedIn from './components/FeaturedIn';
import ValueProposition from './components/ValueProposition';
import Features from './components/Features';
import RecentDeals from './components/RecentDeals';
import Testimonials from './components/Testimonials';
import CTA from './components/CTA';
import Footer from './components/Footer';
import LoginModal from './components/LoginModal';
import Portfolio from './components/Portfolio';
import Scenarios from './components/Scenarios';
import authService from './services/authService';

export default function App() {
  const [loginModalOpen, setLoginModalOpen] = useState(false);
  const [user, setUser] = useState(null);
  const [currentPage, setCurrentPage] = useState('home'); // 'home', 'portfolio', 'scenarios'

  // Check if user is logged in on mount
  useEffect(() => {
    const currentUser = authService.getCurrentUser();
    if (currentUser) {
      setUser(currentUser);
      setCurrentPage('portfolio'); // Redirect to portfolio on login
    }
  }, []);

  const handleSignUpClick = () => {
    setLoginModalOpen(true);
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    setCurrentPage('portfolio'); // Redirect to portfolio after login
  };

  const handleLogout = async () => {
    await authService.logout();
    setUser(null);
    setCurrentPage('home');
  };

  const handleNavigate = (page) => {
    setCurrentPage(page);
  };

  // Render the appropriate page
  const renderPage = () => {
    switch (currentPage) {
      case 'portfolio':
        return <Portfolio user={user} onBack={() => handleNavigate('home')} />;
      case 'scenarios':
        return <Scenarios user={user} onBack={() => handleNavigate('home')} />;
      case 'home':
      default:
        return (
          <>
            <Hero onSignUpClick={handleSignUpClick} />
            <FeaturedIn />
            <ValueProposition />
            <Features />
            <RecentDeals />
            <Testimonials />
            <CTA onSignUpClick={handleSignUpClick} />
            <Footer />
          </>
        );
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <Header
        onSignUpClick={handleSignUpClick}
        user={user}
        onLogout={handleLogout}
        onNavigate={handleNavigate}
      />
      
      {renderPage()}
      
      {/* Single Global Login Modal */}
      <LoginModal 
        isOpen={loginModalOpen} 
        onClose={() => setLoginModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  );
}