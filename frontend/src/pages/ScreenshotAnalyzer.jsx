import { useState } from "react";
import axios from "axios";
import Layout from "../components/Layout";
import Card from "../components/Card";
import RiskBadge from "../components/RiskBadge";

function ScreenshotAnalyzer() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [reportResult, setReportResult] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    setFile(selected);
    setResult(null);
    setError("");
    if (selected) setPreview(URL.createObjectURL(selected));
  };

  const handleUpload = async () => {
    if (!file) return setError("Please select an image first");
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

  
  const handleGenerateReport = async () => {
    if (!result) return;
    setGeneratingReport(true);
    setError("");
    try {
      const combineRes = await axios.post("http://127.0.0.1:5000/api/explain/combine", {
        evidence_results: [{
          type: "Screenshot",
          score: result.risk_assessment.score,
          reasons: result.risk_assessment.reasons,
          content: result.extracted_text || "",
        }],
      });
      const reportRes = await axios.post("http://127.0.0.1:5000/api/report/generate", {
        combined_result: combineRes.data,
        evidence_details: [{
          type: "Screenshot",
          score: result.risk_assessment.score,
          reasons: result.risk_assessment.reasons,
          extracted_text: result.extracted_text,
        }],
        screenshot_image_path: file ? file.name : null,
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
      <h1 className="text-2xl font-bold text-slate-800 mb-6">Screenshot Analyzer</h1>

      <Card className="mb-6">
        <label className="block border-2 border-dashed border-slate-300 rounded-xl p-6 text-center cursor-pointer hover:border-blue-400 transition mb-4">
          <input type="file" accept=".png,.jpg,.jpeg" onChange={handleFileChange} className="hidden" />
          <p className="text-slate-500 text-sm">{file ? file.name : "Click to select a screenshot (PNG, JPG)"}</p>
        </label>
        {preview && <img src={preview} alt="preview" className="max-h-64 rounded-lg mb-4 border border-slate-200 mx-auto" />}
        {error && <p className="text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2 mb-4 text-sm">{error}</p>}
        <button onClick={handleUpload} disabled={loading}
          className="w-full bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition">
          {loading ? "Analyzing..." : "Analyze Screenshot"}
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
                  <span className="text-slate-400">•</span>{r}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="font-semibold text-slate-800 mb-2">Extracted Text</h3>
            <p className="text-sm text-slate-600 bg-slate-50 border border-slate-200 p-3 rounded-lg whitespace-pre-wrap">
              {result.extracted_text || "No text found"}
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-slate-800 mb-2">QR Codes Found</h3>
            {result.qr_codes.length > 0 ? (
              <ul className="space-y-1">
                {result.qr_codes.map((qr, i) => (
                  <li key={i} className="text-sm text-slate-600">• {qr.data}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-slate-400">No QR codes detected</p>
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

export default ScreenshotAnalyzer;