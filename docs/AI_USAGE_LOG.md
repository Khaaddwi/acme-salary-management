# AI Usage Log — Salary Management Assessment

This document records how Claude was used during development, as required by the assessment brief.

---

## Tool used

**Claude Sonnet 4.6** via Claude.ai (claude.ai web interface)

---

## Development workflow

The entire application was built in a single Claude.ai session using the computer use / code execution environment. Rather than asking Claude to generate code snippets to copy-paste, I used it as a full agentic coding environment — reading files, executing commands, catching errors, and iterating.

### Phase 1 — Environment reconnaissance

Before writing any code, I used Claude to check what was actually available in the execution environment:

```
Prompt flow:
- Check Python version, available packages (python3 -c "import flask")
- Discover that PyPI and apt network access are blocked
- Find that Flask 3.1.3 is installed system-wide
- Find that React 19, react-dom, react-icons, esbuild 0.27.7 are globally available in npm
- Determine build strategy: Flask backend + esbuild-compiled React frontend
```

This reconnaissance step shaped every subsequent decision. A less careful approach would have wasted time trying to install packages that weren't accessible.

### Phase 2 — Requirements document

Before writing any code, I wrote `docs/REQUIREMENTS.md` as a forcing function to make scope decisions explicit:

- What is the user persona and their job?
- What goes in scope? (salary CRUD, analytics, AI Q&A)
- What is deliberately out of scope and why? (auth, payroll processing, benefits, approvals)
- What are the data model decisions? (store both local currency and USD equivalent)

Key prompts used:

```
"Write a one-page requirements document for a salary management system.
User persona: HR Manager at a 10,000-person company replacing Excel.
Format: Goal, Scope & Features, Deliberately Out of Scope (with reasoning), Data Model, Technical Constraints."
```

### Phase 3 — Backend

Built incrementally, testing at each step:

1. `models.py` — schema design with indexes, WAL mode, FK constraints
2. `seed.py` — data generation with realistic distributions:
   - Weighted country/department/level selection
   - FX conversion stored at seed time
   - Employment type modifiers (contractors +20%, part-time -40%)
   - Deterministic with `random.seed(42)` for reproducible tests
3. `analytics.py` — 5 query functions, each returning a clean list of dicts
4. `app.py` — Flask routes with manual CORS (no flask-cors dependency), parameterized query builder, AI Q&A with SELECT-only guard

Key prompt for the query builder:
```
"Build a Flask route that accepts filter params (department, country, level, 
employment_type, currency, salary_min, salary_max, search) and constructs a 
parameterized WHERE clause — never interpolating user input into the SQL string.
Sort column must be validated against a whitelist. Silent fallback to 'name' 
if invalid value provided."
```

### Phase 4 — Tests

Written before the frontend to validate all backend logic. Prompt:

```
"Write 50 unit and integration tests covering:
- Seed generation: correct count, unique emails/IDs, salary positivity,
  contractor premium, hire date range, determinism
- Analytics: correct aggregates against a known 5-row test DB
- API routes: all filter/sort/pagination combinations, salary update 
  validation, CSV export, CORS headers, error cases
- Schema: table creation, FK enforcement

Use Python unittest with mock.patch to isolate each layer. 
All tests must use in-memory SQLite — never touch the production DB.
Tests must run in < 1 second total."
```

Result: 50 tests, 80ms runtime, all passing.

### Phase 5 — Frontend

Built the React components with deliberate design choices guided by the frontend-design skill:

**Design plan (generated before writing code):**
- Palette: dark navy sidebar (#1A1D23), white content area, electric blue accent (#2563EB)
- Not: warm cream + terracotta (too "AI-generated"). Not: dark background + acid green. Not: SaaS card grid.
- Typography: Inter (clean, professional HR tool) — single font family
- Layout: fixed sidebar navigation, content area with generous padding
- Charts: custom CSS horizontal bars — no chart library import needed

Key component prompts:
```
"Build a React employee list page with:
- Paginated table (25/50/100 per page)
- Column sort (click header toggles asc/desc)  
- Search input (debounced on change)
- Filter panel (7 filters in a collapsible grid, badge count on filter button)
- Export CSV button (direct link to API endpoint)
- Click row → navigate to detail page

No component library. Custom CSS only. useState for all state, 
useCallback for fetchData to avoid re-render loops."
```

```
"Build an AI Q&A page with:
- Textarea + Ask button (Enter submits, Shift+Enter newlines)
- 8 example chips that fire immediately when clicked
- Answer history: question → explanation → result table → SQL details
- Result table: auto-column detection from first row keys
- Format salary columns (containing 'salary') as USD currency
- No answer history shown until first question asked"
```

### Phase 6 — Integration + verification

```
# Verified end-to-end via Flask test client (server wasn't startable in env):
- All 11 API endpoints return 200 with correct content types
- Employee list pagination, filtering, sorting
- Salary update + history audit trail (INR → USD conversion)
- CSV export with filter applied (only Engineering employees)
- Salary band distribution sums to exactly 10,000
- Filter metadata returns all 11 departments, 11 countries, 10 levels
```

---

## Prompting patterns that worked well

**1. Environment-first:** Always check what's actually available before assuming. The environment check revealed Flask + esbuild were available without any installation, which saved significant time.

**2. Test-driven:** Writing the test spec as a prompt before the implementation produced cleaner code — the tests defined the expected interface, which made the implementation straightforward.

**3. Explicit whitelist for security:** Prompting explicitly for "validate sort column against a whitelist, silent fallback" produced correct injection-resistant code. Vague prompts ("make it secure") produce vague results.

**4. Design plan before code:** For the frontend, writing a design plan first (palette, typography, layout principles, what NOT to do) produced a more distinctive result than jumping straight to "build me a React dashboard."

**5. One concern per prompt:** Breaking "build the app" into ~15 focused prompts (one per file/concern) produced better code than trying to generate everything at once.

---

## What the AI accelerated

- Boilerplate (Flask route structure, React component shells) — wrote in seconds what would take minutes
- SQL query generation — analytics queries written and verified instantly
- Test generation — 50 tests across 4 test classes generated in one prompt
- CSS design system — responsive grid, sidebar, modal, charts without looking up docs

## What required human judgment

- Architecture decisions (no ORM, no chart library, static FX rates)
- Scope decisions (what to leave out and why)
- Environment reconnaissance (discovering esbuild, React were available globally)
- Test design (choosing which invariants actually matter to test)
- Security decisions (SELECT-only guard on AI SQL, parameterized query builder design)
