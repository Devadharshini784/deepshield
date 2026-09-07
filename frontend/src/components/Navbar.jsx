import { Link, useNavigate, useLocation } from "react-router-dom";

function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const name = localStorage.getItem("name");
  const isLoggedIn = !!localStorage.getItem("token");

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("name");
    navigate("/login");
  };

  if (!isLoggedIn) return null;

  const navLink = (path, label) => (
    <Link
      to={path}
      className={`text-sm font-medium px-3 py-2 rounded-md transition ${
        location.pathname === path
          ? "bg-blue-50 text-blue-700"
          : "text-slate-600 hover:bg-slate-50"
      }`}
    >
      {label}
    </Link>
  );

  return (
    <nav className="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center text-white font-bold text-sm">
            DS
          </div>
          <span className="font-bold text-slate-800 text-lg">DeepShield</span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {navLink("/dashboard", "Dashboard")}
          {navLink("/screenshot-analyzer", "Screenshot")}
          {navLink("/email-analyzer", "Email")}
          {navLink("/audio-analyzer", "Audio")}
          {navLink("/combined-analysis", "Combined")}
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500 hidden sm:inline">{name}</span>
          <button
            onClick={handleLogout}
            className="text-sm font-medium text-red-600 hover:bg-red-50 px-3 py-1.5 rounded-md transition"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;