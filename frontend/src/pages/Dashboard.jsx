import { useAsync } from "../hooks/useAsync.js";
import { api, fmt$$, fmtNum } from "../utils/api.js";
import { Spinner, ErrorBanner, StatCard, BarChart } from "../components/shared.jsx";

export default function Dashboard() {
  const summary  = useAsync(() => api.analytics.summary(),     []);
  const depts    = useAsync(() => api.analytics.departments(),  []);
  const countries= useAsync(() => api.analytics.countries(),    []);
  const bands    = useAsync(() => api.analytics.bands(),        []);
  const levels   = useAsync(() => api.analytics.levels(),       []);
  const empTypes = useAsync(() => api.analytics.empTypes(),     []);

  if (summary.loading) return <div className="page-center"><Spinner /></div>;
  if (summary.error)   return <ErrorBanner message={summary.error} />;

  const s = summary.data;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-sub">Salary intelligence across {fmtNum(s.num_countries)} countries, {fmtNum(s.num_departments)} departments</p>
        </div>
      </header>

      {/* Summary cards */}
      <div className="stat-grid">
        <StatCard label="Total headcount"    value={fmtNum(s.total_employees)}   />
        <StatCard label="Annual payroll"     value={fmt$$(s.total_payroll_usd)}  sub="USD equivalent" />
        <StatCard label="Average salary"     value={fmt$$(s.avg_salary_usd)}     sub="USD equivalent" />
        <StatCard label="Salary range"       value={`${fmt$$(s.min_salary_usd)} – ${fmt$$(s.max_salary_usd)}`} />
        <StatCard label="Countries"          value={fmtNum(s.num_countries)}     />
        <StatCard label="Departments"        value={fmtNum(s.num_departments)}   />
      </div>

      {/* Charts */}
      <div className="charts-grid">

        <section className="chart-card">
          <h2 className="chart-title">Headcount by department</h2>
          {depts.loading ? <Spinner /> : (
            <BarChart
              data={[...depts.data].sort((a, b) => b.headcount - a.headcount)}
              labelKey="department"
              valueKey="headcount"
              color="var(--accent)"
            />
          )}
        </section>

        <section className="chart-card">
          <h2 className="chart-title">Average salary by department (USD)</h2>
          {depts.loading ? <Spinner /> : (
            <BarChart
              data={[...depts.data].sort((a, b) => b.avg_salary_usd - a.avg_salary_usd)}
              labelKey="department"
              valueKey="avg_salary_usd"
              color="var(--accent-2)"
            />
          )}
        </section>

        <section className="chart-card">
          <h2 className="chart-title">Salary band distribution</h2>
          {bands.loading ? <Spinner /> : (
            <BarChart
              data={bands.data}
              labelKey="band"
              valueKey="count"
              color="var(--accent-3)"
            />
          )}
        </section>

        <section className="chart-card">
          <h2 className="chart-title">Headcount by country</h2>
          {countries.loading ? <Spinner /> : (
            <BarChart
              data={[...countries.data].slice(0, 10)}
              labelKey="country"
              valueKey="headcount"
              color="var(--accent)"
            />
          )}
        </section>

        <section className="chart-card">
          <h2 className="chart-title">Average salary by level (USD)</h2>
          {levels.loading ? <Spinner /> : (
            <BarChart
              data={[...levels.data].sort((a, b) => b.avg_salary_usd - a.avg_salary_usd)}
              labelKey="job_level"
              valueKey="avg_salary_usd"
              color="var(--accent-2)"
            />
          )}
        </section>

        <section className="chart-card">
          <h2 className="chart-title">Employment type breakdown</h2>
          {empTypes.loading ? <Spinner /> : (
            <div className="emp-type-chart">
              {empTypes.data.map((et) => (
                <div key={et.employment_type} className="emp-type-row">
                  <div className="emp-type-meta">
                    <strong>{et.employment_type}</strong>
                    <span>{fmtNum(et.headcount)} people</span>
                  </div>
                  <div className="emp-type-stats">
                    <span>Avg {fmt$$(et.avg_salary_usd)}</span>
                    <span>Total {fmt$$(et.total_payroll_usd)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

      </div>

      {/* Department table */}
      <section className="section">
        <h2 className="section-title">Pay equity by department</h2>
        {depts.loading ? <Spinner /> : (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Headcount</th>
                  <th>Min (USD)</th>
                  <th>Avg (USD)</th>
                  <th>Max (USD)</th>
                  <th>Spread</th>
                  <th>Total payroll</th>
                </tr>
              </thead>
              <tbody>
                {depts.data.map((d) => {
                  const spread = d.max_salary_usd - d.min_salary_usd;
                  return (
                    <tr key={d.department}>
                      <td>{d.department}</td>
                      <td>{fmtNum(d.headcount)}</td>
                      <td>{fmt$$(d.min_salary_usd)}</td>
                      <td><strong>{fmt$$(d.avg_salary_usd)}</strong></td>
                      <td>{fmt$$(d.max_salary_usd)}</td>
                      <td>{fmt$$(spread)}</td>
                      <td>{fmt$$(d.total_payroll_usd)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
