# Salary Management System — Requirements Document

**Author:** Engineering Assessment Submission  
**Date:** 2026-09-26  
**Version:** 1.0

---

## 1. Goal

Replace the HR team's Excel-based salary management workflow with a web application that lets the ACME HR Manager view, search, update, and analyze salary data for ~10,000 employees across multiple countries — from a single, fast, auditable interface.

---

## 2. User Persona

**Primary:** HR Manager  
A non-technical business user who currently manages salary spreadsheets. They need to:
- Find employee records quickly
- Update salaries (promotions, cost-of-living adjustments, corrections)
- Understand how the org pays people — by department, country, level, and band
- Export data for payroll or audit purposes

---

## 3. Scope & Features

### 3.1 Employee Salary Data Management
- View a paginated, searchable, sortable table of all employees
- Filter by: department, country, employment type, currency, job level
- Search by employee name or employee ID
- View an individual employee's salary profile (current salary, history, metadata)
- Edit an employee's salary (with a required reason / change note)
- Salary history log per employee — who changed it, when, and why

### 3.2 Bulk Operations
- Import employees from CSV (name, department, country, salary, currency, level)
- Export current filtered view to CSV

### 3.3 Analytics Dashboard
- Summary cards: total headcount, total payroll (USD equivalent), avg salary
- Salary distribution by department (chart)
- Headcount and average salary by country (chart)
- Salary band coverage — % of employees per compensation band
- Pay equity signals: department-level salary spread (min/max/median)

### 3.4 AI-powered Q&A ("Ask HR Data")
- Natural language questions answered against the salary database
- Examples: "Which department has the highest average salary?", "How many engineers earn above $150k?", "Show me employees in India below the median"
- Powered by Claude API (claude-sonnet-4-6) with database context

---

## 4. Deliberately Out of Scope (and Why)

| Out of Scope | Reasoning |
|---|---|
| **Authentication / login** | Single HR manager persona; multi-user auth adds significant complexity without assessment value. In production: SSO/SAML integration. |
| **Role-based access control** | Follows from no auth; irrelevant for single user. |
| **Payroll processing / payments** | This is a salary *data management* tool, not a payroll system. Integration with payroll providers (ADP, Workday) is a separate concern. |
| **Benefits / equity / bonus tracking** | Scope creep — base salary is the defined domain. |
| **Performance management integration** | Out of domain; salary changes are manually entered with notes. |
| **Real-time currency conversion** | We store a USD-equivalent at seed time. Live FX rates require external API. |
| **Document generation** | Offer letters, contracts — out of domain for this tool. |
| **Notifications / approvals workflow** | Multi-stakeholder workflow; not relevant for single HR manager. |
| **Mobile app** | Web-responsive suffices for HR desktop workflows. |
| **Multi-tenancy / org hierarchy** | ACME is one org; no need for tenant isolation. |

---

## 5. Data Model

```
Employee
  id              UUID PK
  employee_id     string (ACME-XXXXX)
  name            string
  email           string
  department      string
  job_title       string
  job_level       string  (IC1–IC6, M1–M4)
  employment_type string  (Full-time, Part-time, Contractor)
  country         string
  currency        string  (ISO 4217)
  base_salary     decimal
  salary_usd      decimal (converted at seed time)
  hire_date       date
  created_at      datetime
  updated_at      datetime

SalaryHistory
  id              UUID PK
  employee_id     FK → Employee.id
  old_salary      decimal
  new_salary      decimal
  currency        string
  changed_at      datetime
  changed_by      string  (HR manager name)
  reason          string
```

---

## 6. Technical Constraints

- **Backend:** Python 3 + Flask + SQLite
- **Frontend:** React (single-page app, built with esbuild)
- **No external runtime dependencies beyond Flask and the standard library**
- **AI Q&A:** Anthropic API (claude-sonnet-4-6), called from the backend

---

## 7. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Pagination | 50 rows/page default; user-selectable 25/50/100 |
| Search latency | < 200ms for filtered queries on 10k employees |
| Seed time | < 30s for 10,000 employees |
| Test coverage | Unit tests on all business logic; integration tests on all API routes |

---

## 8. Trade-off Notes

- **SQLite over PostgreSQL:** Sufficient for 10k employees, zero setup overhead, ships as a file. In production: swap SQLAlchemy dialect.
- **React (no Next.js):** Simpler setup without a Node.js server; esbuild bundles to a single JS file served by Flask.
- **USD-equivalent stored at seed:** Avoids live FX dependency. Trade-off: stale exchange rates for display purposes.
- **AI Q&A generates SQL from NL:** Gives precise answers vs. fuzzy vector search. Risk: SQL injection — mitigated by using read-only parameterized queries and schema-only context.
