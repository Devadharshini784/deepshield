import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

function ScreenshotAnalyzer() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    setFile(selected);
    setResult(null);
    setError("");
    if (selected) {
      setPreview(URL.createObjectURL(selected));
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select an image first");
      return;
    }
    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://127.0.0.1:5000/api/screenshot/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (level) => {
    if (level === "High Risk") return "text-red-600 bg-red-50 border-red-300";
    if (level === "Medium Risk") return "text-yellow-600 bg-yellow-50 border-yellow-300";
    return "text-green-600 bg-green-50 border-green-300";
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-3xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Screenshot Analyzer</h1>
          <Link to="/dashboard" className="text-blue-600 hover:underline">Back to Dashboard</Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <input
            type="file"
            accept=".png,.jpg,.jpeg"
            onChange={handleFileChange}
            className="mb-4 block"
          />
          {preview && (
            <img src={preview} alt="preview" className="max-h-64 rounded mb-4 border" />
          )}
          {error && <p className="text-red-500 mb-4 text-sm">{error}</p>}
          <button
            onClick={handleUpload}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Analyzing..." : "Analyze Screenshot"}
          </button>
        </div>

        {result && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className={`p-4 rounded border mb-4 ${getRiskColor(result.risk_assessment.level)}`}>
              <h2 className="text-lg font-bold">{result.risk_assessment.level}</h2>
              <p>Risk Score: {result.risk_assessment.score}/100</p>
            </div>

            <h3 className="font-semibold mb-2">Reasons</h3>
            <ul className="list-disc list-inside mb-4 text-sm text-gray-700">
              {result.risk_assessment.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>

            <h3 className="font-semibold mb-2">Extracted Text</h3>
            <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded mb-4 whitespace-pre-wrap">
              {result.extracted_text || "No text found"}
            </p>

            <h3 className="font-semibold mb-2">QR Codes Found</h3>
            {result.qr_codes.length > 0 ? (
              <ul className="text-sm text-gray-700 list-disc list-inside">
                {result.qr_codes.map((qr, i) => (
                  <li key={i}>{qr.data}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No QR codes detected</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ScreenshotAnalyzer;