function RiskBadge({ level, score, aiVerified }) {
  const styles = {
    "High Risk": {
      bg: "bg-red-50",
      border: "border-red-200",
      text: "text-red-700",
      dot: "bg-red-500",
    },
    "Medium Risk": {
      bg: "bg-amber-50",
      border: "border-amber-200",
      text: "text-amber-700",
      dot: "bg-amber-500",
    },
    "Low Risk": {
      bg: "bg-emerald-50",
      border: "border-emerald-200",
      text: "text-emerald-700",
      dot: "bg-emerald-500",
    },
  };

  const s = styles[level] || styles["Low Risk"];

  return (
    <div className={`rounded-xl border ${s.bg} ${s.border} p-5 flex items-center justify-between`}>
      <div className="flex items-center gap-3">
        <span className={`w-3 h-3 rounded-full ${s.dot}`}></span>
        <div>
          <p className={`font-bold text-lg ${s.text}`}>{level}</p>
          <p className="text-sm text-slate-500">Risk Score: {score}/100</p>
        </div>
      </div>
      {aiVerified && (
        <span className="flex items-center gap-1 text-xs font-medium text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-1 rounded-full">
          ✓ AI Verified
        </span>
      )}
    </div>
  );
}

export default RiskBadge;