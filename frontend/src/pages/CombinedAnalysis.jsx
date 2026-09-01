import { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

function CombinedAnalysis() {
  const [screenshotFile, setScreenshotFile] = useState(null);
  const [audioFile, setAudioFile] = useState(null);
  const [emailBody, setEmailBody] = useState("");
  const [emailSender, setEmailSender] = useState("");

  const [screenshotResult, setScreenshotResult] = useState(null);
  const [emailResult, setEmailResult] = useState(null);
  const [audioResult, setAudioResult] = useState(null);
  const [combinedResult, setCombinedResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyzeAll = async () => {
    setLoading(true);
    setError("");
    setCombinedResult(null);

    const evidenceResults = [];
    let localScreenshotResult = null;
    let localEmailResult = null;
    let localAudioResult = null;

    try {
      if (screenshotFile) {
        const formData = new FormData();
        formData.append("file", screenshotFile);
        const res = await axios.post("http://127.0.0.1:5000/api/screenshot/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        localScreenshotResult = res.data;
        setScreenshotResult(res.data);
        evidenceResults.push({
          type: "Screenshot",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
        });
      }

      if (emailBody) {
        const res = await axios.post("http://127.0.0.1:5000/api/email/analyze", {
          sender_email: emailSender,
          display_name: "",
          subject: "",
          body: emailBody,
        });
        localEmailResult = res.data;
        setEmailResult(res.data);
        evidenceResults.push({
          type: "Email",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
        });
      }

      if (audioFile) {
        const formData = new FormData();
        formData.append("file", audioFile);
        const res = await axios.post("http://127.0.0.1:5000/api/audio/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        localAudioResult = res.data;
        setAudioResult(res.data);
        evidenceResults.push({
          type: "Audio",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
        });
      }

      if (evidenceResults.length === 0) {
        setError("Please provide at least one piece of evidence (screenshot, email, or audio)");
        setLoading(false);
        return;
      }

      const combineRes = await axios.post("http://127.0.0.1:5000/api/explain/combine", {
        evidence_results: evidenceResults,
      });
      setCombinedResult(combineRes.data);
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong during analysis");
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
          <h1 className="text-2xl font-bold">Combined Analysis</h1>
          <Link to="/dashboard" className="text-blue-600 hover:underline">Back to Dashboard</Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md mb-6 space-y-6">
          <div>
            <h3 className="font-semibold mb-2">Screenshot (optional)</h3>
            <input
              type="file"
              accept=".png,.jpg,.jpeg"
              onChange={(e) => setScreenshotFile(e.target.files[0])}
            />
          </div>

          <div>
            <h3 className="font-semibold mb-2">Email (optional)</h3>
            <input
              type="text"
              placeholder="Sender email"
              value={emailSender}
              onChange={(e) => setEmailSender(e.target.value)}
              className="w-full border p-2 rounded mb-2"
            />
            <textarea
              placeholder="Paste email body here..."
              value={emailBody}
              onChange={(e) => setEmailBody(e.target.value)}
              rows={4}
              className="w-full border p-2 rounded"
            />
          </div>

          <div>
            <h3 className="font-semibold mb-2">Audio (optional)</h3>
            <input
              type="file"
              accept=".mp3,.wav,.m4a,.ogg"
              onChange={(e) => setAudioFile(e.target.files[0])}
            />
          </div>

          {error && <p className="text-red-500 text-sm">{error}</p>}

          <button
            onClick={handleAnalyzeAll}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Analyzing all evidence..." : "Analyze All Evidence"}
          </button>
        </div>

        {combinedResult && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className={`p-4 rounded border mb-4 ${getRiskColor(combinedResult.overall_level)}`}>
              <h2 className="text-lg font-bold">{combinedResult.overall_level}</h2>
              <p>Combined Risk Score: {combinedResult.combined_score}/100</p>
              <p>Confidence Level: {combinedResult.confidence}</p>
            </div>

            <h3 className="font-semibold mb-2">Explanation</h3>
            <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded mb-4">
              {combinedResult.explanation}
            </p>

            <h3 className="font-semibold mb-2">Recommended Actions</h3>
            <ul className="list-disc list-inside text-sm text-gray-700">
              {combinedResult.recommended_actions.map((action, i) => (
                <li key={i}>{action}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default CombinedAnalysis;