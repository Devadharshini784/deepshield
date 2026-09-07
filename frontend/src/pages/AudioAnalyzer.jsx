import { useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge from "../components/RiskBadge";

function AudioAnalyzer() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reportResult, setReportResult] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError("");
  };

  const handleUpload = async () => {
    if (!file) return setError("Please select an audio file first");
    setLoading(true);
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await axios.post("http://127.0.0.1:5000/api/audio/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
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
          type: "Audio",
          score: result.risk_assessment.score,
          reasons: result.risk_assessment.reasons,
          content: result.transcript || "",
        }],
      });
      const reportRes = await axios.post("http://127.0.0.1:5000/api/report/generate", {
        combined_result: combineRes.data,
        evidence_details: [{
          type: "Audio",
          score: result.risk_assessment.score,
          reasons: result.risk_assessment.reasons,
          transcript: result.labeled_transcript || result.transcript,
        }],
      });
      setReportResult(reportRes.data);
    } catch (err) {
      setError(err.response?.data?.error || "Could not generate report");
    } finally {
      setGeneratingReport(false);
    }
  };

  const renderList = (title, items) => (
    <div>
      <h3 className="font-semibold text-slate-800 mb-2">{title}</h3>
      {items.length > 0 ? (
        <ul className="space-y-1">
          {items.map((item, i) => <li key={i} className="text-sm text-slate-600">• {item}</li>)}
        </ul>
      ) : (
        <p className="text-sm text-slate-400">None detected</p>
      )}
    </div>
  );

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Audio Analyzer</h1>

      <Card className="mb-6">
        <label className="block border-2 border-dashed border-slate-300 rounded-xl p-6 text-center cursor-pointer hover:border-blue-400 transition mb-4">
          <input type="file" accept=".mp3,.wav,.m4a,.ogg" onChange={handleFileChange} className="hidden" />
          <p className="text-slate-500 text-sm">{file ? file.name : "Click to select a call recording (mp3, wav, m4a)"}</p>
        </label>
        {error && <p className="text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4 text-sm">{error}</p>}
        <button onClick={handleUpload} disabled={loading}
          className="w-full bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition">
          {loading ? "Transcribing, identifying speakers & analyzing..." : "Analyze Audio"}
        </button>
      </Card>

      {result && (
        <Card className="space-y-5">
          <RiskBadge level={result.risk_assessment.level} score={result.risk_assessment.score} aiVerified={result.risk_assessment.ai_verified} />

          <div>
            <h3 className="font-semibold text-slate-800 mb-2">Reasons</h3>
            <ul className="space-y-1.5">
              {result.risk_assessment.reasons.map((r, i) => (
                <li key={i} className="text-sm text-slate-600 flex gap-2">
                  <span className="text-slate-400 shrink-0">•</span><span>{r}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-slate-800 mb-2">
              Transcript {result.speaker_count > 0 && `(${result.speaker_count} speaker${result.speaker_count > 1 ? "s" : ""} identified)`}
            </h3>
            {result.labeled_transcript ? (
              <div className="text-sm text-slate-600 bg-slate-50 border border-slate-200 p-3 rounded-lg space-y-2">
                {result.speaker_segments.map((seg, i) => (
                  <p key={i}>
                    <span className="font-semibold text-blue-700">{seg.speaker}:</span> {seg.text}
                  </p>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-600 bg-slate-50 border border-slate-200 p-3 rounded-lg whitespace-pre-wrap">
                {result.transcript || "No speech detected"}
              </p>
            )}
          </div>

          {result.is_repeated_script && (
            <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-lg p-3 font-medium">
              ⚠ This message repeats itself almost word-for-word — typical of a pre-recorded scam robocall.
            </div>
          )}

          <div className="grid sm:grid-cols-2 gap-5">
            {renderList("Scam Keywords", result.scam_keywords_found)}
            {renderList("Money Request Keywords", result.money_request_keywords)}
            {renderList("OTP Request Keywords", result.otp_keywords)}
            {renderList("Emotional Manipulation", result.manipulation_keywords)}
            {renderList("Robocall Script Phrases", result.robocall_keywords_found)}
            {renderList("Phone Numbers Mentioned", result.phone_numbers_found)}
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

export default AudioAnalyzer;