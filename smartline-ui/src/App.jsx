import { Routes, Route, Navigate } from "react-router-dom";
import GamesDashboard from "./pages/GamesDashboard";
import GameDetail from "./pages/GameDetail";
import Analytics from "./pages/Analytics";


function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>SmartLine</h1>
        <p>NFL Betting Intelligence</p>
      </header>

      <main className="app-content">
        <Routes>
          <Route path="/" element={<Navigate to="/games" replace />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/games" element={<GamesDashboard />} />
          <Route path="/game/:gameId" element={<GameDetail />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
