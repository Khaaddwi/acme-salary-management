import { useState } from "react";

export function Spinner() {
  return <div className="spinner" aria-label="Loading…" />;
}

export function ErrorBanner({ message }) {
  return <div className="error-banner">⚠ {message}</div>;
}

export function StatCard({ label, value, sub }) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
      {sub && <span className="stat-sub">{sub}</span>}
    </div>
  );
}

/** Simple horizontal bar chart rendered with CSS. */
export function BarChart({ data, labelKey, valueKey, color = "var(--accent)" }) {
  if (!data || data.length === 0) return null;
  const max = Math.max(...data.map((d) => d[valueKey]));

  return (
    <div className="bar-chart">
      {data.map((d) => {
        const pct = max > 0 ? (d[valueKey] / max) * 100 : 0;
        return (
          <div key={d[labelKey]} className="bar-row">
            <span className="bar-label">{d[labelKey]}</span>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: `${pct}%`, background: color }}
              />
            </div>
            <span className="bar-value">{d[valueKey].toLocaleString()}</span>
          </div>
        );
      })}
    </div>
  );
}

/** Modal dialog */
export function Modal({ title, onClose, children }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

/** Pagination controls */
export function Pagination({ page, pages, onPage }) {
  if (pages <= 1) return null;
  const visible = [];
  const delta = 2;
  for (let i = 1; i <= pages; i++) {
    if (i === 1 || i === pages || (i >= page - delta && i <= page + delta)) {
      visible.push(i);
    }
  }
  // Insert ellipsis markers
  const items = [];
  let prev = 0;
  for (const n of visible) {
    if (n - prev > 1) items.push("…");
    items.push(n);
    prev = n;
  }

  return (
    <div className="pagination">
      <button disabled={page <= 1} onClick={() => onPage(page - 1)}>←</button>
      {items.map((item, i) =>
        item === "…" ? (
          <span key={`e${i}`} className="pag-ellipsis">…</span>
        ) : (
          <button
            key={item}
            className={item === page ? "pag-active" : ""}
            onClick={() => onPage(item)}
          >
            {item}
          </button>
        )
      )}
      <button disabled={page >= pages} onClick={() => onPage(page + 1)}>→</button>
    </div>
  );
}

/** Select-based filter dropdown */
export function FilterSelect({ label, value, onChange, options, placeholder = "All" }) {
  return (
    <label className="filter-field">
      <span className="filter-label">{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">{placeholder}</option>
        {options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    </label>
  );
}
