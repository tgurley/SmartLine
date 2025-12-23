// pages/Analytics.jsx
import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import WeatherAnalytics from './WeatherAnalytics';

const AnalyticPage = () => {
  const location = useLocation();
  const currentTab = location.pathname.includes('weather') ? 'weather' : 'overview';
  
  return (
    <div>
      {/* Tab Navigation */}
      <div className="flex gap-4 border-b border-dark-700 mb-8">
        <Link 
          to="/analytics"
          className={`px-4 py-2 ${currentTab === 'overview' ? 'border-b-2 border-primary-500 text-white' : 'text-slate-400'}`}
        >
          Overview
        </Link>
        <Link 
          to="/analytics/weather"
          className={`px-4 py-2 ${currentTab === 'weather' ? 'border-b-2 border-primary-500 text-white' : 'text-slate-400'}`}
        >
          Weather Impact
        </Link>
        <Link 
          to="/analytics/lines"
          className={`px-4 py-2 text-slate-400`}
        >
          Line Movement
        </Link>
      </div>
      
      {/* Content based on route */}
      {currentTab === 'weather' ? <WeatherAnalytics /> : <div>Overview content</div>}
    </div>
  );
};

export default AnalyticPage;