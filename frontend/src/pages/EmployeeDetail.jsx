import { useState } from "react";
import { useAsync } from "../hooks/useAsync.js";
import { api, fmt$$, fmtNum } from "../utils/api.js";
import { Spinner, ErrorBanner, Modal } from "../components/shared.jsx";

export default function EmployeeDetail({ empId, onBack }) {
  const { data, loading, error, refetch } = useAsync(
    () => api.employees.get(empId), [empId]
  );
  const [editing, setEditing] = useState(false);

  if (loading) return <div className="page-center"><Spinner /></div>;
  if (error)   return <ErrorBanner message={error} />;
  if (!data)   return null;

  const { employee: emp, history } = data;

  return (
    <div className="page page--detail">
      <header className="page-header">
        <div className="back-header">
          <button className="btn-ghost btn-back" onClick={onBack}>← Back</button>
          <div>
            <h1>{emp.name}</h1>
            <p className="page-sub"><code>{emp.employee_id}</code> · {emp.job_title}</p>
          </div>
        </div>
        <button className="btn-primary" onClick={() => setEditing(true)}>
          Update salary
        </button>
      </header>

      <div className="detail-grid">

        {/* Profile card */}
        <section className="detail-card">
          <h2 className="card-title">Profile</h2>
          <dl className="detail-list">
            <div className="dl-row">
              <dt>Email</dt>
              <dd>{emp.email}</dd>
            </div>
            <div className="dl-row">
              <dt>Department</dt>
              <dd>{emp.department}</dd>
            </div>
            <div className="dl-row">
              <dt>Job title</dt>
              <dd>{emp.job_title}</dd>
            </div>
            <div className="dl-row">
              <dt>Level</dt>
              <dd><span className="level-badge">{emp.job_level}</span></dd>
            </div>
            <div className="dl-row">
              <dt>Employment type</dt>
              <dd>{emp.employment_type}</dd>
            </div>
            <div className="dl-row">
              <dt>Country</dt>
              <dd>{emp.country}</dd>
            </div>
            <div className="dl-row">
              <dt>Hire date</dt>
              <dd>{emp.hire_date}</dd>
            </div>
          </dl>
        </section>

        {/* Compensation card */}
        <section className="detail-card detail-card--salary">
          <h2 className="card-title">Compensation</h2>
          <div className="salary-hero">
            <span className="salary-usd">{fmt$$(emp.salary_usd)}</span>
            <span className="salary-usd-label">USD equivalent</span>
          </div>
          <dl className="detail-list">
            <div className="dl-row">
              <dt>Local salary</dt>
              <dd>{emp.currency} {fmtNum(Math.round(emp.base_salary))}</dd>
            </div>
            <div className="dl-row">
              <dt>Currency</dt>
              <dd>{emp.currency}</dd>
            </div>
            <div className="dl-row">
              <dt>Last updated</dt>
              <dd>{emp.updated_at.split("T")[0]}</dd>
            </div>
          </dl>
        </section>

      </div>

      {/* Salary history */}
      <section className="section">
        <h2 className="section-title">Salary history</h2>
        {history.length === 0 ? (
          <p className="text-muted">No salary changes recorded yet.</p>
        ) : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Previous salary</th>
                  <th>New salary</th>
                  <th>Change</th>
                  <th>Reason</th>
                  <th>Updated by</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => {
                  const delta = h.new_salary - h.old_salary;
                  const pct   = h.old_salary > 0
                    ? ((delta / h.old_salary) * 100).toFixed(1)
                    : "—";
                  return (
                    <tr key={h.id}>
                      <td>{h.changed_at.split("T")[0]}</td>
                      <td className="text-muted">
                        {h.currency} {fmtNum(Math.round(h.old_salary))}
                      </td>
                      <td>
                        {h.currency} {fmtNum(Math.round(h.new_salary))}
                      </td>
                      <td>
                        <span className={`delta ${delta >= 0 ? "delta--pos" : "delta--neg"}`}>
                          {delta >= 0 ? "+" : ""}{fmtNum(Math.round(delta))} ({pct}%)
                        </span>
                      </td>
                      <td>{h.reason}</td>
                      <td className="text-muted">{h.changed_by}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {editing && (
        <EditSalaryModal
          emp={emp}
          onClose={() => setEditing(false)}
          onSaved={() => { setEditing(false); refetch(); }}
        />
      )}
    </div>
  );
}

function EditSalaryModal({ emp, onClose, onSaved }) {
  const [newSalary,  setNewSalary]  = useState(Math.round(emp.base_salary));
  const [reason,     setReason]     = useState("");
  const [changedBy,  setChangedBy]  = useState("HR Manager");
  const [submitting, setSubmitting] = useState(false);
  const [err,        setErr]        = useState(null);

  const submit = async () => {
    if (!reason.trim()) { setErr("Reason is required."); return; }
    if (newSalary <= 0)  { setErr("Salary must be positive."); return; }
    setSubmitting(true);
    setErr(null);
    try {
      await api.employees.updateSalary(emp.id, {
        new_salary: newSalary,
        reason: reason.trim(),
        changed_by: changedBy.trim() || "HR Manager",
      });
      onSaved();
    } catch (e) {
      setErr(e.message);
      setSubmitting(false);
    }
  };

  const newUsd = emp.base_salary > 0
    ? (newSalary / emp.base_salary) * emp.salary_usd
    : newSalary;

  return (
    <Modal title="Update salary" onClose={onClose}>
      <div className="form-field">
        <label>Employee</label>
        <p className="form-static">{emp.name} · {emp.employee_id}</p>
      </div>
      <div className="form-field">
        <label>Current salary</label>
        <p className="form-static">
          {emp.currency} {fmtNum(Math.round(emp.base_salary))} (≈ {fmt$$(emp.salary_usd)} USD)
        </p>
      </div>
      <div className="form-field">
        <label>New salary ({emp.currency})</label>
        <input
          type="number"
          min="1"
          value={newSalary}
          onChange={(e) => setNewSalary(+e.target.value)}
        />
        {newSalary > 0 && (
          <small className="form-hint">≈ {fmt$$(Math.round(newUsd))} USD equivalent</small>
        )}
      </div>
      <div className="form-field">
        <label>Reason for change <span className="required">*</span></label>
        <textarea
          rows={3}
          placeholder="e.g. Annual performance review — exceeds expectations"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      </div>
      <div className="form-field">
        <label>Updated by</label>
        <input
          type="text"
          value={changedBy}
          onChange={(e) => setChangedBy(e.target.value)}
          placeholder="HR Manager"
        />
      </div>
      {err && <div className="form-error">{err}</div>}
      <div className="modal-actions">
        <button className="btn-ghost" onClick={onClose} disabled={submitting}>Cancel</button>
        <button className="btn-primary" onClick={submit} disabled={submitting}>
          {submitting ? "Saving…" : "Save change"}
        </button>
      </div>
    </Modal>
  );
}
