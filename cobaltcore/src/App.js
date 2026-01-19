import React, { useState } from 'react';
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

export default function App() {
  const [loginModalOpen, setLoginModalOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      <Header />
      <Hero onSignUpClick={() => setLoginModalOpen(true)} />
      <FeaturedIn />
      <ValueProposition />
      <Features />
      <RecentDeals />
      <Testimonials />
      <CTA onSignUpClick={() => setLoginModalOpen(true)} />
      <Footer />
      
      <LoginModal isOpen={loginModalOpen} onClose={() => setLoginModalOpen(false)} />
    </div>
  );
}