import { useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge from "../components/RiskBadge";

function EmailAnalyzer() {
  const [senderEmail, setSenderEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reportResult, setReportResult] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const handleAnalyze = async () => {
    if (!body) return setError("Please paste the email content");
    setLoading(true);
    setError("");
    try {
      const res = await axios.post("http://127.0.0.1:5000/api/email/analyze", {
        sender_email: senderEmail, display_name: displayName, subject, body,
      });
      setResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  
  const handleGenerateReport = async () => {
    if (!result) return;
    setGeneratingReport(true);
    setError("");
    try {
      const combineRes = await axios.post("http://127.0.0.1:5000/api/explain/combine", {
        evidence_results: [{
          type: "Email",
          score: result.risk_assessment.score,
          reasons: result.risk_assessment.reasons,
          content: body,
        }],
      });
      const reportRes = await axios.post("http://127.0.0.1:5000/api/report/generate", {
        combined_result: combineRes.data,
        evidence_details: [{
          type: "Email",
          score: result.risk_assessment.score,
          reasons: result.risk_assessment.reasons,
        }],
      });
      setReportResult(reportRes.data);
    } catch (err) {
      setError(err.response?.data?.error || "Could not generate report");
    } finally {
      setGeneratingReport(false);
    }
  };

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Email Analyzer</h1>

      <Card className="mb-6 space-y-3">
        <div className="grid sm:grid-cols-2 gap-3">
          <input type="text" placeholder="Sender email" value={senderEmail} onChange={(e) => setSenderEmail(e.target.value)}
            className="border border-slate-300 p-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <input type="text" placeholder="Display name" value={displayName} onChange={(e) => setDisplayName(e.target.value)}
            className="border border-slate-300 p-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <input type="text" placeholder="Subject" value={subject} onChange={(e) => setSubject(e.target.value)}
          className="w-full border border-slate-300 p-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <textarea placeholder="Paste the full email body here..." value={body} onChange={(e) => setBody(e.target.value)} rows={7}
          className="w-full border border-slate-300 p-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        {error && <p className="text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">{error}</p>}
        <button onClick={handleAnalyze} disabled={loading}
          className="w-full bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition">
          {loading ? "Analyzing..." : "Analyze Email"}
        </button>
      </Card>

      {result && (
        <Card className="space-y-5">
          <RiskBadge level={result.risk_assessment.level} score={result.risk_assessment.score} aiVerified={result.risk_assessment.ai_verified} />

          <div>
            <h3 className="font-semibold text-slate-800 mb-2">Reasons</h3>
            <ul className="space-y-1.5">
              {result.risk_assessment.reasons.map((r, i) => (
                <li key={i} className="text-sm text-slate-600 flex gap-2 leading-relaxed">
                  <span className="text-slate-400 shrink-0">•</span><span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-slate-800 mb-2">URLs Found</h3>
            {result.urls_found.length > 0 ? (
              <div className="space-y-2">
                {result.urls_found.map((u, i) => (
                  <div key={i} className={`text-sm p-2.5 rounded-lg border ${u.suspicious ? "bg-red-50 border-red-200 text-red-700" : "bg-slate-50 border-slate-200 text-slate-600"}`}>
                    <p className="font-medium break-all">{u.url}</p>
                    <p className="text-xs mt-1 opacity-80">{u.suspicious ? u.reason : "Looks normal"}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400">No URLs found</p>
            )}
          </div>

          <button onClick={handleGenerateReport} disabled={generatingReport}
            className="bg-emerald-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 transition">
            {generatingReport ? "Generating PDF..." : "Generate Report"}
          </button>

          {reportResult && (
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="font-semibold text-slate-800">Case ID: {reportResult.case_id}</p>
                <p className="text-xs text-slate-500">Generated: {reportResult.created_at}</p>
              </div>
              <a href={`http://127.0.0.1:5000${reportResult.download_url}`} target="_blank" rel="noreferrer"
                className="bg-white border border-emerald-300 text-emerald-700 font-medium text-sm px-4 py-2 rounded-lg hover:bg-emerald-100 transition">
                Download PDF
              </a>
            </div>
          )}
        </Card>
      )}
    </Layout>
  );
}

export default EmailAnalyzer;