import { useNavigate, Link } from "react-router-dom";
import { useEffect, useState } from "react";

function Dashboard() {
  const navigate = useNavigate();
  const [name, setName] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/login");
    } else {
      setName(localStorage.getItem("name") || "User");
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("name");
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Welcome, {name}</h1>
        <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
          Logout
        </button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/screenshot-analyzer" className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
          <h2 className="font-semibold text-lg mb-2">Screenshot Analyzer</h2>
          <p className="text-sm text-gray-500">Check payment screenshots and images for scam signs</p>
        </Link>
        <Link to="/email-analyzer" className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
          <h2 className="font-semibold text-lg mb-2">Email Analyzer</h2>
          <p className="text-sm text-gray-500">Check emails for phishing and scam indicators</p>
        </Link>
        <Link to="/audio-analyzer" className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
          <h2 className="font-semibold text-lg mb-2">Audio Analyzer</h2>
          <p className="text-sm text-gray-500">Check call recordings for scam language and OTP requests</p>
        </Link>
        <Link to="/combined-analysis" className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
          <h2 className="font-semibold text-lg mb-2">Combined Analysis</h2>
          <p className="text-sm text-gray-500">Analyze multiple evidence types together for one verdict</p>
        </Link>
      </div>
    </div>
  );
}

export default Dashboard;