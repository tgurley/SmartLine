import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import AppLayout from './components/layout/AppLayout';
import Dashboard from './pages/Dashboard';
import GamesPage from './pages/GamesPage';
import GameDetailPage from './pages/GameDetailPage';
import AnalyticsPage from './pages/AnalyticsPage';
import WeatherAnalytics from './pages/WeatherAnalytics';
import PlayerDetailPage from './pages/PlayerDetailPage';
import TeamDetailPage from './pages/TeamDetailPage';

// Placeholder pages - to be built later
const OddsPage = () => (
  <div>
    <h1 className="text-3xl font-display font-bold text-white mb-4">Odds</h1>
    <p className="text-slate-400">Odds comparison page coming soon...</p>
  </div>
);

// const AnalyticsPage = () => (
//   <div>
//     <h1 className="text-3xl font-display font-bold text-white mb-4">Analytics</h1>
//     <p className="text-slate-400">Analytics overview page coming soon...</p>
//   </div>
// );

const StandingsPage = () => (
  <div>
    <h1 className="text-3xl font-display font-bold text-white mb-4">Standings</h1>
    <p className="text-slate-400">Standings page coming soon...</p>
  </div>
);

const SettingsPage = () => (
  <div>
    <h1 className="text-3xl font-display font-bold text-white mb-4">Settings</h1>
    <p className="text-slate-400">Settings page coming soon...</p>
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<LoginPage />} /> {/* Same as login for now */}
        
        {/* App Routes (with layout) */}
        <Route path="/" element={<AppLayout />}>
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="games" element={<GamesPage />} />
          <Route path="games/:gameId" element={<GameDetailPage />} />
          <Route path="players/:playerId" element={<PlayerDetailPage />} />
          <Route path="teams/:teamId" element={<TeamDetailPage />} />
          <Route path="odds" element={<OddsPage />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="analytics/weather" element={<WeatherAnalytics />} />
          <Route path="standings" element={<StandingsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        
        {/* Catch all - redirect to landing */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
