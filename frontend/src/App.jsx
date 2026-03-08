import { useState, useEffect, useRef } from "react";

const API = "https://ai-testing-agent-production.up.railway.app";

const FONTS = `
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@300;400;600;700;900&display=swap');
`;

const CSS = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #050810;
    --bg2:      #090d1a;
    --bg3:      #0d1225;
    --border:   #1a2440;
    --green:    #00ff88;
    --cyan:     #00cfff;
    --red:      #ff3b6b;
    --yellow:   #ffc42b;
    --dim:      #3a4a6b;
    --text:     #c8d8f0;
    --textdim:  #5a7090;
    --mono:     'Share Tech Mono', monospace;
    --sans:     'Exo 2', sans-serif;
  }

  body { background: var(--bg); color: var(--text); font-family: var(--sans); }

  ::-webkit-scrollbar { width: 4px; }
  ::-webkit-scrollbar-track { background: var(--bg2); }
  ::-webkit-scrollbar-thumb { background: var(--dim); border-radius: 2px; }

  @keyframes scanline {
    0%   { transform: translateY(-100%); }
    100% { transform: translateY(100vh); }
  }
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
  }
  @keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes glowPulse {
    0%, 100% { box-shadow: 0 0 8px rgba(0,255,136,0.3); }
    50%       { box-shadow: 0 0 20px rgba(0,255,136,0.7); }
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
  }
