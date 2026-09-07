import { useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge from "../components/RiskBadge";

function CombinedAnalysis() {
  const [screenshotFile, setScreenshotFile] = useState(null);
  const [screenshotTimestamp, setScreenshotTimestamp] = useState("");

  const [emailSender, setEmailSender] = useState("");
  const [emailDisplayName, setEmailDisplayName] = useState("");
  const [emailSubject, setEmailSubject] = useState("");
  const [emailBody, setEmailBody] = useState("");
  const [emailTimestamp, setEmailTimestamp] = useState("");

  const [audioFile, setAudioFile] = useState(null);
  const [audioTimestamp, setAudioTimestamp] = useState("");

  const [combinedResult, setCombinedResult] = useState(null);
  const [reportResult, setReportResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [error, setError] = useState("");

  const handleAnalyzeAll = async () => {
    setLoading(true);
    setError("");
    setCombinedResult(null);
    setReportResult(null);

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
        evidenceResults.push({
          type: "Screenshot",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
          content: res.data.extracted_text || "",
          timestamp: screenshotTimestamp || null,
        });
      }

      if (emailBody) {
        const res = await axios.post("http://127.0.0.1:5000/api/email/analyze", {
          sender_email: emailSender,
          display_name: emailDisplayName,
          subject: emailSubject,
          body: emailBody,
        });
        localEmailResult = res.data;
        evidenceResults.push({
          type: "Email",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
          content: emailBody,
          timestamp: emailTimestamp || null,
        });
      }

      if (audioFile) {
        const formData = new FormData();
        formData.append("file", audioFile);
        const res = await axios.post("http://127.0.0.1:5000/api/audio/upload", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        localAudioResult = res.data;
        evidenceResults.push({
          type: "Audio",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
          content: res.data.transcript || "",
          timestamp: audioTimestamp || null,
        });
      }

      if (evidenceResults.length === 0) {
        setError("Please provide at least one piece of evidence (screenshot, email, or audio)");
        setLoading(false);
        return;
      }

      const combineRes = await axios.post("http://127.0.0.1:5000/api/explain/combine", { evidence_results: evidenceResults });
      setCombinedResult(combineRes.data);

      const details = [];
      if (localScreenshotResult) details.push({
        type: "Screenshot", score: localScreenshotResult.risk_assessment.score,
        reasons: localScreenshotResult.risk_assessment.reasons,
        extracted_text: localScreenshotResult.extracted_text,
        timestamp: screenshotTimestamp || "Not specified",
      });
      if (localEmailResult) details.push({
        type: "Email", score: localEmailResult.risk_assessment.score,
        reasons: localEmailResult.risk_assessment.reasons,
        timestamp: emailTimestamp || "Not specified",
      });
      if (localAudioResult) details.push({
        type: "Audio", score: localAudioResult.risk_assessment.score,
        reasons: localAudioResult.risk_assessment.reasons,
        transcript: localAudioResult.labeled_transcript || localAudioResult.transcript,
        timestamp: audioTimestamp || "Not specified",
      });

      window.__deepshieldEvidenceDetails = details;
      window.__deepshieldScreenshotFilename = screenshotFile ? screenshotFile.name : null;
    } catch (err) {
      setError(err.response?.data?.error || "Something went wrong during analysis");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (!combinedResult) return;
    setGeneratingReport(true);
    setError("");
    try {
      const res = await axios.post("http://127.0.0.1:5000/api/report/generate", {
        combined_result: combinedResult,
        evidence_details: window.__deepshieldEvidenceDetails || [],
        screenshot_image_path: window.__deepshieldScreenshotFilename || null,
      });
      setReportResult(res.data);
    } catch (err) {
      setError(err.response?.data?.error || "Could not generate report");
    } finally {
      setGeneratingReport(false);
    }
  };

  const timestampField = (label, value, setValue) => (
    <div>
      <label className="block text-xs font-medium text-slate-500 mb-1">{label} (optional)</label>
      <input type="datetime-local" value={value} onChange={(e) => setValue(e.target.value)}
        className="w-full border border-slate-300 p-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
    </div>
  );

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-slate-800 mb-1">Combined Analysis</h1>
      <p className="text-slate-500 mb-6">
        Provide any combination of evidence. Adding when you received each item lets DeepShield catch
        inconsistencies, like a scammer quoting different amounts across a call and a screenshot.
      </p>

      <Card className="mb-6 space-y-6">
        <div>
          <h3 className="font-semibold text-slate-800 mb-2 text-sm uppercase tracking-wide text-slate-500">Screenshot (optional)</h3>
          <label className="block border-2 border-dashed border-slate-300 rounded-xl p-4 text-center cursor-pointer hover:border-blue-400 transition mb-2">
            <input type="file" accept=".png,.jpg,.jpeg" onChange={(e) => setScreenshotFile(e.target.files[0])} className="hidden" />
            <p className="text-slate-500 text-sm">{screenshotFile ? screenshotFile.name : "Click to select an image"}</p>
          </label>
          {timestampField("When did you receive this screenshot?", screenshotTimestamp, setScreenshotTimestamp)}
        </div>

        <div>
          <h3 className="font-semibold text-slate-800 mb-2 text-sm uppercase tracking-wide text-slate-500">Email (optional)</h3>
          <div className="grid sm:grid-cols-2 gap-2 mb-2">
            <input type="text" placeholder="Sender email" value={emailSender} onChange={(e) => setEmailSender(e.target.value)}
              className="border border-slate-300 p-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            <input type="text" placeholder="Display name" value={emailDisplayName} onChange={(e) => setEmailDisplayName(e.target.value)}
              className="border border-slate-300 p-2.5 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <input type="text" placeholder="Subject" value={emailSubject} onChange={(e) => setEmailSubject(e.target.value)}
            className="w-full border border-slate-300 p-2.5 rounded-lg mb-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <textarea placeholder="Paste email body here..." value={emailBody} onChange={(e) => setEmailBody(e.target.value)} rows={4}
            className="w-full border border-slate-300 p-2.5 rounded-lg text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          {timestampField("When did you receive this email?", emailTimestamp, setEmailTimestamp)}
        </div>

        <div>
          <h3 className="font-semibold text-slate-800 mb-2 text-sm uppercase tracking-wide text-slate-500">Audio (optional)</h3>
          <label className="block border-2 border-dashed border-slate-300 rounded-xl p-4 text-center cursor-pointer hover:border-blue-400 transition mb-2">
            <input type="file" accept=".mp3,.wav,.m4a,.ogg" onChange={(e) => setAudioFile(e.target.files[0])} className="hidden" />
            <p className="text-slate-500 text-sm">{audioFile ? audioFile.name : "Click to select a call recording"}</p>
          </label>
          {timestampField("When did you receive this call?", audioTimestamp, setAudioTimestamp)}
        </div>

        {error && <p className="text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-sm">{error}</p>}

        <button onClick={handleAnalyzeAll} disabled={loading}
          className="w-full bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition">
          {loading ? "Analyzing all evidence..." : "Analyze All Evidence"}
        </button>
      </Card>

      {combinedResult && (
        <Card className="space-y-5">
          <RiskBadge level={combinedResult.overall_level} score={combinedResult.combined_score} />

          <div className="flex items-center gap-2 text-sm text-slate-500">
            <span className="font-medium text-slate-700">Confidence:</span>
            <span className="px-2 py-0.5 rounded-full bg-slate-100 font-medium">{combinedResult.confidence}</span>
          </div>

          {combinedResult.time_window_findings && combinedResult.time_window_findings.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <h3 className="font-semibold text-red-700 mb-2">⚠ Cross-Evidence Inconsistencies Detected</h3>
              <ul className="space-y-1">
                {combinedResult.time_window_findings.map((f, i) => (
                  <li key={i} className="text-sm text-red-700">• {f}</li>
                ))}
              </ul>
            </div>
          )}

                    <div>
            <h3 className="font-semibold text-slate-800 mb-2">Explanation</h3>
            <div className="bg-slate-50 border border-slate-200 p-4 rounded-lg space-y-3">
              {(combinedResult.explanation_paragraphs || [combinedResult.explanation]).map((para, i) => (
                <p key={i} className="text-sm text-slate-600 leading-relaxed">{para}</p>
              ))}
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-slate-800 mb-2">Recommended Actions</h3>
            <ul className="space-y-1.5">
              {combinedResult.recommended_actions.map((action, i) => (
                <li key={i} className="text-sm text-slate-600 flex gap-2">
                  <span className="text-blue-500 shrink-0">✓</span><span>{action}</span>
                </li>
              ))}
            </ul>
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

export default CombinedAnalysis;