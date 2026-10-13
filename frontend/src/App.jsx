import React, { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000/api";

export default function App() {
  const [status, setStatus] = useState(null);
  const [commits, setCommits] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    try {
      setError(null);
      const [statusRes, logRes] = await Promise.all([
        fetch(`${API_BASE}/status`),
        fetch(`${API_BASE}/log`),
      ]);

      if (!statusRes.ok || !logRes.ok) throw new Error("Failed to reach K-Git API");

      const statusData = await statusRes.json();
      const logData = await logRes.json();

      setStatus(statusData);
      setCommits(logData);
    } catch (err) {
      setError("Unable to connect to FastAPI backend at http://localhost:8000");
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCommit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/commit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message }),
      });

      if (!res.ok) throw new Error("Commit transaction failed");

      setMessage("");
      await fetchData();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: "1.8rem" }}>⚡</span>
          <div>
            <h1 style={styles.title}>K-Git Visual Control Center</h1>
            <p style={styles.subtitle}>Low-Level Content-Addressable Storage Engine Dashboard</p>
          </div>
        </div>
        <button onClick={fetchData} style={styles.refreshBtn}>
          🔄 Refresh State
        </button>
      </header>

      {error && <div style={styles.errorBanner}>{error}</div>}

      <section style={styles.grid}>
        <div style={styles.card}>
          <div style={styles.cardLabel}>DATABASE ENGINE</div>
          <div style={styles.cardValue}>
            <span style={styles.statusDot(status?.initialized)}></span>
            {status?.status || "Checking..."}
          </div>
          <div style={styles.metaText}>{status?.db_path || "—"}</div>
        </div>

        <div style={styles.card}>
          <div style={styles.cardLabel}>STORED OBJECTS (BLOBS & TREES)</div>
          <div style={styles.cardValue}>{status?.total_objects ?? 0}</div>
          <div style={styles.metaText}>zlib Compressed / Level 9</div>
        </div>

        <div style={styles.card}>
          <div style={styles.cardLabel}>ACTIVE COMMIT (HEAD)</div>
          <div style={styles.cardValueCode}>
            {commits[0] ? commits[0].sha1.slice(0, 10) + "..." : "None"}
          </div>
          <div style={styles.metaText}>
            {commits[0] ? `"${commits[0].message}"` : "No commits made yet"}
          </div>
        </div>
      </section>

      <section style={styles.formCard}>
        <h3 style={{ margin: "0 0 10px 0", fontSize: "1.1rem" }}>📸 Record New Repository Snapshot</h3>
        <form onSubmit={handleCommit} style={{ display: "flex", gap: 10 }}>
          <input
            type="text"
            placeholder="Enter commit message (e.g., 'Implemented tree node visualizer')..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            style={styles.input}
            disabled={loading}
          />
          <button type="submit" style={styles.commitBtn} disabled={loading || !message.trim()}>
            {loading ? "Snapshotting..." : "Commit Changes"}
          </button>
        </form>
      </section>

      <section style={styles.card}>
        <h3 style={{ margin: "0 0 18px 0", fontSize: "1.1rem" }}>📜 Commit Directed Acyclic Graph (DAG)</h3>
        {commits.length === 0 ? (
          <p style={{ color: "#888" }}>No commit history found in HEAD lineage.</p>
        ) : (
          <div style={styles.timeline}>
            {commits.map((c, index) => (
              <div key={c.sha1} style={styles.timelineItem}>
                <div style={styles.timelineMarker}>
                  <div style={styles.timelineDot(c.is_head)}></div>
                  {index < commits.length - 1 && <div style={styles.timelineLine}></div>}
                </div>

                <div style={styles.timelineContent}>
                  <div style={styles.timelineHeader}>
                    <span style={styles.commitMessage}>{c.message}</span>
                    {c.is_head && <span style={styles.headBadge}>HEAD</span>}
                  </div>
                  <div style={styles.timelineDetails}>
                    <code style={styles.codeHash}>{c.sha1.slice(0, 12)}</code>
                    <span>• {c.date}</span>
                    <span>• Author: {c.author}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {status?.fingerprints?.length > 0 && (
        <section style={{ ...styles.card, marginTop: 20 }}>
          <h3 style={{ margin: "0 0 12px 0", fontSize: "1.1rem" }}>
            🔑 Stored Object Fingerprints (First 10 Bytes)
          </h3>
          <div style={styles.badgeContainer}>
            {status.fingerprints.map((fp, i) => (
              <span key={i} style={styles.fpBadge}>
                {fp}...
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

const styles = {
  container: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "32px 20px",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    color: "#e6edf3",
    backgroundColor: "#0d1117",
    minHeight: "100vh",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderBottom: "1px solid #30363d",
    paddingBottom: 20,
    marginBottom: 24,
  },
  title: { margin: 0, fontSize: "1.5rem", fontWeight: 600, color: "#f0f6fc" },
  subtitle: { margin: "4px 0 0 0", fontSize: "0.85rem", color: "#8b949e" },
  refreshBtn: {
    backgroundColor: "#21262d",
    color: "#c9d1d9",
    border: "1px solid #30363d",
    borderRadius: 6,
    padding: "8px 14px",
    cursor: "pointer",
    fontSize: "0.85rem",
  },
  errorBanner: {
    backgroundColor: "#490202",
    color: "#ff7b72",
    border: "1px solid #f85149",
    borderRadius: 6,
    padding: "10px 14px",
    marginBottom: 20,
    fontSize: "0.85rem",
  },
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
    gap: 16,
    marginBottom: 24,
  },
  card: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: 8,
    padding: 18,
  },
  cardLabel: { fontSize: "0.75rem", fontWeight: 600, color: "#8b949e", letterSpacing: 0.5 },
  cardValue: {
    fontSize: "1.4rem",
    fontWeight: 600,
    color: "#f0f6fc",
    margin: "8px 0 4px 0",
    display: "flex",
    alignItems: "center",
    gap: 8,
  },
  cardValueCode: {
    fontSize: "1.2rem",
    fontFamily: "monospace",
    color: "#58a6ff",
    margin: "8px 0 4px 0",
  },
  metaText: { fontSize: "0.8rem", color: "#8b949e", wordBreak: "break-all" },
  statusDot: (active) => ({
    display: "inline-block",
    width: 10,
    height: 10,
    borderRadius: "50%",
    backgroundColor: active ? "#3fb950" : "#f85149",
  }),
  formCard: {
    backgroundColor: "#161b22",
    border: "1px solid #30363d",
    borderRadius: 8,
    padding: 18,
    marginBottom: 24,
  },
  input: {
    flex: 1,
    backgroundColor: "#0d1117",
    border: "1px solid #30363d",
    borderRadius: 6,
    padding: "10px 14px",
    color: "#c9d1d9",
    fontSize: "0.9rem",
    outline: "none",
  },
  commitBtn: {
    backgroundColor: "#238636",
    color: "#ffffff",
    border: "none",
    borderRadius: 6,
    padding: "10px 18px",
    fontWeight: 600,
    cursor: "pointer",
  },
  timeline: { display: "flex", flexDirection: "column" },
  timelineItem: { display: "flex", position: "relative", paddingBottom: 22 },
  timelineMarker: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    width: 24,
    marginRight: 14,
  },
  timelineDot: (isHead) => ({
    width: 14,
    height: 14,
    borderRadius: "50%",
    backgroundColor: isHead ? "#238636" : "#1f6feb",
    border: "2px solid #0d1117",
    zIndex: 1,
  }),
  timelineLine: {
    position: "absolute",
    top: 14,
    width: 2,
    bottom: 0,
    backgroundColor: "#30363d",
  },
  timelineContent: { flex: 1 },
  timelineHeader: { display: "flex", alignItems: "center", gap: 10 },
  commitMessage: { fontWeight: 600, color: "#f0f6fc", fontSize: "0.95rem" },
  headBadge: {
    backgroundColor: "#1f6feb26",
    color: "#58a6ff",
    border: "1px solid #388bfd4d",
    fontSize: "0.7rem",
    fontWeight: 600,
    padding: "2px 6px",
    borderRadius: 10,
  },
  timelineDetails: {
    display: "flex",
    gap: 10,
    fontSize: "0.8rem",
    color: "#8b949e",
    marginTop: 4,
  },
  codeHash: { fontFamily: "monospace", color: "#d29922", backgroundColor: "#21262d", padding: "1px 5px", borderRadius: 4 },
  badgeContainer: { display: "flex", flexWrap: "wrap", gap: 8 },
  fpBadge: {
    fontFamily: "monospace",
    fontSize: "0.75rem",
    backgroundColor: "#21262d",
    border: "1px solid #30363d",
    color: "#7ee787",
    padding: "4px 8px",
    borderRadius: 4,
  },
};