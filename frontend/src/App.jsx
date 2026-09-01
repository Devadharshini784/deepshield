import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ScreenshotAnalyzer from "./pages/ScreenshotAnalyzer";
import EmailAnalyzer from "./pages/EmailAnalyzer";
import AudioAnalyzer from "./pages/AudioAnalyzer";
import CombinedAnalysis from "./pages/CombinedAnalysis";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/screenshot-analyzer" element={<ScreenshotAnalyzer />} />
        <Route path="/email-analyzer" element={<EmailAnalyzer />} />
        <Route path="/audio-analyzer" element={<AudioAnalyzer />} />
        <Route path="/combined-analysis" element={<CombinedAnalysis />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;