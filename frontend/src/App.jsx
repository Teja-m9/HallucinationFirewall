import { useState, useEffect, useRef, useCallback } from "react";

const API = "/api";

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  ICONS                                                                     */
/* ═══════════════════════════════════════════════════════════════════════════ */
const Shield = ({ className = "" }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);
const Search = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);
const Check = () => (
  <svg className="w-5 h-5 text-emerald-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);
const XIcon = () => (
  <svg className="w-5 h-5 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);
const ChevDown = () => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="6 9 12 15 18 9" />
  </svg>
);
const Zap = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
  </svg>
);
const Upload = () => (
  <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="17 8 12 3 7 8" />
    <line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);
const FileText = () => (
  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
  </svg>
);
const Trash = () => (
  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
  </svg>
);

const EXAMPLES = [
  "When was Python released and who created it?",
  "What caused World War I?",
  "Tell me about artificial intelligence history.",
  "How does the human body work?",
  "What is climate change and what causes it?",
  "Tell me about the Renaissance period.",
  "How did the internet develop?",
  "Tell me about quantum physics.",
];

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  SMALL COMPONENTS                                                          */
/* ═══════════════════════════════════════════════════════════════════════════ */
function Metric({ label, value, color = "text-indigo-400" }) {
  return (
    <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-4 text-center backdrop-blur-sm">
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      <p className="text-xs text-slate-400 mt-1 uppercase tracking-wider">{label}</p>
    </div>
  );
}

function ClaimCard({ claim }) {
  const [open, setOpen] = useState(false);
  const ok = claim.is_supported;
  return (
    <div className={`rounded-xl border p-4 transition-all duration-200 ${ok ? "border-emerald-500/30 bg-emerald-950/20" : "border-red-500/30 bg-red-950/20"}`}>
      <div className="flex items-start gap-3 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="mt-0.5">{ok ? <Check /> : <XIcon />}</div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-200 leading-relaxed">{claim.text}</p>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
            <span>Similarity: <strong className={ok ? "text-emerald-400" : "text-red-400"}>{(claim.similarity_score * 100).toFixed(1)}%</strong></span>
            <span className="opacity-40">|</span>
            <span>Entailment: <strong className={claim.entailment_label === "ENTAILED" ? "text-emerald-400" : "text-amber-400"}>{claim.entailment_label}</strong></span>
          </div>
        </div>
        <div className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}><ChevDown /></div>
      </div>
      {open && claim.best_evidence && (
        <div className="mt-3 ml-8 p-3 bg-slate-800/50 rounded-lg border border-slate-700/40 text-xs text-slate-300 leading-relaxed">
          <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1 font-semibold">Best Evidence</p>
          {claim.best_evidence}
        </div>
      )}
    </div>
  );
}

function EvidenceCard({ ev, idx }) {
  return (
    <div className="bg-slate-800/40 border border-slate-700/40 rounded-lg p-3">
      <div className="flex items-center justify-between text-xs text-slate-400 mb-1">
        <span className="font-semibold text-blue-400">#{idx + 1} — {ev.source}</span>
        <span>Score: {(ev.similarity_score * 100).toFixed(1)}%</span>
      </div>
      <p className="text-xs text-slate-300 leading-relaxed">{ev.content}</p>
    </div>
  );
}

function ResponseRenderer({ text }) {
  // Detect comparison responses and render as table
  if (text.startsWith("Comparison between")) {
    return <ComparisonTable text={text} />;
  }
  // Detect list responses (filter results like "Students with % greater than...")
  if (/^\d+\s+students\s+have|^Students with .* found\):/i.test(text) || /^\s*\d+\.\s+/m.test(text)) {
    return <ListResponse text={text} />;
  }
  // Detect detail responses ("Details for X:" or "For X:")
  if (/^(Details for|For )\S/i.test(text)) {
    return <DetailTable text={text} />;
  }
  // Default: plain text with line breaks
  return <p className="text-slate-200 leading-relaxed whitespace-pre-line">{text}</p>;
}

