import asyncio
import os

import aiosqlite
import pytest

# IMPORTANT:
# Set test DB path BEFORE importing app.main / app.database
TEST_DB_PATH = "test_temp.db"
os.environ["DB_PATH"] = TEST_DB_PATH

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db, SCHEMA


# Test data

EMPLOYEES = [
    (
        "1",
        "ACME-00001",
        "Alice Johnson",
        "alice@acme.com",
        "Engineering",
        "Software Engineer",
        "IC3",
        "Full-time",
        "United States",
        "USD",
        120_000,
        120_000,
        "2022-03-15",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00",
    ),
    (
        "2",
        "ACME-00002",
        "Bob Smith",
        "bob@acme.com",
        "Engineering",
        "Senior Software Engineer",
        "IC4",
        "Full-time",
        "United States",
        "USD",
        150_000,
        150_000,
        "2020-07-01",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00",
    ),
    (
        "3",
        "ACME-00003",
        "Priya Patel",
        "priya@acme.com",
        "Product",
        "Product Manager",
        "IC3",
        "Full-time",
        "India",
        "INR",
        5_000_000,
        60_000,
        "2023-01-10",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00",
    ),
    (
        "4",
        "ACME-00004",
        "Carlos García",
        "carlos@acme.com",
        "Sales",
        "Account Executive",
        "IC2",
        "Contractor",
        "Germany",
        "EUR",
        70_000,
        76_000,
        "2021-11-20",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00",
    ),
    (
        "5",
        "ACME-00005",
        "Emma Wilson",
        "emma@acme.com",
        "Marketing",
        "Marketing Manager",
        "IC3",
        "Part-time",
        "United Kingdom",
        "GBP",
        45_000,
        57_000,
        "2024-05-01",
        "2026-01-01T00:00:00",
        "2026-01-01T00:00:00",
    ),
]


# Test database

