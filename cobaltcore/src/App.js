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
import UnderConstruction from './components/UnderConstruction';
import About from './components/About';
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
    // Resource pages
    if (currentPage.startsWith('methodology-')) {
      const industryMap = {
        'methodology-midstream-energy': 'Midstream Energy',
        'methodology-manufacturing': 'Manufacturing',
        'methodology-diversified-technology': 'Diversified Technology',
        'methodology-retail-apparel': 'Retail and Apparel',
        'methodology-communications-infrastructure': 'Communications Infrastructure',
        'methodology-gaming': 'Gaming',
        'methodology-media': 'Media',
        'methodology-soft-beverages': 'Soft Beverages',
        'methodology-unregulated-utilities': 'Unregulated Utilities and Power Companies',
        'methodology-semiconductors': 'Semiconductors',
        'methodology-automobile-manufacturers': 'Automobile Manufacturers',
        'methodology-equipment-transportation-rental': 'Equipment and Transportation Rental',
        'methodology-medical-products-devices': 'Medical Products and Devices',
        'methodology-protein-agriculture': 'Protein and Agriculture',
        'methodology-oilfield-services': 'Oilfield Services',
        'methodology-homebuilding-property-development': 'Homebuilding and Property Development',
        'methodology-shipping': 'Shipping',
        'methodology-pharmaceuticals': 'Pharmaceuticals',
        'methodology-steel': 'Steel',
        'methodology-alcoholic-beverages': 'Alcoholic Beverages',
      };
      return (
        <UnderConstruction
          user={user}
          onBack={() => handleNavigate('home')}
          industry={industryMap[currentPage] || 'Methodologies'}
        />
      );
    }

    switch (currentPage) {
      case 'portfolio':
        return <Portfolio user={user} onBack={() => handleNavigate('home')} />;
      case 'scenarios':
        return <Scenarios user={user} onBack={() => handleNavigate('home')} />;
      case 'about':
        return <About user={user} onBack={() => handleNavigate('home')} />;
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