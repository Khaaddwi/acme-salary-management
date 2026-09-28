import { useState } from "react";
import { api, fmt$$ } from "../utils/api.js";

const EXAMPLES = [
  "Which department has the highest average salary?",
  "How many employees earn above $150,000?",
  "Show the top 10 highest paid employees",
  "What's the average salary in Engineering vs Sales?",
  "How many contractors do we have in India?",
  "Which country has the most employees at the IC4 level?",
  "Show me all employees hired after 2023",
  "What percentage of employees earn between $100k and $150k?",
];

export default function AskHR() {
  const [question,  setQuestion]  = useState("");
  const [history,   setHistory]   = useState([]);
  const [loading,   setLoading]   = useState(false);

  const ask = async (q = question) => {
    const trimmed = q.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    try {
      const result = await api.ask(trimmed);
      setHistory((h) => [{ question: trimmed, ...result }, ...h]);
    } catch (e) {
      setHistory((h) => [{ question: trimmed, error: e.message }, ...h]);
    } finally {
      setLoading(false);
      setQuestion("");
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Ask HR Data</h1>
          <p className="page-sub">Ask natural language questions about the org's salary data</p>
        </div>
      </header>

      {/* Input */}
      <div className="ask-input-area">
        <textarea
          className="ask-textarea"
          rows={2}
          placeholder="Ask a question about salary data…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); ask(); }
          }}
        />
        <button
          className="btn-primary ask-submit"
          onClick={() => ask()}
          disabled={loading || !question.trim()}
        >
          {loading ? "Thinking…" : "Ask"}
        </button>
      </div>

      {/* Example questions */}
      {history.length === 0 && (
        <div className="examples-section">
          <p className="examples-label">Try one of these:</p>
          <div className="examples-grid">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                className="example-chip"
                onClick={() => ask(ex)}
                disabled={loading}
              >
                {ex}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Answer history */}
      <div className="answers-list">
        {history.map((item, i) => (
          <div key={i} className="answer-card">
            <p className="answer-question">{item.question}</p>
            {item.error ? (
              <div className="answer-error">⚠ {item.error}</div>
            ) : (
              <>
                <p className="answer-explanation">{item.explanation}</p>
                {item.results && item.results.length > 0 && (
                  <div className="answer-results">
                    <ResultTable rows={item.results} />
                  </div>
                )}
                {item.sql && (
                  <details className="answer-sql">
                    <summary>SQL query</summary>
                    <pre>{item.sql}</pre>
                  </details>
                )}
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ResultTable({ rows }) {
  if (!rows || rows.length === 0) return null;
  const cols = Object.keys(rows[0]);
  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {cols.map((c) => <th key={c}>{c.replace(/_/g, " ")}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {cols.map((c) => (
                <td key={c}>
                  {typeof row[c] === "number" && c.includes("salary")
                    ? fmt$$(row[c])
                    : row[c] ?? "—"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="result-count">{rows.length} {rows.length === 1 ? "row" : "rows"}</p>
    </div>
  );
}
