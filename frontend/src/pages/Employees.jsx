import { useState, useCallback, useEffect } from "react";
import { api, fmt$$, fmtNum } from "../utils/api.js";
import { Spinner, ErrorBanner, Pagination, FilterSelect } from "../components/shared.jsx";

const PAGE_SIZES = [25, 50, 100];

const SORT_OPTIONS = [
  { value: "name",        label: "Name" },
  { value: "employee_id", label: "Employee ID" },
  { value: "department",  label: "Department" },
  { value: "country",     label: "Country" },
  { value: "job_level",   label: "Level" },
  { value: "salary_usd",  label: "Salary (USD)" },
  { value: "hire_date",   label: "Hire date" },
];

export default function Employees({ onSelectEmployee }) {
  const [filters, setFilters] = useState({
    search: "", department: "", country: "", job_level: "",
    employment_type: "", currency: "", salary_min: "", salary_max: "",
  });
  const [sortBy,    setSortBy]    = useState("name");
  const [sortDir,   setSortDir]   = useState("asc");
  const [page,      setPage]      = useState(1);
  const [pageSize,  setPageSize]  = useState(50);
  const [data,      setData]      = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);
  const [metaOpts,  setMetaOpts]  = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Load filter metadata once
  useEffect(() => {
    api.meta.filters().then(setMetaOpts).catch(() => {});
  }, []);

  const fetchData = useCallback(() => {
    setLoading(true);
    setError(null);
    api.employees.list({
      ...filters,
      sort_by: sortBy, sort_dir: sortDir,
      page, page_size: pageSize,
    })
      .then((d) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [filters, sortBy, sortDir, page, pageSize]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const setFilter = (key, val) => {
    setPage(1);
    setFilters((f) => ({ ...f, [key]: val }));
  };

  const toggleSort = (col) => {
    if (sortBy === col) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(col);
      setSortDir("asc");
    }
    setPage(1);
  };

  const SortHeader = ({ col, label }) => (
    <th
      className={`sortable ${sortBy === col ? "sort-active" : ""}`}
      onClick={() => toggleSort(col)}
    >
      {label}
      {sortBy === col ? (sortDir === "asc" ? " ↑" : " ↓") : " ↕"}
    </th>
  );

  const exportUrl = api.employees.exportUrl({ ...filters, sort_by: sortBy, sort_dir: sortDir });
  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>People</h1>
          {data && (
            <p className="page-sub">
              {fmtNum(data.total)} {data.total === 1 ? "employee" : "employees"}
              {activeFilterCount > 0 && ` matching ${activeFilterCount} filter${activeFilterCount > 1 ? "s" : ""}`}
            </p>
          )}
        </div>
        <div className="page-actions">
          <button
            className={`btn-outline ${showFilters ? "btn-outline--active" : ""}`}
            onClick={() => setShowFilters((v) => !v)}
          >
            Filters {activeFilterCount > 0 && <span className="badge">{activeFilterCount}</span>}
          </button>
          <a href={exportUrl} className="btn-outline" download="employees.csv">
            Export CSV
          </a>
        </div>
      </header>

      {/* Search bar */}
      <div className="search-bar">
        <input
          type="search"
          placeholder="Search by name, ID, or email…"
          value={filters.search}
          onChange={(e) => setFilter("search", e.target.value)}
        />
      </div>

      {/* Expanded filters */}
      {showFilters && metaOpts && (
        <div className="filters-panel">
          <div className="filters-grid">
            <FilterSelect
              label="Department"
              value={filters.department}
              onChange={(v) => setFilter("department", v)}
              options={metaOpts.departments}
            />
            <FilterSelect
              label="Country"
              value={filters.country}
              onChange={(v) => setFilter("country", v)}
              options={metaOpts.countries}
            />
            <FilterSelect
              label="Level"
              value={filters.job_level}
              onChange={(v) => setFilter("job_level", v)}
              options={metaOpts.job_levels}
            />
            <FilterSelect
              label="Employment type"
              value={filters.employment_type}
              onChange={(v) => setFilter("employment_type", v)}
              options={metaOpts.employment_types}
            />
            <FilterSelect
              label="Currency"
              value={filters.currency}
              onChange={(v) => setFilter("currency", v)}
              options={metaOpts.currencies}
            />
            <label className="filter-field">
              <span className="filter-label">Min salary (USD)</span>
              <input
                type="number" min="0"
                value={filters.salary_min}
                onChange={(e) => setFilter("salary_min", e.target.value)}
                placeholder="0"
              />
            </label>
            <label className="filter-field">
              <span className="filter-label">Max salary (USD)</span>
              <input
                type="number" min="0"
                value={filters.salary_max}
                onChange={(e) => setFilter("salary_max", e.target.value)}
                placeholder="any"
              />
            </label>
          </div>
          <button
            className="btn-ghost"
            onClick={() => {
              setFilters({ search: "", department: "", country: "", job_level: "",
                employment_type: "", currency: "", salary_min: "", salary_max: "" });
              setPage(1);
            }}
          >
            Clear all filters
          </button>
        </div>
      )}

      {/* Sort + page size controls */}
      <div className="table-controls">
        <div className="control-group">
          <label>Sort by
            <select value={sortBy} onChange={(e) => { setSortBy(e.target.value); setPage(1); }}>
              {SORT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </label>
          <label>
            <select value={sortDir} onChange={(e) => { setSortDir(e.target.value); setPage(1); }}>
              <option value="asc">Ascending</option>
              <option value="desc">Descending</option>
            </select>
          </label>
        </div>
        <div className="control-group">
          <label>Show
            <select value={pageSize} onChange={(e) => { setPageSize(+e.target.value); setPage(1); }}>
              {PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
            per page
          </label>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {loading && !data ? (
        <div className="page-center"><Spinner /></div>
      ) : data ? (
        <>
          <div className="table-wrapper">
            <table className="data-table data-table--hoverable">
              <thead>
                <tr>
                  <SortHeader col="employee_id" label="ID" />
                  <SortHeader col="name"        label="Name" />
                  <SortHeader col="department"  label="Department" />
                  <th>Title</th>
                  <SortHeader col="job_level"   label="Level" />
                  <th>Type</th>
                  <SortHeader col="country"     label="Country" />
                  <SortHeader col="salary_usd"  label="Salary (USD)" />
                  <th>Local salary</th>
                  <SortHeader col="hire_date"   label="Hired" />
                </tr>
              </thead>
              <tbody>
                {data.data.length === 0 ? (
                  <tr>
                    <td colSpan="10" className="empty-cell">
                      No employees match the current filters.
                    </td>
                  </tr>
                ) : data.data.map((emp) => (
                  <tr
                    key={emp.id}
                    className="row-clickable"
                    onClick={() => onSelectEmployee(emp.id)}
                  >
                    <td><code>{emp.employee_id}</code></td>
                    <td>{emp.name}</td>
                    <td>{emp.department}</td>
                    <td className="text-muted">{emp.job_title}</td>
                    <td><span className="level-badge">{emp.job_level}</span></td>
                    <td>{emp.employment_type}</td>
                    <td>{emp.country}</td>
                    <td><strong>{fmt$$(emp.salary_usd)}</strong></td>
                    <td className="text-muted">
                      {emp.currency !== "USD"
                        ? `${emp.currency} ${fmtNum(Math.round(emp.base_salary))}`
                        : "—"}
                    </td>
                    <td className="text-muted">{emp.hire_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="table-footer">
            {loading && <Spinner />}
            <Pagination page={data.page} pages={data.pages} onPage={setPage} />
          </div>
        </>
      ) : null}
    </div>
  );
}