`;

const priorityColor  = { high: "var(--red)",    medium: "var(--yellow)", low: "var(--green)"  };
const categoryColor = { happy_path: "var(--green)", edge_case: "var(--cyan)", validation: "var(--yellow)", validation_errors: "var(--yellow)", auth: "var(--red)", auth_errors: "var(--red)", error_handling: "var(--dim)" };
const categoryLabel = { happy_path: "HAPPY", edge_case: "EDGE", validation: "VALID", validation_errors: "VALID", auth: "AUTH", auth_errors: "AUTH", error_handling: "ERR" };
const methodColor    = { GET: "var(--green)", POST: "var(--cyan)", PUT: "var(--yellow)", DELETE: "var(--red)", PATCH: "var(--yellow)" };

function GlowDot({ color }) {
  return (
    <span style={{
      display: "inline-block", width: 7, height: 7,
      borderRadius: "50%", background: color,
      boxShadow: `0 0 6px ${color}`, flexShrink: 0
    }} />
  );
}

function Spinner() {
  return (
    <span style={{
      display: "inline-block", width: 14, height: 14,
      border: "2px solid var(--dim)",
      borderTopColor: "var(--green)",
      borderRadius: "50%",
      animation: "spin 0.7s linear infinite"
    }} />
  );
}

function Tag({ label, color }) {
  return (
    <span style={{
      fontFamily: "var(--mono)", fontSize: 10, letterSpacing: 1,
      padding: "2px 7px", border: `1px solid ${color}`,
      color, borderRadius: 3, flexShrink: 0
    }}>{label}</span>
  );
}

function Panel({ title, accent = "var(--cyan)", children, style = {} }) {
  return (
    <div style={{
      background: "var(--bg2)", border: "1px solid var(--border)",
      borderRadius: 8, overflow: "hidden",
      boxShadow: "0 4px 32px rgba(0,0,0,0.5)", ...style
    }}>
      <div style={{
        padding: "10px 18px", borderBottom: "1px solid var(--border)",
        display: "flex", alignItems: "center", gap: 10,
        background: "var(--bg3)"
      }}>
        <div style={{ width: 3, height: 14, background: accent, borderRadius: 2, boxShadow: `0 0 6px ${accent}` }} />
        <span style={{ fontFamily: "var(--mono)", fontSize: 11, letterSpacing: 2, color: accent, textTransform: "uppercase" }}>{title}</span>
      </div>
      <div style={{ padding: 18 }}>{children}</div>
    </div>
  );
}

function TestCaseCard({ tc, index }) {
  const [open, setOpen] = useState(false);
  const pc = priorityColor[tc.priority] || "var(--dim)";
  const cc = categoryColor[tc.category] || "var(--dim)";
  const cl = categoryLabel[tc.category] || "??";

  return (
    <div style={{
      background: "var(--bg3)", border: "1px solid var(--border)",
      borderRadius: 6, overflow: "hidden", marginBottom: 8,
      animation: `fadeSlideIn 0.3s ease both`,
      animationDelay: `${index * 0.06}s`
    }}>
      <div onClick={() => setOpen(!open)} style={{
        padding: "10px 14px", display: "flex", alignItems: "center",
        gap: 10, cursor: "pointer",
        transition: "background 0.15s",
      }}
        onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.03)"}
        onMouseLeave={e => e.currentTarget.style.background = "transparent"}
      >
        <span style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", width: 48, flexShrink: 0 }}>{tc.id}</span>
        <GlowDot color={pc} />
        <Tag label={cl} color={cc} />
        <span style={{ flex: 1, fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{tc.name}</span>
        <span style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)" }}>
          {tc.expected?.status_code}
        </span>
        <span style={{ color: "var(--dim)", fontSize: 12, transform: open ? "rotate(90deg)" : "none", transition: "transform 0.2s" }}>▶</span>
      </div>

      {open && (
        <div style={{ borderTop: "1px solid var(--border)", padding: "12px 14px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", marginBottom: 6, letterSpacing: 1 }}>INPUT</div>
            <pre style={{
              fontFamily: "var(--mono)", fontSize: 11, color: "var(--cyan)",
              background: "var(--bg)", padding: 10, borderRadius: 4,
              overflow: "auto", maxHeight: 120, lineHeight: 1.5
            }}>{JSON.stringify(tc.input, null, 2)}</pre>
          </div>
          <div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", marginBottom: 6, letterSpacing: 1 }}>EXPECTED</div>
            <pre style={{
              fontFamily: "var(--mono)", fontSize: 11, color: "var(--green)",
              background: "var(--bg)", padding: 10, borderRadius: 4,
              overflow: "auto", maxHeight: 120, lineHeight: 1.5
            }}>{JSON.stringify(tc.expected, null, 2)}</pre>
          </div>
          <div style={{ gridColumn: "span 2" }}>
            <div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", marginBottom: 4, letterSpacing: 1 }}>DESCRIPTION</div>
            <div style={{ fontSize: 12, color: "var(--text)", lineHeight: 1.6 }}>{tc.description}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function HistoryRow({ item, index }) {
  const isOk = item.status === "success";
  return (
    <div style={{
      display: "grid", gridTemplateColumns: "1fr 80px 140px",
      gap: 12, padding: "10px 14px",
      borderBottom: "1px solid var(--border)",
      fontSize: 12, animation: `fadeSlideIn 0.3s ease both`,
      animationDelay: `${index * 0.04}s`,
      transition: "background 0.15s"
    }}
      onMouseEnter={e => e.currentTarget.style.background = "rgba(255,255,255,0.02)"}
      onMouseLeave={e => e.currentTarget.style.background = "transparent"}
    >
      <span style={{ fontFamily: "var(--mono)", fontSize: 11, color: "var(--textdim)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
        {item.test_name}
      </span>
      <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <GlowDot color={isOk ? "var(--green)" : "var(--red)"} />
        <span style={{ fontFamily: "var(--mono)", fontSize: 10, color: isOk ? "var(--green)" : "var(--red)" }}>
          {isOk ? "PASS" : "FAIL"}
        </span>
      </span>
      <span style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", textAlign: "right" }}>
        {new Date(item.ran_at).toLocaleTimeString()}
      </span>
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState("generate");
  const [desc, setDesc] = useState("");
  const [method, setMethod] = useState("POST");
  const [numCases, setNumCases] = useState(5);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [testCases, setTestCases] = useState([]);
  const [playwrightResult, setPlaywrightResult] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");
  const [log, setLog] = useState([]);
  const [stats, setStats] = useState({ total: 0, pass: 0, fail: 0 });
  const logRef = useRef(null);

  const addLog = (msg, color = "var(--text)") => {
    const ts = new Date().toLocaleTimeString("en-US", { hour12: false });
    setLog(l => [...l.slice(-60), { msg, color, ts }]);
  };

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [log]);

  const fetchHistory = async () => {
    try {
      const r = await fetch(`${API}/history?limit=30`);
      const d = await r.json();
      setHistory(d.history || []);
      const pass = (d.history || []).filter(h => h.status === "success").length;
      setStats({ total: d.total || 0, pass, fail: (d.total || 0) - pass });
    } catch {}
  };

  useEffect(() => {
    addLog("SYSTEM ONLINE — AI Testing Agent v2.0", "var(--green)");
    addLog("Connecting to backend...", "var(--cyan)");
    fetch(`${API}/`).then(() => {
      addLog("Backend connection established ✓", "var(--green)");
      fetchHistory();
    }).catch(() => addLog("Backend offline — start uvicorn server", "var(--red)"));
  }, []);

  const handleGenerate = async () => {
    if (!desc.trim()) return setError("Enter an endpoint description");
    setError(""); setLoading(true); setTestCases([]); setPlaywrightResult(null);
    addLog(`Generating ${numCases} test cases via Groq AI...`, "var(--cyan)");

    try {
      const endpoint = url.trim() ? "/generate-and-run" : "/generate-tests";
      const body = url.trim()
        ? { endpoint_description: desc, method, num_cases: numCases, url }
        : { endpoint_description: desc, method, num_cases: numCases };

      addLog(`POST ${endpoint}`, "var(--textdim)");
      const r = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const d = await r.json();

      if (!r.ok) throw new Error(d.detail || "API error");

      const cases = d.test_cases || d.report?.ai_generated_cases || [];
      setTestCases(cases);
      if (d.report?.playwright_result) setPlaywrightResult(d.report.playwright_result);

      addLog(`Generated ${cases.length} test cases ✓`, "var(--green)");
      if (d.report) addLog(`Playwright: ${d.report.overall_status?.toUpperCase()}`, d.report.overall_status === "success" ? "var(--green)" : "var(--red)");
      await fetchHistory();
      setTab("results");
    } catch (e) {
      setError(e.message);
      addLog(`ERROR: ${e.message}`, "var(--red)");
    } finally {
      setLoading(false);
    }
  };

  const tabs = ["generate", "results", "history", "console"];

  return (
    <>
      <style>{FONTS + CSS}</style>

      {/* Scanline overlay */}
      <div style={{
        position: "fixed", inset: 0, pointerEvents: "none", zIndex: 999,
        background: "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.03) 2px, rgba(0,0,0,0.03) 4px)"
      }} />

      <div style={{ minHeight: "100vh", padding: "0 0 40px" }}>

        {/* ── HEADER ─────────────────────────────── */}
        <header style={{
          borderBottom: "1px solid var(--border)",
          background: "linear-gradient(180deg, var(--bg3) 0%, var(--bg) 100%)",
          padding: "16px 32px", display: "flex", alignItems: "center",
          justifyContent: "space-between", position: "sticky", top: 0, zIndex: 100,
          backdropFilter: "blur(10px)"
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 8,
              background: "linear-gradient(135deg, var(--green), var(--cyan))",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 18, boxShadow: "0 0 16px rgba(0,255,136,0.4)"
            }}>⬡</div>
            <div>
              <div style={{ fontFamily: "var(--sans)", fontWeight: 900, fontSize: 17, letterSpacing: 1, color: "#fff" }}>
                AI TESTING AGENT
              </div>
              <div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", letterSpacing: 2 }}>
                MISSION CONTROL v2.0
              </div>
            </div>
          </div>

          {/* Stats bar */}
          <div style={{ display: "flex", gap: 24, alignItems: "center" }}>
            {[
              { label: "TOTAL RUNS", value: stats.total, color: "var(--cyan)" },
              { label: "PASSED",     value: stats.pass,  color: "var(--green)" },
              { label: "FAILED",     value: stats.fail,  color: "var(--red)" },
            ].map(s => (
              <div key={s.label} style={{ textAlign: "center" }}>
                <div style={{ fontFamily: "var(--mono)", fontSize: 20, fontWeight: 700, color: s.color, lineHeight: 1 }}>{s.value}</div>
                <div style={{ fontFamily: "var(--mono)", fontSize: 9, color: "var(--textdim)", letterSpacing: 1.5, marginTop: 2 }}>{s.label}</div>
              </div>
            ))}
            <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 14px", border: "1px solid var(--green)", borderRadius: 20 }}>
              <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--green)", animation: "pulse 2s ease infinite" }} />
              <span style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--green)", letterSpacing: 1 }}>LIVE</span>
            </div>
          </div>
        </header>

        {/* ── NAV TABS ────────────────────────────── */}
        <div style={{
          display: "flex", gap: 0, padding: "0 32px",
          borderBottom: "1px solid var(--border)",
          background: "var(--bg2)"
        }}>
          {tabs.map(t => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: "12px 22px", background: "none", border: "none",
              fontFamily: "var(--mono)", fontSize: 11, letterSpacing: 2,
              textTransform: "uppercase", cursor: "pointer",
              color: tab === t ? "var(--green)" : "var(--textdim)",
              borderBottom: tab === t ? "2px solid var(--green)" : "2px solid transparent",
              transition: "all 0.15s",
              marginBottom: -1
            }}
              onMouseEnter={e => { if (tab !== t) e.target.style.color = "var(--text)" }}
              onMouseLeave={e => { if (tab !== t) e.target.style.color = "var(--textdim)" }}
            >{t}</button>
          ))}
        </div>

        <div style={{ padding: "28px 32px", maxWidth: 1200, margin: "0 auto" }}>

          {/* ═══════════════════════════════════════
              TAB: GENERATE
          ═══════════════════════════════════════ */}
          {tab === "generate" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 24 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

                <Panel title="Configure Test Generation" accent="var(--green)">
                  {/* Description */}
                  <div style={{ marginBottom: 18 }}>
                    <label style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", letterSpacing: 2, display: "block", marginBottom: 8 }}>
                      ENDPOINT DESCRIPTION *
                    </label>
                    <textarea
                      value={desc}
                      onChange={e => setDesc(e.target.value)}
                      placeholder="e.g. POST /api/login — accepts email and password, returns JWT token on success (200), 401 for wrong credentials..."
                      rows={4}
                      style={{
                        width: "100%", background: "var(--bg)", border: "1px solid var(--border)",
                        borderRadius: 6, padding: "12px 14px", color: "var(--text)",
                        fontFamily: "var(--mono)", fontSize: 12, lineHeight: 1.6, resize: "vertical",
                        outline: "none", transition: "border-color 0.2s"
                      }}
                      onFocus={e => e.target.style.borderColor = "var(--green)"}
                      onBlur={e => e.target.style.borderColor = "var(--border)"}
                    />
                  </div>

                  {/* Method + Cases row */}
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 18 }}>
                    <div>
                      <label style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", letterSpacing: 2, display: "block", marginBottom: 8 }}>HTTP METHOD</label>
                      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                        {["GET", "POST", "PUT", "DELETE", "PATCH"].map(m => (
                          <button key={m} onClick={() => setMethod(m)} style={{
                            padding: "6px 12px", borderRadius: 4, cursor: "pointer",
                            fontFamily: "var(--mono)", fontSize: 11, letterSpacing: 1,
                            border: `1px solid ${method === m ? methodColor[m] : "var(--border)"}`,
                            background: method === m ? `${methodColor[m]}18` : "var(--bg)",
                            color: method === m ? methodColor[m] : "var(--textdim)",
                            transition: "all 0.15s"
                          }}>{m}</button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <label style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", letterSpacing: 2, display: "block", marginBottom: 8 }}>NUMBER OF CASES: <span style={{ color: "var(--cyan)" }}>{numCases}</span></label>
                      <input type="range" min={1} max={10} value={numCases} onChange={e => setNumCases(+e.target.value)}
                        style={{ width: "100%", accentColor: "var(--green)" }} />
                      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "var(--mono)", fontSize: 9, color: "var(--textdim)", marginTop: 4 }}>
                        <span>1</span><span>5</span><span>10</span>
                      </div>
                    </div>
                  </div>

                  {/* URL (optional) */}
                  <div style={{ marginBottom: 20 }}>
                    <label style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", letterSpacing: 2, display: "block", marginBottom: 8 }}>
                      TARGET URL <span style={{ color: "var(--dim)" }}>(OPTIONAL — RUNS PLAYWRIGHT IF PROVIDED)</span>
                    </label>
                    <input
                      value={url}
                      onChange={e => setUrl(e.target.value)}
                      placeholder="https://your-api.com/login"
                      style={{
                        width: "100%", background: "var(--bg)", border: "1px solid var(--border)",
                        borderRadius: 6, padding: "10px 14px", color: "var(--text)",
                        fontFamily: "var(--mono)", fontSize: 12, outline: "none", transition: "border-color 0.2s"
                      }}
                      onFocus={e => e.target.style.borderColor = "var(--cyan)"}
                      onBlur={e => e.target.style.borderColor = "var(--border)"}
                    />
                  </div>

                  {error && (
                    <div style={{
                      padding: "10px 14px", marginBottom: 16, borderRadius: 6,
                      border: "1px solid var(--red)", background: "rgba(255,59,107,0.08)",
                      fontFamily: "var(--mono)", fontSize: 11, color: "var(--red)"
                    }}>⚠ {error}</div>
                  )}

                  {/* Generate button */}
                  <button onClick={handleGenerate} disabled={loading} style={{
                    width: "100%", padding: "14px", borderRadius: 6, cursor: loading ? "not-allowed" : "pointer",
                    background: loading ? "var(--bg3)" : "linear-gradient(135deg, rgba(0,255,136,0.15), rgba(0,207,255,0.1))",
                    border: `1px solid ${loading ? "var(--dim)" : "var(--green)"}`,
                    color: loading ? "var(--dim)" : "var(--green)",
                    fontFamily: "var(--mono)", fontSize: 13, letterSpacing: 3,
                    textTransform: "uppercase", display: "flex", alignItems: "center",
                    justifyContent: "center", gap: 10, transition: "all 0.2s",
                    boxShadow: loading ? "none" : "0 0 20px rgba(0,255,136,0.15)"
                  }}>
                    {loading ? <><Spinner /> GENERATING...</> : "⬡ GENERATE TEST CASES"}
                  </button>
                </Panel>

                {/* Quick templates */}
                <Panel title="Quick Templates" accent="var(--dim)">
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    {[
                      { label: "Login Endpoint",   method: "POST",   desc: "POST /api/login — accepts email and password in JSON body. Returns JWT token (200), 401 for wrong credentials, 422 for missing fields." },
                      { label: "Get User Profile",  method: "GET",    desc: "GET /api/users/{id} — returns user profile by ID. Requires Bearer token. Returns 200 with user object, 404 if not found, 401 if unauthorized." },
                      { label: "Create Resource",   method: "POST",   desc: "POST /api/products — creates a new product with name, price, category. Admin only. Returns 201 with created object, 400 for validation errors." },
                      { label: "Delete Resource",   method: "DELETE", desc: "DELETE /api/users/{id} — admin-only endpoint to delete user by ID. Returns 204 on success, 404 if not found, 403 if not admin." },
                    ].map(t => (
                      <button key={t.label} onClick={() => { setDesc(t.desc); setMethod(t.method); }} style={{
                        padding: "10px 12px", background: "var(--bg3)", border: "1px solid var(--border)",
                        borderRadius: 6, cursor: "pointer", textAlign: "left", transition: "all 0.15s"
                      }}
                        onMouseEnter={e => { e.currentTarget.style.borderColor = "var(--cyan)"; e.currentTarget.style.background = "rgba(0,207,255,0.05)"; }}
                        onMouseLeave={e => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.background = "var(--bg3)"; }}
                      >
                        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                          <Tag label={t.method} color={methodColor[t.method]} />
                          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text)" }}>{t.label}</span>
                        </div>
                        <div style={{ fontSize: 11, color: "var(--textdim)", lineHeight: 1.4, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical" }}>
                          {t.desc}
                        </div>
                      </button>
                    ))}
                  </div>
                </Panel>
              </div>

              {/* Right: Console log */}
              <Panel title="System Console" accent="var(--dim)" style={{ height: "fit-content" }}>
                <div ref={logRef} style={{ height: 420, overflowY: "auto", fontFamily: "var(--mono)", fontSize: 11, lineHeight: 1.8 }}>
                  {log.map((l, i) => (
                    <div key={i} style={{ display: "flex", gap: 10 }}>
                      <span style={{ color: "var(--dim)", flexShrink: 0 }}>{l.ts}</span>
                      <span style={{ color: l.color }}>{l.msg}</span>
                    </div>
                  ))}
                  <div style={{ display: "inline-block", width: 8, height: 14, background: "var(--green)", animation: "blink 1s step-end infinite", marginLeft: 2, verticalAlign: "text-bottom" }} />
                </div>
              </Panel>
            </div>
          )}

          {/* ═══════════════════════════════════════
              TAB: RESULTS
          ═══════════════════════════════════════ */}
          {tab === "results" && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 24 }}>
              <Panel title={`Test Cases — ${testCases.length} Generated`} accent="var(--cyan)">
                {testCases.length === 0 ? (
                  <div style={{ textAlign: "center", padding: "48px 0", color: "var(--textdim)", fontFamily: "var(--mono)", fontSize: 12 }}>
                    No test cases yet — go to GENERATE tab
                  </div>
                ) : (
                  testCases.map((tc, i) => <TestCaseCard key={tc.id} tc={tc} index={i} />)
                )}
              </Panel>

              <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                {/* Category breakdown */}
                {testCases.length > 0 && (
                  <Panel title="Coverage Breakdown" accent="var(--yellow)">
                    {Object.entries(
                      testCases.reduce((acc, tc) => { acc[tc.category] = (acc[tc.category] || 0) + 1; return acc; }, {})
                    ).map(([cat, count]) => (
                      <div key={cat} style={{ marginBottom: 10 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                          <Tag label={categoryLabel[cat] || cat} color={categoryColor[cat] || "var(--dim)"} />
                          <span style={{ fontFamily: "var(--mono)", fontSize: 11, color: "var(--textdim)" }}>{count}/{testCases.length}</span>
                        </div>
                        <div style={{ height: 4, background: "var(--bg)", borderRadius: 2, overflow: "hidden" }}>
                          <div style={{
                            height: "100%", borderRadius: 2,
                            background: categoryColor[cat] || "var(--dim)",
                            width: `${(count / testCases.length) * 100}%`,
                            transition: "width 0.6s ease",
                            boxShadow: `0 0 6px ${categoryColor[cat] || "var(--dim)"}`
                          }} />
                        </div>
                      </div>
                    ))}
                  </Panel>
                )}

                {/* Playwright result */}
                {playwrightResult && (
                  <Panel title="Playwright Result" accent={playwrightResult.status === "success" ? "var(--green)" : "var(--red)"}>
                    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                      {[
                        { label: "STATUS",   value: playwrightResult.status?.toUpperCase(), color: playwrightResult.status === "success" ? "var(--green)" : "var(--red)" },
                        { label: "TITLE",    value: playwrightResult.title || "—",         color: "var(--cyan)" },
                        { label: "LINKS",    value: playwrightResult.checks?.links_found,  color: "var(--text)" },
                        { label: "BUTTONS",  value: playwrightResult.checks?.buttons_found, color: "var(--text)" },
                        { label: "IMAGES",   value: playwrightResult.checks?.images_found, color: "var(--text)" },
                        { label: "LOAD MS",  value: playwrightResult.checks?.performance_ms?.loadComplete, color: "var(--yellow)" },
                      ].map(row => (
                        <div key={row.label} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                          <span style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--textdim)", letterSpacing: 1 }}>{row.label}</span>
                          <span style={{ fontFamily: "var(--mono)", fontSize: 12, color: row.color, fontWeight: 600 }}>{row.value ?? "—"}</span>
                        </div>
                      ))}
                    </div>
                  </Panel>
                )}
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════
              TAB: HISTORY
          ═══════════════════════════════════════ */}
          {tab === "history" && (
            <Panel title={`Test History — ${history.length} Runs`} accent="var(--yellow)">
              {history.length === 0 ? (
                <div style={{ textAlign: "center", padding: "48px 0", color: "var(--textdim)", fontFamily: "var(--mono)", fontSize: 12 }}>
                  No history yet — run some tests first
                </div>
              ) : (
                <>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 80px 140px", gap: 12, padding: "6px 14px 10px", borderBottom: "1px solid var(--border)", marginBottom: 4 }}>
                    {["TEST NAME", "STATUS", "TIME"].map(h => (
                      <span key={h} style={{ fontFamily: "var(--mono)", fontSize: 9, color: "var(--dim)", letterSpacing: 2 }}>{h}</span>
                    ))}
                  </div>
                  {history.map((item, i) => <HistoryRow key={item.result_id} item={item} index={i} />)}
                </>
              )}
            </Panel>
          )}

          {/* ═══════════════════════════════════════
              TAB: CONSOLE
          ═══════════════════════════════════════ */}
          {tab === "console" && (
            <Panel title="Live System Console" accent="var(--green)">
              <div ref={logRef} style={{
                height: 520, overflowY: "auto", fontFamily: "var(--mono)",
                fontSize: 12, lineHeight: 2, padding: 4
              }}>
                {log.map((l, i) => (
                  <div key={i} style={{ display: "flex", gap: 14 }}>
                    <span style={{ color: "var(--dim)", flexShrink: 0, userSelect: "none" }}>[{l.ts}]</span>
                    <span style={{ color: l.color }}>{l.msg}</span>
                  </div>
                ))}
                <span style={{ display: "inline-block", width: 10, height: 16, background: "var(--green)", animation: "blink 1s step-end infinite", marginLeft: 2, verticalAlign: "text-bottom" }} />
              </div>
            </Panel>
          )}
        </div>
      </div>
    </>
  );
}