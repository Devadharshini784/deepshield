import { useNavigate, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Card from "../components/Card";

function Dashboard() {
  const navigate = useNavigate();
  const [name, setName] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) navigate("/login");
    else setName(localStorage.getItem("name") || "User");
  }, [navigate]);

  const tools = [
    { to: "/screenshot-analyzer", title: "Screenshot Analyzer", desc: "Check payment screenshots and images for scam signs", icon: "🖼️" },
    { to: "/email-analyzer", title: "Email Analyzer", desc: "Check emails for phishing and scam indicators", icon: "📧" },
    { to: "/audio-analyzer", title: "Audio Analyzer", desc: "Check call recordings for scam language and OTP requests", icon: "🎙️" },
    { to: "/combined-analysis", title: "Combined Analysis", desc: "Analyze multiple evidence types together for one verdict", icon: "🛡️" },
  ];

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Welcome back, {name}</h1>
      <p className="text-slate-500 mb-8">Choose a tool below to start analyzing suspicious content.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {tools.map((tool) => (
          <Link key={tool.to} to={tool.to}>
            <Card className="hover:shadow-md hover:border-blue-300 transition h-full">
              <div className="text-3xl mb-3">{tool.icon}</div>
              <h2 className="font-semibold text-slate-800 mb-1">{tool.title}</h2>
              <p className="text-sm text-slate-500">{tool.desc}</p>
            </Card>
          </Link>
        ))}
      </div>
    </Layout>
  );
}

export default Dashboard;