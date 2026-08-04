import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ScreenshotAnalyzer from "./pages/ScreenshotAnalyzer";
import EmailAnalyzer from "./pages/EmailAnalyzer";

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
      </Routes>
    </BrowserRouter>
  );
}

export default App;