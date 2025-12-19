import { Routes, Route, Navigate } from "react-router-dom";
import GamesDashboard from "./pages/GamesDashboard";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>SmartLine</h1>
        <p>NFL Betting Intelligence</p>
      </header>

      <Routes>
        <Route path="/" element={<Navigate to="/games" replace />} />
        <Route path="/games" element={<GamesDashboard />} />
      </Routes>
    </div>
  );
}

export default App;