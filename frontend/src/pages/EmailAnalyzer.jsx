import { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

function EmailAnalyzer() {
  const [senderEmail, setSenderEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyze = async () => {
    if (!body) {
      setError("Please paste the email content");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await axios.post("http://127.0.0.1:5000/api/email/analyze", {
        sender_email: senderEmail,
        display_name: displayName,
        subject,
        body,
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
          <h1 className="text-2xl font-bold">Email Analyzer</h1>
          <Link to="/dashboard" className="text-blue-600 hover:underline">Back to Dashboard</Link>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-md mb-6 space-y-4">
          <input
            type="text"
            placeholder="Sender email (e.g. support@paypal-secure.xyz)"
            value={senderEmail}
            onChange={(e) => setSenderEmail(e.target.value)}
            className="w-full border p-2 rounded"
          />
          <input
            type="text"
            placeholder="Display name (e.g. PayPal Support)"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            className="w-full border p-2 rounded"
          />
          <input
            type="text"
            placeholder="Subject"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className="w-full border p-2 rounded"
          />
          <textarea
            placeholder="Paste the full email body here..."
            value={body}
            onChange={(e) => setBody(e.target.value)}
            rows={8}
            className="w-full border p-2 rounded"
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? "Analyzing..." : "Analyze Email"}
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

            <h3 className="font-semibold mb-2">URLs Found</h3>
            {result.urls_found.length > 0 ? (
              <ul className="text-sm text-gray-700 list-disc list-inside">
                {result.urls_found.map((u, i) => (
                  <li key={i} className={u.suspicious ? "text-red-600" : ""}>
                    {u.url} {u.suspicious ? `- ${u.reason}` : "- looks normal"}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-gray-500">No URLs found</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default EmailAnalyzer;