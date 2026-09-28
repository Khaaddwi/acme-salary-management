# Architecture — ACME Salary Management System

## System overview

```
Browser (React SPA)
      │
      │  HTTP / JSON
      ▼
Flask App (Python 3)  ──────  SQLite DB (WAL mode)
      │
      │  HTTPS / JSON  (AI Q&A only)
      ▼
Anthropic API (claude-sonnet-4-6)
```

Everything runs as a single process. The React SPA is compiled to static files served by Flask — no separate Node.js server.

---

## Request lifecycle

```
User action (search, filter, update)
    │
    ▼
React component (useState / useAsync hook)
    │  fetch()
    ▼
Flask route (app.py)
    │  build_employee_filters() → WHERE clause + params
    ▼
sqlite3 (WAL read / write)
    │
    ▼
JSON response → React re-render
```

For AI Q&A:

```
User types question
    │
    ▼
POST /api/ask
    │  SCHEMA_CONTEXT + question → claude-sonnet-4-6
    ▼
Anthropic API returns {sql, explanation}
    │  Validate: must start with SELECT
    ▼
sqlite3 executes read-only query
    │
    ▼
{results, explanation, sql} → frontend
```

---

## Database schema

```sql
employees
  id              TEXT PK       (UUID)
  employee_id     TEXT UNIQUE   (ACME-00001 ... ACME-10000)
  name            TEXT
  email           TEXT UNIQUE
  department      TEXT          ← indexed
  job_title       TEXT
  job_level       TEXT          ← indexed  (IC1–IC6, M1–M4)
  employment_type TEXT          (Full-time / Part-time / Contractor)
  country         TEXT          ← indexed
  currency        TEXT          (ISO 4217)
  base_salary     REAL          (in local currency)
  salary_usd      REAL          (USD equivalent, computed at seed time)
  hire_date       TEXT          (ISO date)
  created_at      TEXT
  updated_at      TEXT          ← updated on every salary change

salary_history
  id          TEXT PK
  employee_id TEXT FK → employees(id) CASCADE DELETE
  old_salary  REAL
  new_salary  REAL
  currency    TEXT
  changed_at  TEXT
  changed_by  TEXT
  reason      TEXT              (required — enforced at API layer)
```

Indexes on `department`, `country`, `job_level`, `name`, and `salary_history.employee_id` keep all filtered queries under 10ms on 10k rows.

---

## Key design decisions

### 1. No ORM

Using Python's built-in `sqlite3` module directly. The queries are simple enough that an ORM adds more abstraction than value. The `get_connection()` helper sets `row_factory = sqlite3.Row` so rows come back as dict-like objects.

**Trade-off:** Manual SQL is more verbose but easier to audit and optimize. Swapping to PostgreSQL requires only changing the connection string.

### 2. Salary stored in both local currency and USD

`base_salary` stores the amount in the employee's local currency (INR, GBP, EUR, etc.). `salary_usd` stores the USD equivalent computed once at seed time.

**Trade-off:** Stale FX rates. Acceptable for an HR management tool where base salary (in local currency) is the authoritative figure. USD is used only for analytics cross-country comparisons.

**On salary update:** The implicit FX rate is re-derived as `fx = salary_usd / base_salary` and applied to the new local salary to update `salary_usd`. This preserves the original FX rate for that employee. In production: integrate with a live FX API.

### 3. Parameterized query builder for filters

`build_employee_filters()` constructs WHERE clauses by appending `?` placeholders and building a params list — never interpolating user input into the SQL string. Sort column is validated against a whitelist set.

```python
valid_sorts = {"name", "employee_id", "department", ...}
if sort_by not in valid_sorts:
    sort_by = "name"   # silent fallback — tested in test suite
```

### 4. AI Q&A: NL → SQL, not vector search

The AI is given the schema and asked to produce a `{sql, explanation}` JSON. The generated SQL is executed directly.

**Why not RAG/vector search:** The database is structured — SQL gives exact, verifiable answers. RAG is appropriate for unstructured text. For "how many engineers earn above $150k", a COUNT query is strictly better than nearest-neighbor search.

**Safety mitigations:**
- Only SELECT statements accepted (checked before execution)
- Schema-only context given to model (no row data in prompt)
- Parameterized execution prevents second-order injection
- Max 1000 tokens output keeps responses focused

### 5. Frontend: React + esbuild, no dev server

The React app is compiled to `static/app.js` and served by Flask directly. This eliminates the npm dev server and proxy configuration. The esbuild step takes 108ms and produces a 215KB bundle.

**Build command:**
```bash
NODE_PATH=/path/to/globals esbuild src/index.jsx \
  --bundle --outfile=../backend/static/app.js \
  --loader:.jsx=jsx --define:process.env.NODE_ENV='"production"' --minify
```

### 6. Test architecture

Tests use three layers:

| Layer | What's tested | Isolation |
|-------|--------------|-----------|
| Seed generation | Data correctness, uniqueness, distributions | `random.seed(42)` for determinism |
| Analytics | SQL queries return correct aggregates | `unittest.mock.patch` replaces `get_connection` with in-memory DB |
| API routes | HTTP status codes, response shapes, filtering, sorting | Flask test client + `patch` on `get_connection` |
| Schema | Table creation, FK enforcement | Fresh in-memory SQLite |

All tests are fast (~80ms total), deterministic, and isolated from the production database.

---

## Performance profile

| Operation | ~Time | Notes |
|-----------|-------|-------|
| Seed 10,000 employees | ~2s | Batched in 500-row transactions |
| List employees (no filter) | <5ms | Full table scan on 10k rows with LIMIT |
| List employees (filtered) | <3ms | Index on `department`, `country`, `job_level` |
| Search by name | <5ms | LIKE scan — acceptable; in production: FTS5 |
| Analytics queries | <10ms | Aggregates on 10k rows |
| Salary update | <5ms | Write + history insert in one transaction |
| AI Q&A | 1–5s | Anthropic API latency |

SQLite in WAL mode supports concurrent reads from multiple processes. For a single HR manager, this is never a bottleneck.

---

## What production would add

1. **Authentication** — SSO/SAML via Okta or Azure AD; JWT session tokens
2. **PostgreSQL** — drop-in via SQLAlchemy; gains full-text search, pg_trgm indexes
3. **Live FX rates** — Fixer.io or ECB feed; store rate + timestamp per update
4. **Approval workflow** — salary changes above threshold require manager sign-off
5. **Audit log** — who viewed what, not just what changed (SOX compliance)
6. **Role-based access** — HR viewer vs HR editor vs Finance
7. **Bulk import validation** — CSV upload with row-level error reporting
8. **Redis caching** — analytics queries cached with 5-min TTL
