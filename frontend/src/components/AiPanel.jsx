import { useState } from "react";
import Modal from "./Modal";
import { api } from "../api";
import { TONES } from "../constants";

export default function AiPanel({ lead, onClose }) {
  const [mode, setMode] = useState("follow_up");
  const [tone, setTone] = useState("friendly");
  const [senderName, setSenderName] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const hasNotes = lead.notes.trim().length > 0;

  function switchMode(next) {
    setMode(next);
    setResult("");
    setError("");
  }

  async function generate() {
    setLoading(true);
    setError("");
    setResult("");
    try {
      const data =
        mode === "summary"
          ? await api.summarize(lead.id)
          : await api.followUp(lead.id, { tone, sender_name: senderName });
      setResult(data.text);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setError("Could not copy automatically - select the text and copy it manually.");
    }
  }

  return (
    <Modal title={`AI assistant · ${lead.name}`} onClose={onClose} wide>
      <div className="tabs" role="tablist">
        <button
          role="tab"
          aria-selected={mode === "follow_up"}
          className={`tab ${mode === "follow_up" ? "tab-active" : ""}`}
          onClick={() => switchMode("follow_up")}
        >
          Draft follow-up
        </button>
        <button
          role="tab"
          aria-selected={mode === "summary"}
          className={`tab ${mode === "summary" ? "tab-active" : ""}`}
          onClick={() => switchMode("summary")}
        >
          Summarise notes
        </button>
      </div>

      <div className="ai-context">
        <strong>{lead.company}</strong> · {lead.event}
        <p className="muted">{hasNotes ? lead.notes : "No notes yet."}</p>
      </div>

      {mode === "follow_up" ? (
        <div className="field-row">
          <label className="field">
            <span>Tone</span>
            <select value={tone} onChange={(e) => setTone(e.target.value)}>
              {TONES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Sign off as (optional)</span>
            <input value={senderName} onChange={(e) => setSenderName(e.target.value)} placeholder="Your name" />
          </label>
        </div>
      ) : (
        !hasNotes && <div className="alert">Add some notes to this lead first, then come back to summarise them.</div>
      )}

      <div className="form-actions left">
        <button
          className="btn btn-primary"
          onClick={generate}
          disabled={loading || (mode === "summary" && !hasNotes)}
        >
          {loading ? "Generating…" : result ? "Regenerate" : "Generate"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {result && (
        <div className="result">
          <textarea
            className="result-text"
            value={result}
            onChange={(e) => setResult(e.target.value)}
            rows={mode === "summary" ? 7 : 12}
            aria-label="Generated text (editable)"
          />
          <div className="form-actions left">
            <button className="btn" onClick={copy}>
              {copied ? "Copied ✓" : "Copy"}
            </button>
            {mode === "follow_up" && (
              <a
                className="btn"
                href={`mailto:${encodeURIComponent(lead.email)}?${buildMailtoQuery(result)}`}
              >
                Open in email app
              </a>
            )}
          </div>
        </div>
      )}
    </Modal>
  );
}

// The AI is asked to start with "Subject: ..."; split that off for the mailto link.
function buildMailtoQuery(text) {
  const match = text.match(/^\s*subject:\s*(.+)\n+/i);
  const subject = match ? match[1].trim() : "";
  const body = match ? text.slice(match[0].length) : text;
  return `subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
