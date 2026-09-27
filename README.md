# ACME Salary Management System

HR salary management system for 10,000 employees across multiple countries.

**Stack:** FastAPI · SQLite · React · Groq (Llama3)

---

## Setup

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Seed the database
```bash
python seed.py
```

### 3. Get a free Groq API key
- Go to **console.groq.com**
- Sign up — free, no credit card needed
- Create an API key

### 4. Start the server
```bash
# Windows
set GROQ_API_KEY=gsk_your-key-here
uvicorn app.main:app --reload --port 8000

# Mac/Linux
export GROQ_API_KEY=gsk_your-key-here
uvicorn app.main:app --reload --port 8000
```

### 5. Open the app
````

[http://localhost:8000](http://localhost:8000)        → React UI\
      [http://localhost:8000/docs](http://localhost:8000/docs)   → Swagger API docs\
      [http://localhost:8000/redoc](http://localhost:8000/redoc)  → ReDoc API docs
```

---

## Project Structure
```

salary-mgmt/\
      ├── backend/\
      │   ├── app/\
      │   │   ├── main.py          # FastAPI app entry point\
      │   │   ├── database.py      # SQLite schema and connection\
      │   │   ├── schemas.py       # Pydantic v2 request/response models\
      │   │   ├── analytics.py     # Dashboard query functions\
      │   │   └── routers/\
      │   │       ├── employees.py # Employee CRUD and CSV export\
      │   │       ├── analytics.py # Dashboard analytics endpoints\
      │   │       ├── meta.py      # Filter dropdown values\
      │   │       └── ask.py       # AI natural language Q&A (Groq)\
      │   ├── tests/\
      │   │   ├── test_seed.py     # Seed generation tests\
      │   │   └── test_api.py      # API integration tests\
      │   ├── seed.py              # Generates 10,000 employees\
      │   └── requirements.txt\
      ├── frontend/\
      │   └── src/                 # React source files\
      └── docs/\
      └── REQUIREMENTS.md
````

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/employees` | List with pagination, search, filters, sort |
| GET | `/api/employees/export` | Download filtered CSV |
| GET | `/api/employees/{id}` | Employee detail + salary history |
| PUT | `/api/employees/{id}/salary` | Update salary with audit record |
| GET | `/api/analytics/summary` | Headcount, payroll, avg salary |
| GET | `/api/analytics/departments` | Per department breakdown |
| GET | `/api/analytics/countries` | Per country breakdown |
| GET | `/api/analytics/levels` | Per job level breakdown |
| GET | `/api/analytics/bands` | Salary band distribution |
| GET | `/api/analytics/employment-types` | Employment type breakdown |
| GET | `/api/meta/filters` | Dropdown filter values |
| POST | `/api/ask` | AI natural language Q&A |

---

## Run Tests

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## Notes

- `GROQ_API_KEY` is only needed for the Ask HR Data feature
- Everything else works without it
- Get free key at console.groq.com — no credit card needed
````