async def _setup_test_db():
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        await db.executescript(SCHEMA)

        await db.executemany(
            """
            INSERT INTO employees (
                id,
                employee_id,
                name,
                email,
                department,
                job_title,
                job_level,
                employment_type,
                country,
                currency,
                base_salary,
                salary_usd,
                hire_date,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            EMPLOYEES,
        )

        await db.commit()


async def override_get_db():
    async with aiosqlite.connect(TEST_DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        yield db


def setup_module(module):
    app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_test_database():
    # Start every test with a fresh database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    asyncio.run(_setup_test_db())

    yield


def teardown_module(module):
    app.dependency_overrides.clear()

    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


client = TestClient(
    app,
    raise_server_exceptions=True,
)

# Employee list

class TestListEmployees:
    def test_returns_200(self):
        r = client.get("/api/employees")
        assert r.status_code == 200

    def test_returns_all_employees(self):
        r = client.get("/api/employees")
        assert r.json()["total"] == 5

    def test_pagination_page_size(self):
        r = client.get("/api/employees?page=1&page_size=2")
        data = r.json()
        assert len(data["data"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_pagination_page_2(self):
        r = client.get("/api/employees?page=2&page_size=2")
        data = r.json()
        assert len(data["data"]) == 2   # rows 3 & 4

    def test_search_by_name(self):
        r = client.get("/api/employees?search=Alice")
        data = r.json()
        assert data["total"] == 1
        assert data["data"][0]["name"] == "Alice Johnson"

    def test_search_by_employee_id(self):
        r = client.get("/api/employees?search=ACME-00003")
        data = r.json()
        assert data["total"] == 1
        assert data["data"][0]["name"] == "Priya Patel"

    def test_filter_by_department(self):
        r = client.get("/api/employees?department=Engineering")
        data = r.json()
        assert data["total"] == 2
        assert all(e["department"] == "Engineering" for e in data["data"])

    def test_filter_by_country(self):
        r = client.get("/api/employees?country=India")
        data = r.json()
        assert data["total"] == 1
        assert data["data"][0]["name"] == "Priya Patel"

    def test_filter_by_job_level(self):
        r = client.get("/api/employees?job_level=IC3")
        data = r.json()
        assert data["total"] == 3   # Alice, Priya, Emma

    def test_filter_by_employment_type(self):
        r = client.get("/api/employees?employment_type=Contractor")
        data = r.json()
        assert data["total"] == 1
        assert data["data"][0]["name"] == "Carlos García"

    def test_salary_min_filter(self):
        r = client.get("/api/employees?salary_min=100000")
        data = r.json()
        for e in data["data"]:
            assert e["salary_usd"] >= 100_000

    def test_salary_max_filter(self):
        r = client.get("/api/employees?salary_max=100000")
        data = r.json()
        for e in data["data"]:
            assert e["salary_usd"] <= 100_000

    def test_sort_by_salary_desc(self):
        r = client.get("/api/employees?sort_by=salary_usd&sort_dir=desc")
        salaries = [e["salary_usd"] for e in r.json()["data"]]
        assert salaries == sorted(salaries, reverse=True)

    def test_sort_by_name_asc(self):
        r = client.get("/api/employees?sort_by=name&sort_dir=asc")
        names = [e["name"] for e in r.json()["data"]]
        assert names == sorted(names)

    def test_invalid_sort_field_falls_back_safely(self):
        """Injecting invalid sort column must not 500 — falls back to 'name'."""
        r = client.get("/api/employees?sort_by=DROP+TABLE+employees")
        assert r.status_code == 200

    def test_response_schema_fields(self):
        r = client.get("/api/employees?page_size=1")
        emp = r.json()["data"][0]
        for field in ["id", "employee_id", "name", "email", "department",
                      "job_title", "job_level", "employment_type", "country",
                      "currency", "base_salary", "salary_usd", "hire_date"]:
            assert field in emp


# Employee detail

class TestGetEmployee:
    def test_found(self):
        r = client.get("/api/employees/1")
        assert r.status_code == 200
        data = r.json()
        assert "employee" in data
        assert "history" in data
        assert data["employee"]["name"] == "Alice Johnson"

    def test_not_found(self):
        r = client.get("/api/employees/nonexistent-id")
        assert r.status_code == 404

    def test_history_empty_initially(self):
        r = client.get("/api/employees/2")
        assert r.json()["history"] == []


# Salary update

class TestUpdateSalary:
    def test_success(self):
        r = client.put("/api/employees/1/salary", json={
            "new_salary": 130_000,
            "reason": "Annual review — strong performance",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["new_salary"] == 130_000

    def test_creates_history_record(self):
        # Update first, then check history
        client.put("/api/employees/2/salary", json={
            "new_salary": 160_000, "reason": "Promotion to IC5",
        })
        r = client.get("/api/employees/2")
        history = r.json()["history"]
        assert len(history) >= 1
        assert history[0]["new_salary"] == 160_000
        assert history[0]["reason"] == "Promotion to IC5"

    def test_missing_reason_rejected(self):
        r = client.put("/api/employees/1/salary", json={"new_salary": 130_000})
        assert r.status_code == 422   # Pydantic validation error

    def test_blank_reason_rejected(self):
        r = client.put("/api/employees/1/salary", json={
            "new_salary": 130_000, "reason": "  "
        })
        assert r.status_code == 422

    def test_negative_salary_rejected(self):
        r = client.put("/api/employees/1/salary", json={
            "new_salary": -5000, "reason": "Test"
        })
        assert r.status_code == 422

    def test_zero_salary_rejected(self):
        r = client.put("/api/employees/1/salary", json={
            "new_salary": 0, "reason": "Test"
        })
        assert r.status_code == 422

    def test_employee_not_found(self):
        r = client.put("/api/employees/bad-id/salary", json={
            "new_salary": 50_000, "reason": "Test"
        })
        assert r.status_code == 404

    def test_usd_equivalent_updated(self):
        """For USD employees, new_salary_usd should equal new_salary."""
        r = client.put("/api/employees/1/salary", json={
            "new_salary": 140_000, "reason": "Spot bonus adjustment"
        })
        data = r.json()
        assert abs(data["new_salary_usd"] - 140_000) < 1.0  # USD fx=1.0


# CSV export

class TestExport:
    def test_returns_csv(self):
        r = client.get("/api/employees/export")
        assert r.status_code == 200
        assert "text/csv" in r.headers["content-type"]

    def test_csv_has_header(self):
        r = client.get("/api/employees/export")
        lines = r.text.strip().split("\n")
        assert "employee_id" in lines[0]
        assert "salary_usd" in lines[0]

    def test_filter_applied_to_export(self):
        r = client.get("/api/employees/export?department=Engineering")
        lines = [l for l in r.text.strip().split("\n") if l]
        # 1 header + 2 engineering employees
        assert len(lines) == 3

    def test_all_employees_exported_without_filter(self):
        r = client.get("/api/employees/export")
        lines = [l for l in r.text.strip().split("\n") if l]
        assert len(lines) == 6  # 1 header + 5 employees


# Filter metadata

class TestFilterMeta:
    def test_returns_200(self):
        assert client.get("/api/meta/filters").status_code == 200

    def test_all_keys_present(self):
        data = client.get("/api/meta/filters").json()
        for key in ["departments", "countries", "job_levels", "currencies", "employment_types"]:
            assert key in data

    def test_departments_correct(self):
        data = client.get("/api/meta/filters").json()
        assert set(data["departments"]) == {"Engineering", "Product", "Sales", "Marketing"}

    def test_job_levels_correct(self):
        data = client.get("/api/meta/filters").json()
        assert set(data["job_levels"]) == {"IC2", "IC3", "IC4"}


# Analytics

class TestAnalytics:
    def test_summary_status(self):
        assert client.get("/api/analytics/summary").status_code == 200

    def test_summary_total_employees(self):
        data = client.get("/api/analytics/summary").json()
        assert data["total_employees"] == 5

    def test_summary_total_payroll(self):
        # 120k + 150k + 60k + 76k + 57k = 463k
        data = client.get("/api/analytics/summary").json()
        assert abs(data["total_payroll_usd"] - 463_000) < 1

    def test_summary_required_fields(self):
        data = client.get("/api/analytics/summary").json()
        for f in ["total_employees", "total_payroll_usd", "avg_salary_usd",
                  "min_salary_usd", "max_salary_usd", "num_departments", "num_countries"]:
            assert f in data

    def test_departments_returns_list(self):
        r = client.get("/api/analytics/departments")
        assert isinstance(r.json(), list)
        assert len(r.json()) == 4

    def test_departments_engineering_headcount(self):
        depts = client.get("/api/analytics/departments").json()
        eng = next(d for d in depts if d["department"] == "Engineering")
        assert eng["headcount"] == 2

    def test_departments_engineering_avg(self):
        depts = client.get("/api/analytics/departments").json()
        eng = next(d for d in depts if d["department"] == "Engineering")
        assert abs(eng["avg_salary_usd"] - 135_000) < 1

    def test_countries_returns_list(self):
        r = client.get("/api/analytics/countries")
        assert len(r.json()) == 4

    def test_levels_returns_list(self):
        r = client.get("/api/analytics/levels")
        assert len(r.json()) == 3  # IC2, IC3, IC4

    def test_bands_sum_equals_total(self):
        bands = client.get("/api/analytics/bands").json()
        assert sum(b["count"] for b in bands) == 5

    def test_employment_types(self):
        data = client.get("/api/analytics/employment-types").json()
        types = {e["employment_type"] for e in data}
        assert types == {"Full-time", "Contractor", "Part-time"}


# AI Ask endpoint

class TestAskEndpoint:
    def test_empty_question_rejected(self):
        r = client.post("/api/ask", json={"question": ""})
        assert r.status_code == 422

    def test_short_question_rejected(self):
        r = client.post("/api/ask", json={"question": "hi"})
        assert r.status_code == 422

    def test_missing_api_key_returns_503(self):
        saved = os.environ.pop("GROQ_API_KEY", None)

        try:
            r = client.post(
                "/api/ask",
                json={"question": "How many employees?"},
            )

            assert r.status_code == 503

        finally:
            if saved:
                os.environ["GROQ_API_KEY"] = saved

    def test_missing_question_field_rejected(self):
        r = client.post("/api/ask", json={})
        assert r.status_code == 422


# CORS

class TestCORS:
    def test_cors_header_present(self):
        r = client.get("/api/employees", headers={"Origin": "http://localhost:3000"})
        assert r.headers.get("access-control-allow-origin") in ("*", "http://localhost:3000")

    def test_options_preflight(self):
        r = client.options("/api/employees", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        })
        assert r.status_code in (200, 204)


# OpenAPI docs

class TestOpenAPI:
    def test_docs_available(self):
        assert client.get("/docs").status_code == 200

    def test_openapi_json_available(self):
        r = client.get("/openapi.json")
        assert r.status_code == 200
        schema = r.json()
        assert schema["info"]["title"] == "ACME Salary Management API"

    def test_all_routes_in_schema(self):
        paths = client.get("/openapi.json").json()["paths"]
        assert "/api/employees" in paths
        assert "/api/employees/{emp_id}" in paths
        assert "/api/employees/{emp_id}/salary" in paths
        assert "/api/analytics/summary" in paths
        assert "/api/ask" in paths
