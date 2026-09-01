import { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

function CombinedAnalysis() {
  const [screenshotFile, setScreenshotFile] = useState(null);
  const [reportResult, setReportResult] = useState(null);
  const [generatingReport, setGeneratingReport] = useState(false);

  const [audioFile, setAudioFile] = useState(null);

  const [emailBody, setEmailBody] = useState("");
  const [emailSender, setEmailSender] = useState("");

  const [screenshotResult, setScreenshotResult] = useState(null);
  const [emailResult, setEmailResult] = useState(null);
  const [audioResult, setAudioResult] = useState(null);
  const [combinedResult, setCombinedResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // -----------------------------------------
  // ANALYZE ALL EVIDENCE
  // -----------------------------------------
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
      // -----------------------------------------
      // SCREENSHOT ANALYSIS
      // -----------------------------------------
      if (screenshotFile) {
        const formData = new FormData();
        formData.append("file", screenshotFile);

        const res = await axios.post(
          "http://127.0.0.1:5000/api/screenshot/upload",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        localScreenshotResult = res.data;
        setScreenshotResult(res.data);

        evidenceResults.push({
          type: "Screenshot",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
        });
      }

      // -----------------------------------------
      // EMAIL ANALYSIS
      // -----------------------------------------
      if (emailBody.trim()) {
        const res = await axios.post(
          "http://127.0.0.1:5000/api/email/analyze",
          {
            sender_email: emailSender,
            display_name: "",
            subject: "",
            body: emailBody,
          }
        );

        localEmailResult = res.data;
        setEmailResult(res.data);

        evidenceResults.push({
          type: "Email",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
        });
      }

      // -----------------------------------------
      // AUDIO ANALYSIS
      // -----------------------------------------
      if (audioFile) {
        const formData = new FormData();
        formData.append("file", audioFile);

        const res = await axios.post(
          "http://127.0.0.1:5000/api/audio/upload",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        localAudioResult = res.data;
        setAudioResult(res.data);

        evidenceResults.push({
          type: "Audio",
          score: res.data.risk_assessment.score,
          reasons: res.data.risk_assessment.reasons,
        });
      }

      // -----------------------------------------
      // CHECK IF ANY EVIDENCE WAS PROVIDED
      // -----------------------------------------
      if (evidenceResults.length === 0) {
        setError(
          "Please provide at least one piece of evidence (screenshot, email, or audio)."
        );

        setLoading(false);
        return;
      }

      // -----------------------------------------
      // COMBINE RESULTS
      // -----------------------------------------
      const combineRes = await axios.post(
        "http://127.0.0.1:5000/api/explain/combine",
        {
          evidence_results: evidenceResults,
        }
      );

      setCombinedResult(combineRes.data);

      // -----------------------------------------
      // BUILD FULL EVIDENCE DETAILS
      // FOR PDF REPORT
      // -----------------------------------------
      const details = [];

      if (localScreenshotResult) {
        details.push({
          type: "Screenshot",
          score: localScreenshotResult.risk_assessment.score,
          reasons: localScreenshotResult.risk_assessment.reasons,
          extracted_text: localScreenshotResult.extracted_text,
        });
      }

      if (localEmailResult) {
        details.push({
          type: "Email",
          score: localEmailResult.risk_assessment.score,
          reasons: localEmailResult.risk_assessment.reasons,
          sender_email: emailSender,
          body: emailBody,
        });
      }

      if (localAudioResult) {
        details.push({
          type: "Audio",
          score: localAudioResult.risk_assessment.score,
          reasons: localAudioResult.risk_assessment.reasons,
          transcript: localAudioResult.transcript,
        });
      }

      // Store evidence details temporarily
      window.__deepshieldEvidenceDetails = details;

      // Store screenshot filename
      window.__deepshieldScreenshotFilename = screenshotFile
        ? screenshotFile.name
        : null;
    } catch (err) {
      console.error("Analysis error:", err);

      setError(
        err.response?.data?.error ||
          "Something went wrong during analysis."
      );
    } finally {
      setLoading(false);
    }
  };

  // -----------------------------------------
  // RISK COLOR
  // -----------------------------------------
  const getRiskColor = (level) => {
    if (level === "High Risk") {
      return "text-red-600 bg-red-50 border-red-300";
    }

    if (level === "Medium Risk") {
      return "text-yellow-600 bg-yellow-50 border-yellow-300";
    }

    return "text-green-600 bg-green-50 border-green-300";
  };

  // -----------------------------------------
  // GENERATE PDF REPORT
  // -----------------------------------------
  const handleGenerateReport = async () => {
    if (!combinedResult) {
      return;
    }

    setGeneratingReport(true);
    setError("");

    try {
      const res = await axios.post(
        "http://127.0.0.1:5000/api/report/generate",
        {
          combined_result: combinedResult,

          evidence_details:
            window.__deepshieldEvidenceDetails || [],

          screenshot_image_path:
            window.__deepshieldScreenshotFilename || null,
        }
      );

      setReportResult(res.data);
    } catch (err) {
      console.error("Report generation error:", err);

      setError(
        err.response?.data?.error ||
          "Could not generate report."
      );
    } finally {
      setGeneratingReport(false);
    }
  };

  // -----------------------------------------
  // UI
  // -----------------------------------------
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-3xl mx-auto">

        {/* HEADER */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">
            Combined Analysis
          </h1>

          <Link
            to="/dashboard"
            className="text-blue-600 hover:underline"
          >
            Back to Dashboard
          </Link>
        </div>

        {/* -----------------------------------------
            INPUT SECTION
        ----------------------------------------- */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6 space-y-6">

          {/* SCREENSHOT */}
          <div>
            <h3 className="font-semibold mb-2">
              Screenshot (optional)
            </h3>

            <input
              type="file"
              accept=".png,.jpg,.jpeg"
              onChange={(e) =>
                setScreenshotFile(e.target.files[0] || null)
              }
            />

            {screenshotFile && (
              <p className="text-sm text-gray-500 mt-2">
                Selected: {screenshotFile.name}
              </p>
            )}
          </div>

          {/* EMAIL */}
          <div>
            <h3 className="font-semibold mb-2">
              Email (optional)
            </h3>

            <input
              type="text"
              placeholder="Sender email"
              value={emailSender}
              onChange={(e) =>
                setEmailSender(e.target.value)
              }
              className="w-full border p-2 rounded mb-2"
            />

            <textarea
              placeholder="Paste email body here..."
              value={emailBody}
              onChange={(e) =>
                setEmailBody(e.target.value)
              }
              rows={4}
              className="w-full border p-2 rounded"
            />
          </div>

          {/* AUDIO */}
          <div>
            <h3 className="font-semibold mb-2">
              Audio (optional)
            </h3>

            <input
              type="file"
              accept=".mp3,.wav,.m4a,.ogg"
              onChange={(e) =>
                setAudioFile(e.target.files[0] || null)
              }
            />

            {audioFile && (
              <p className="text-sm text-gray-500 mt-2">
                Selected: {audioFile.name}
              </p>
            )}
          </div>

          {/* ERROR */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-300 rounded">
              <p className="text-red-600 text-sm">
                {error}
              </p>
            </div>
          )}

          {/* ANALYZE BUTTON */}
          <button
            onClick={handleAnalyzeAll}
            disabled={loading}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading
              ? "Analyzing all evidence..."
              : "Analyze All Evidence"}
          </button>
        </div>

        {/* -----------------------------------------
            COMBINED RESULT
        ----------------------------------------- */}
        {combinedResult && (
          <div className="bg-white p-6 rounded-lg shadow-md">

            {/* RISK SUMMARY */}
            <div
              className={`p-4 rounded border mb-4 ${getRiskColor(
                combinedResult.overall_level
              )}`}
            >
              <h2 className="text-lg font-bold">
                {combinedResult.overall_level}
              </h2>

              <p>
                Combined Risk Score:{" "}
                {combinedResult.combined_score}/100
              </p>

              <p>
                Confidence Level:{" "}
                {combinedResult.confidence}
              </p>
            </div>

            {/* EXPLANATION */}
            <h3 className="font-semibold mb-2">
              Explanation
            </h3>

            <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded mb-4">
              {combinedResult.explanation}
            </p>

            {/* RECOMMENDED ACTIONS */}
            <h3 className="font-semibold mb-2">
              Recommended Actions
            </h3>

            <ul className="list-disc list-inside text-sm text-gray-700 mb-4">
              {combinedResult.recommended_actions?.map(
                (action, i) => (
                  <li key={i}>{action}</li>
                )
              )}
            </ul>

            {/* GENERATE REPORT BUTTON */}
            <button
              onClick={handleGenerateReport}
              disabled={generatingReport}
              className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {generatingReport
                ? "Generating PDF..."
                : "Generate Report"}
            </button>

            {/* -----------------------------------------
                REPORT RESULT
            ----------------------------------------- */}
            {reportResult && (
              <div className="mt-4 p-4 bg-green-50 border border-green-300 rounded">

                <p className="font-semibold">
                  Case ID: {reportResult.case_id}
                </p>

                <p className="text-sm text-gray-600 mb-2">
                  Generated: {reportResult.created_at}
                </p>

                {/* DOWNLOAD LINK */}
                <a
                  href={`http://127.0.0.1:5000${reportResult.download_url}`}
                  className="text-blue-600 hover:underline font-medium"
                  target="_blank"
                  rel="noreferrer"
                >
                  Download PDF Report
                </a>

              </div>
            )}

          </div>
        )}

      </div>
    </div>
  );
}

export default CombinedAnalysis;