function ComparisonTable({ text }) {
  const lines = text.split("\n").filter(l => l.trim());
  // First line: "Comparison between X and Y:"
  const header = lines[0];
  const nameMatch = header.match(/Comparison between (.+?) and (.+?):/);
  const name1 = nameMatch?.[1] || "Student 1";
  const name2 = nameMatch?.[2] || "Student 2";

  // Parse rows: "  Subject: val1 vs val2 marker"
  const rows = [];
  let summary = [];
  for (let i = 1; i < lines.length; i++) {
    const vsMatch = lines[i].match(/^\s*(.+?):\s*([\d.]+)\s+vs\s+([\d.]+)\s*(.*)/);
    if (vsMatch) {
      const [, subject, v1, v2, marker] = vsMatch;
      rows.push({ subject: subject.trim(), v1: parseFloat(v1), v2: parseFloat(v2), marker: marker.trim() });
    } else if (!lines[i].match(/^Comparison between/)) {
      summary.push(lines[i].trim());
    }
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-xl border border-slate-700/40">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-slate-700/40 text-slate-300">
              <th className="text-left px-4 py-2.5 font-semibold">Subject</th>
              <th className="text-center px-4 py-2.5 font-semibold">{name1}</th>
              <th className="text-center px-4 py-2.5 font-semibold">{name2}</th>
              <th className="text-center px-4 py-2.5 font-semibold">Result</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => {
              const diff = r.v1 - r.v2;
              const cls1 = diff > 0 ? "text-emerald-400 font-semibold" : diff < 0 ? "text-red-400" : "text-slate-300";
              const cls2 = diff < 0 ? "text-emerald-400 font-semibold" : diff > 0 ? "text-red-400" : "text-slate-300";
              const badge = diff > 0
                ? <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">+{diff.toFixed(1)}</span>
                : diff < 0
                ? <span className="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400">{diff.toFixed(1)}</span>
                : <span className="text-xs px-2 py-0.5 rounded-full bg-slate-600/40 text-slate-400">Equal</span>;
              return (
                <tr key={i} className={i % 2 === 0 ? "bg-slate-800/30" : "bg-slate-800/10"}>
                  <td className="px-4 py-2 text-slate-300 font-medium">{r.subject}</td>
                  <td className={`px-4 py-2 text-center ${cls1}`}>{r.v1}</td>
                  <td className={`px-4 py-2 text-center ${cls2}`}>{r.v2}</td>
                  <td className="px-4 py-2 text-center">{badge}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {summary.length > 0 && (
        <div className="bg-slate-700/30 rounded-xl px-4 py-3 text-sm text-slate-300 space-y-1">
          {summary.map((s, i) => <p key={i}>{s}</p>)}
        </div>
      )}
    </div>
  );
}

function ListResponse({ text }) {
  const lines = text.split("\n").filter(l => l.trim());
  const header = lines[0];
  const items = lines.slice(1).filter(l => /^\s*\d+\./.test(l));
  const rest = lines.slice(1).filter(l => !/^\s*\d+\./.test(l));

  return (
    <div className="space-y-3">
      <p className="text-slate-200 font-medium">{header}</p>
      {items.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-700/40">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-slate-700/40 text-slate-300">
                <th className="text-left px-4 py-2.5 font-semibold w-10">#</th>
                <th className="text-left px-4 py-2.5 font-semibold">Name</th>
                <th className="text-right px-4 py-2.5 font-semibold">Value</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => {
                const m = item.match(/^\s*(\d+)\.\s+(.+?)\s*[—–-]\s*([\d.]+)/);
                if (!m) return null;
                return (
                  <tr key={i} className={i % 2 === 0 ? "bg-slate-800/30" : "bg-slate-800/10"}>
                    <td className="px-4 py-2 text-slate-500">{m[1]}</td>
                    <td className="px-4 py-2 text-slate-200">{m[2].trim()}</td>
                    <td className="px-4 py-2 text-right text-indigo-400 font-semibold">{m[3]}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      {rest.map((r, i) => <p key={i} className="text-sm text-slate-400">{r}</p>)}
    </div>
  );
}

function DetailTable({ text }) {
  const lines = text.split("\n").filter(l => l.trim());
  const header = lines[0];
  const items = lines.slice(1).filter(l => l.includes(":"));

  return (
    <div className="space-y-3">
      <p className="text-slate-200 font-medium">{header}</p>
      {items.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-700/40">
          <table className="w-full text-sm">
            <tbody>
              {items.map((item, i) => {
                const m = item.match(/^\s*-?\s*(.+?):\s*(.+)/);
                if (!m) return null;
                return (
                  <tr key={i} className={i % 2 === 0 ? "bg-slate-800/30" : "bg-slate-800/10"}>
                    <td className="px-4 py-2 text-slate-400 font-medium w-1/3">{m[1].trim()}</td>
                    <td className="px-4 py-2 text-slate-200 font-semibold">{m[2].trim()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  TAB: UPLOAD DOCUMENTS                                                     */
/* ═══════════════════════════════════════════════════════════════════════════ */
function UploadTab({ onStatusChange }) {
  const [uploading, setUploading] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState(null);
  const fileInput = useRef(null);

  // Load already-uploaded files on mount
  useEffect(() => {
    fetch(`${API}/status`).then(r => r.json()).then(d => {
      setUploadedFiles(d.uploaded_files.map(f => ({ name: f, status: "done" })));
    }).catch(() => {});
  }, []);

  const uploadFile = async (file) => {
    setError(null);
    const ext = file.name.split(".").pop().toLowerCase();
    if (!["txt", "pdf", "docx", "xlsx", "xls", "csv"].includes(ext)) {
      setError(`Unsupported file: .${ext}. Use .txt, .pdf, .docx, .xlsx, .xls, or .csv`);
      return;
    }

    setUploading(true);
    setUploadedFiles(prev => [...prev, { name: file.name, status: "uploading" }]);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await fetch(`${API}/upload`, { method: "POST", body: form });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Upload failed");
      }
      const data = await res.json();
      setUploadedFiles(prev =>
        prev.map(f => f.name === file.name ? { ...f, status: "done", chunks: data.chunks_added } : f)
      );
      onStatusChange?.();
    } catch (e) {
      setError(e.message);
      setUploadedFiles(prev => prev.filter(f => f.name !== file.name || f.status !== "uploading"));
    }
    setUploading(false);
  };

  const handleFiles = (files) => {
    Array.from(files).forEach(uploadFile);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  };

  const clearAll = async () => {
    if (!confirm("Delete all uploaded files?")) return;
    try {
      await fetch(`${API}/clear-uploads`, { method: "POST" });
      setUploadedFiles([]);
      onStatusChange?.();
    } catch (e) { console.error(e); }
  };

  const deleteFile = async (filename) => {
    if (!confirm(`Delete "${filename}"?`)) return;
    try {
      const res = await fetch(`${API}/delete-file`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename }),
      });
      if (res.ok) {
        setUploadedFiles(prev => prev.filter(f => f.name !== filename));
        onStatusChange?.();
      }
    } catch (e) { console.error(e); }
  };

  const doneFiles = uploadedFiles.filter(f => f.status === "done");

  return (
    <div className="space-y-6">
      {/* Drop zone */}
      <div
        className={`relative border-2 border-dashed rounded-2xl p-10 text-center transition-all cursor-pointer ${dragOver ? "border-indigo-400 bg-indigo-950/20" : "border-slate-600/50 hover:border-slate-500/70 bg-slate-800/30"}`}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInput.current?.click()}
      >
        <input
          ref={fileInput}
          type="file"
          className="hidden"
          accept=".txt,.pdf,.docx,.xlsx,.xls,.csv"
          multiple
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="flex flex-col items-center gap-3">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-colors ${dragOver ? "bg-indigo-600/30 text-indigo-300" : "bg-slate-700/50 text-slate-400"}`}>
            <Upload />
          </div>
          <div>
            <p className="text-base font-semibold text-slate-200">
              {dragOver ? "Drop files here" : "Upload your documents"}
            </p>
            <p className="text-sm text-slate-400 mt-1">
              Drag & drop or click to browse — <span className="text-indigo-400">TXT, PDF, DOCX, Excel, CSV</span>
            </p>
          </div>
          {uploading && (
            <div className="flex items-center gap-2 mt-2">
              <div className="spinner !w-5 !h-5 !border-2" />
              <span className="text-sm text-slate-400">Processing...</span>
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-950/30 border border-red-500/30 rounded-xl p-3 text-sm text-red-300 flex items-center gap-2">
          <XIcon /> {error}
        </div>
      )}

      {/* Uploaded files list */}
      {doneFiles.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
              Uploaded Documents ({doneFiles.length})
            </h3>
            <button onClick={clearAll} className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors">
              <Trash /> Clear all uploads
            </button>
          </div>
          <div className="space-y-2">
            {doneFiles.map((f, i) => (
              <div key={i} className="flex items-center gap-3 bg-slate-800/50 border border-slate-700/40 rounded-xl p-3 group">
                <div className="w-9 h-9 rounded-lg bg-indigo-600/15 flex items-center justify-center text-indigo-400">
                  <FileText />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{f.name}</p>
                  <p className="text-xs text-slate-500">{f.chunks ? `${f.chunks} chunks extracted` : "Processed"}</p>
                </div>
                <div className="w-6 h-6 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <Check />
                </div>
                <button
                  onClick={() => deleteFile(f.name)}
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 hover:text-red-400 hover:bg-red-950/30 opacity-0 group-hover:opacity-100 transition-all"
                  title={`Delete ${f.name}`}
                >
                  <Trash />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Hint */}
      <div className="bg-slate-800/30 border border-slate-700/30 rounded-xl p-4 text-sm text-slate-400 leading-relaxed">
        <p className="font-semibold text-slate-300 mb-1">How it works:</p>
        <ol className="list-decimal list-inside space-y-1">
          <li>Upload any document (TXT, PDF, DOCX, Excel, or CSV)</li>
          <li>The system extracts text and splits it into searchable chunks</li>
          <li>Switch to the <strong className="text-indigo-400">Query</strong> tab and ask questions about your document</li>
          <li>Every claim in the answer is verified against your uploaded content</li>
        </ol>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  TAB: QUERY                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */
function QueryTab({ chunkCount }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [showEvidence, setShowEvidence] = useState(false);

  const run = async (q) => {
    const text = q || query;
    if (!text.trim()) return;
    setQuery(text);
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: text }),
      });
      setResult(await res.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* No docs warning */}
      {chunkCount === 0 && (
        <div className="bg-amber-950/30 border border-amber-500/30 rounded-xl p-4 text-sm text-amber-300 text-center">
          No documents loaded. Go to <strong>Upload</strong> tab to add documents first.
        </div>
      )}

      {/* Search bar */}
      <div className="relative">
        <input
          type="text"
          className="w-full bg-slate-800/70 border border-slate-600/50 rounded-2xl py-4 pl-5 pr-28 text-base text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500/50 transition-all"
          placeholder="Ask anything about your documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run()}
        />
        <button
          onClick={() => run()}
          disabled={loading || chunkCount === 0}
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-2.5 px-5 rounded-xl flex items-center gap-2 transition-all text-sm"
        >
          {loading ? <div className="spinner !w-5 !h-5 !border-2" /> : <><Search /> Ask</>}
        </button>
      </div>

      {/* Example chips */}
      <div className="flex flex-wrap gap-2">
        {EXAMPLES.slice(0, 5).map((ex) => (
          <button
            key={ex}
            onClick={() => run(ex)}
            disabled={chunkCount === 0}
            className="text-xs bg-slate-800/60 hover:bg-slate-700/60 disabled:opacity-40 border border-slate-700/40 text-slate-300 hover:text-white py-1.5 px-3 rounded-full transition-all"
          >
            {ex.length > 40 ? ex.slice(0, 38) + "..." : ex}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex flex-col items-center py-16 gap-4">
          <div className="spinner" />
          <p className="text-slate-400 text-sm animate-pulse">Running VDHF pipeline...</p>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="space-y-6 animate-[fadeIn_.3s_ease]">
          {/* Status banner */}
          <div className={`rounded-2xl p-5 flex items-center justify-between ${result.is_verified ? "bg-gradient-to-r from-emerald-900/40 to-emerald-800/20 border border-emerald-500/30" : result.supported_claims === 0 ? "bg-gradient-to-r from-red-900/40 to-red-800/20 border border-red-500/30" : "bg-gradient-to-r from-amber-900/40 to-amber-800/20 border border-amber-500/30"}`}>
            <div className="flex items-center gap-3">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${result.is_verified ? "bg-emerald-500/20" : result.supported_claims === 0 ? "bg-red-500/20" : "bg-amber-500/20"}`}>
                {result.is_verified ? "✅" : result.supported_claims === 0 ? "❌" : "⚠️"}
              </div>
              <div>
                <p className="font-bold text-lg">{result.is_verified ? "Verified Response" : result.supported_claims === 0 ? "Hallucinated Response" : "Partially Verified"}</p>
                <p className="text-sm text-slate-400">{result.supported_claims}/{result.total_claims} claims supported</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-2xl font-extrabold tabular-nums" style={{ color: result.is_verified ? "#22c55e" : result.supported_claims === 0 ? "#ef4444" : "#f59e0b" }}>
                {(result.support_ratio * 100).toFixed(0)}%
              </p>
              <p className="text-[10px] uppercase tracking-widest text-slate-500">support ratio</p>
            </div>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Metric label="Support Ratio" value={`${(result.support_ratio * 100).toFixed(0)}%`} color={result.is_verified ? "text-emerald-400" : result.supported_claims === 0 ? "text-red-400" : "text-amber-400"} />
            <Metric label="Total Claims" value={result.total_claims} />
            <Metric label="Supported" value={result.supported_claims} color="text-emerald-400" />
            <Metric label="Regenerations" value={result.regeneration_attempts} color="text-blue-400" />
          </div>

          {/* Response */}
          <div className="bg-slate-800/50 border border-slate-700/40 rounded-2xl p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400">Response</h3>
              <span className="text-xs text-slate-500">{result.elapsed_seconds}s</span>
            </div>
            <ResponseRenderer text={result.response} />
          </div>

          {/* Progress bar */}
          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1">
              <span>Verification Progress</span>
              <span>{result.supported_claims}/{result.total_claims}</span>
            </div>
            <div className="h-2.5 bg-slate-800 rounded-full overflow-hidden">
              <div className="bar-fill h-full rounded-full" style={{ width: `${result.support_ratio * 100}%`, background: result.is_verified ? "linear-gradient(90deg,#22c55e,#4ade80)" : result.supported_claims === 0 ? "linear-gradient(90deg,#ef4444,#f87171)" : "linear-gradient(90deg,#f59e0b,#fbbf24)" }} />
            </div>
          </div>

          {/* Claims */}
          {result.claims.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">Claims Breakdown</h3>
              <div className="space-y-2">
                {result.claims.map((c, i) => <ClaimCard key={i} claim={c} />)}
              </div>
            </div>
          )}

          {/* Evidence */}
          {result.evidence.length > 0 && (
            <div>
              <button onClick={() => setShowEvidence(!showEvidence)} className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wider text-slate-400 hover:text-slate-200 transition-colors mb-3">
                <span>Retrieved Evidence ({result.evidence.length})</span>
                <div className={`transition-transform duration-200 ${showEvidence ? "rotate-180" : ""}`}><ChevDown /></div>
              </button>
              {showEvidence && (
                <div className="space-y-2">
                  {result.evidence.map((ev, i) => <EvidenceCard key={i} ev={ev} idx={i} />)}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  TAB: VERIFY CLAIMS                                                        */
/* ═══════════════════════════════════════════════════════════════════════════ */
function VerifyTab() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const verify = async () => {
    const lines = text.split("\n").map((l) => l.trim()).filter(Boolean);
    if (!lines.length) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claims: lines }),
      });
      setResult(await res.json());
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <label className="block text-sm text-slate-400 mb-2">Enter claims to verify (one per line):</label>
        <textarea
          rows={6}
          className="w-full bg-slate-800/70 border border-slate-600/50 rounded-xl p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all resize-none"
          placeholder={"Python was created by Guido van Rossum.\nPython was released in 2005.\nPython is a compiled language."}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </div>
      <button onClick={verify} disabled={loading} className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 px-6 rounded-xl flex items-center gap-2 transition-all">
        {loading ? <div className="spinner !w-5 !h-5 !border-2" /> : <><Zap /> Verify Claims</>}
      </button>

      {result && (
        <div className="space-y-4 animate-[fadeIn_.3s_ease]">
          <div className="flex items-center gap-4">
            <p className="text-lg font-bold">{result.supported}/{result.total} supported <span className="text-slate-500 font-normal">({(result.ratio * 100).toFixed(0)}%)</span></p>
            <div className="flex-1 h-2.5 bg-slate-800 rounded-full overflow-hidden">
              <div className="bar-fill h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500" style={{ width: `${result.ratio * 100}%` }} />
            </div>
          </div>
          <div className="space-y-2">
            {result.results.map((c, i) => <ClaimCard key={i} claim={c} />)}
          </div>
        </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  TAB: ABOUT                                                                */
/* ═══════════════════════════════════════════════════════════════════════════ */
function AboutTab() {
  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h3 className="text-xl font-bold text-slate-100 mb-3">How VDHF Works</h3>
        <p className="text-slate-400 leading-relaxed text-sm">
          The Verification-Driven Hallucination Firewall is a post-generation system that detects and blocks
          hallucinated content in LLM responses by verifying every factual claim against a trusted knowledge base.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { n: "1", title: "Retrieve", desc: "Sentence-BERT embeds your query and finds the top-K most relevant document chunks via ChromaDB." },
          { n: "2", title: "Generate", desc: "An LLM (Groq / mock) generates a response grounded in the retrieved evidence context." },
          { n: "3", title: "Extract", desc: "Rule-based decomposition splits the response into atomic, independently verifiable factual claims." },
          { n: "4", title: "Verify", desc: "Each claim is scored for semantic similarity and checked for NLI entailment against evidence." },
          { n: "5", title: "Firewall", desc: "If SupportRatio >= threshold (80%), the response passes. Otherwise, regeneration is triggered." },
          { n: "6", title: "Regenerate", desc: "A refined prompt using only verified evidence is created, and the LLM produces a safer response." },
        ].map((s) => (
          <div key={s.n} className="bg-slate-800/50 border border-slate-700/40 rounded-xl p-4">
            <div className="w-8 h-8 rounded-lg bg-indigo-600/20 flex items-center justify-center text-indigo-400 font-bold text-sm mb-3">{s.n}</div>
            <p className="font-semibold text-slate-200 text-sm mb-1">{s.title}</p>
            <p className="text-xs text-slate-400 leading-relaxed">{s.desc}</p>
          </div>
        ))}
      </div>

      <div>
        <h3 className="text-lg font-bold text-slate-100 mb-3">Models & Config</h3>
        <div className="overflow-hidden rounded-xl border border-slate-700/40">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/60"><tr>
              <th className="text-left p-3 text-slate-400 font-medium">Parameter</th>
              <th className="text-left p-3 text-slate-400 font-medium">Value</th>
            </tr></thead>
            <tbody className="divide-y divide-slate-700/30">
              {[
                ["Embedding Model", "all-MiniLM-L6-v2 (Sentence-BERT)"],
                ["NLI Model", "microsoft/deberta-base-mnli"],
                ["LLM", "llama-3.3-70b-versatile (Groq)"],
                ["Similarity Threshold", "0.75"],
                ["Firewall Threshold", "0.80"],
                ["Top-K Retrieval", "7"],
                ["Max Regenerations", "2"],
              ].map(([k, v]) => (
                <tr key={k} className="hover:bg-slate-800/30 transition-colors">
                  <td className="p-3 text-slate-300">{k}</td>
                  <td className="p-3 text-indigo-300 font-mono text-xs">{v}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */
/*  MAIN APP                                                                  */
/* ═══════════════════════════════════════════════════════════════════════════ */
export default function App() {
  const [tab, setTab] = useState("upload");
  const [status, setStatus] = useState(null);

  const refreshStatus = useCallback(() => {
    fetch(`${API}/status`).then((r) => r.json()).then(setStatus).catch(() => {});
  }, []);

  useEffect(() => { refreshStatus(); }, [refreshStatus]);

  const chunkCount = status?.document_chunks ?? 0;
  const totalDocs = (status?.documents_loaded?.length ?? 0) + (status?.uploaded_files?.length ?? 0);

  const tabs = [
    { id: "upload", label: "Upload", icon: "📁" },
    { id: "query", label: "Query", icon: "🔍" },
    { id: "verify", label: "Verify Claims", icon: "🧪" },
    { id: "about", label: "About", icon: "📖" },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* ── Hero Header ─── */}
      <header className="hero-gradient relative overflow-hidden border-b border-slate-700/40">
        <div className="particle w-32 h-32 top-8 left-[10%]" style={{ animationDelay: "0s" }} />
        <div className="particle w-20 h-20 top-20 right-[15%]" style={{ animationDelay: "2s" }} />
        <div className="particle w-16 h-16 bottom-4 left-[40%]" style={{ animationDelay: "4s" }} />

        <div className="relative max-w-5xl mx-auto px-6 py-12 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 pulse-ring mb-5">
            <Shield className="w-8 h-8 text-indigo-400" />
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
            Hallucination Firewall
          </h1>
          <p className="text-slate-400 mt-3 text-base md:text-lg max-w-xl mx-auto">
            Upload any document, ask questions, and get verified answers — every claim checked against your content.
          </p>
          {status && (
            <div className="mt-5 flex items-center justify-center gap-3 flex-wrap">
              <div className="inline-flex items-center gap-2 bg-slate-800/60 border border-slate-700/50 rounded-full py-1.5 px-4 text-xs text-slate-400">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                {chunkCount} chunks from {totalDocs} documents
              </div>
              {status.uploaded_files?.length > 0 && (
                <div className="inline-flex items-center gap-2 bg-indigo-950/40 border border-indigo-500/30 rounded-full py-1.5 px-4 text-xs text-indigo-300">
                  <FileText /> {status.uploaded_files.length} uploaded
                </div>
              )}
            </div>
          )}
        </div>
      </header>

      {/* ── Tabs ─── */}
      <nav className="border-b border-slate-700/40 bg-slate-900/60 backdrop-blur-sm sticky top-0 z-20">
        <div className="max-w-5xl mx-auto px-6 flex gap-1">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`py-3.5 px-5 text-sm font-medium transition-all border-b-2 ${tab === t.id ? "border-indigo-500 text-indigo-300" : "border-transparent text-slate-400 hover:text-slate-200"}`}
            >
              <span className="mr-1.5">{t.icon}</span>{t.label}
            </button>
          ))}
        </div>
      </nav>

      {/* ── Content ─── */}
      <main className="flex-1 max-w-5xl mx-auto px-6 py-8 w-full">
        {tab === "upload" && <UploadTab onStatusChange={refreshStatus} />}
        {tab === "query" && <QueryTab chunkCount={chunkCount} />}
        {tab === "verify" && <VerifyTab />}
        {tab === "about" && <AboutTab />}
      </main>

      {/* ── Footer ─── */}
      <footer className="border-t border-slate-700/40 py-4 text-center text-xs text-slate-500">
        VDHF — Verification-Driven Hallucination Firewall &middot; Built with React + FastAPI
      </footer>
    </div>
  );
}
