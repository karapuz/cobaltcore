import React from 'react';
import Header from './components/Header';
import Hero from './components/Hero';
import FeaturedIn from './components/FeaturedIn';
import ValueProposition from './components/ValueProposition';
import Features from './components/Features';
import RecentDeals from './components/RecentDeals';
import Testimonials from './components/Testimonials';
import CTA from './components/CTA';
import Footer from './components/Footer';

export default function App() {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      <Hero />
      <FeaturedIn />
      <ValueProposition />
      <Features />
      <RecentDeals />
      <Testimonials />
      <CTA />
      <Footer />
    </div>
  );
}