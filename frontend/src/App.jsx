import { useState } from "react";
import Dashboard from "./pages/Dashboard.jsx";
import Employees from "./pages/Employees.jsx";
import EmployeeDetail from "./pages/EmployeeDetail.jsx";
import AskHR from "./pages/AskHR.jsx";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard" },
  { id: "employees", label: "People" },
  { id: "ask",       label: "Ask HR Data" },
];

export default function App() {
  const [page, setPage]           = useState("dashboard");
  const [selectedEmpId, setEmpId] = useState(null);

  const navigate = (to, empId = null) => {
    setPage(to);
    setEmpId(empId);
    window.scrollTo(0, 0);
  };

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="brand-mark">A</span>
          <span className="brand-name">ACME <span>HR</span></span>
        </div>
        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${page === item.id || (page === "employee" && item.id === "employees") ? "nav-item--active" : ""}`}
              onClick={() => navigate(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="user-badge">
            <span className="user-avatar">H</span>
            <span className="user-info">
              <strong>HR Manager</strong>
              <small>ACME Corp</small>
            </span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        {page === "dashboard" && <Dashboard />}
        {page === "employees" && (
          <Employees onSelectEmployee={(id) => navigate("employee", id)} />
        )}
        {page === "employee" && selectedEmpId && (
          <EmployeeDetail
            empId={selectedEmpId}
            onBack={() => navigate("employees")}
          />
        )}
        {page === "ask" && <AskHR />}
      </main>
    </div>
  );
}
