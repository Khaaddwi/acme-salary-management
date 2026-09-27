"""
Tests for the seed data generation logic.
No database required — tests pure Python functions.
"""

import random
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from seed import (
    generate_employees,
    _gen_employee_id,
    _gen_email,
    _weighted_choice,
    DEPARTMENTS,
    COUNTRIES,
    JOB_LEVELS,
)


class TestEmployeeIdGeneration:
    def test_format(self):
        assert _gen_employee_id(1)     == "ACME-00001"
        assert _gen_employee_id(42)    == "ACME-00042"
        assert _gen_employee_id(9999)  == "ACME-09999"
        assert _gen_employee_id(10000) == "ACME-10000"

    def test_zero_padded_to_5_digits(self):
        eid = _gen_employee_id(7)
        assert len(eid.split("-")[1]) == 5


class TestEmailGeneration:
    def test_uses_acme_domain(self):
        email = _gen_email("Alice Smith", set())
        assert email.endswith("@acme.com")

    def test_unique_on_collision(self):
        existing = {"alice.smith@acme.com"}
        e1 = _gen_email("Alice Smith", existing)
        assert e1 not in existing
        existing.add(e1)
        e2 = _gen_email("Alice Smith", existing)
        assert e2 not in existing
        assert e1 != e2

    def test_ascii_only(self):
        # Name with non-ascii character
        email = _gen_email("Björn Müller", set())
        assert email.isascii()


class TestWeightedChoice:
    def test_always_returns_valid_key(self):
        opts = {"A": 0.5, "B": 0.3, "C": 0.2}
        for _ in range(100):
            assert _weighted_choice(opts) in opts


class TestGenerateEmployees:
    def test_correct_count(self):
        assert len(generate_employees(100)) == 100

    def test_required_fields_present(self):
        required = [
            "id", "employee_id", "name", "email", "department", "job_title",
            "job_level", "employment_type", "country", "currency",
            "base_salary", "salary_usd", "hire_date", "created_at", "updated_at",
        ]
        for emp in generate_employees(5):
            for field in required:
                assert field in emp, f"Missing: {field}"

    def test_unique_emails(self):
        employees = generate_employees(500)
        emails = [e["email"] for e in employees]
        assert len(emails) == len(set(emails))

    def test_unique_employee_ids(self):
        employees = generate_employees(200)
        ids = [e["employee_id"] for e in employees]
        assert len(ids) == len(set(ids))

    def test_salary_usd_positive(self):
        for emp in generate_employees(200):
            assert emp["salary_usd"] > 0

    def test_base_salary_positive(self):
        for emp in generate_employees(100):
            assert emp["base_salary"] > 0

    def test_hire_dates_in_valid_range(self):
        from datetime import date
        for emp in generate_employees(100):
            d = date.fromisoformat(emp["hire_date"])
            assert date(2015, 1, 1) <= d <= date(2024, 12, 31)

    def test_departments_are_valid(self):
        valid = set(DEPARTMENTS.keys())
        for emp in generate_employees(200):
            assert emp["department"] in valid

    def test_countries_are_valid(self):
        valid = set(COUNTRIES.keys())
        for emp in generate_employees(200):
            assert emp["country"] in valid

    def test_contractor_salary_premium(self):
        """Contractors earn ~20% more than FT — their average should be higher."""
        random.seed(42)
        emps = generate_employees(3000)
        ft = [e["salary_usd"] for e in emps if e["employment_type"] == "Full-time"]
        ct = [e["salary_usd"] for e in emps if e["employment_type"] == "Contractor"]
        assert ct and ft
        # Contractor average should be at least 5% above FT (level mix causes variance)
        assert (sum(ct) / len(ct)) > (sum(ft) / len(ft)) * 1.05

    def test_part_time_salary_lower(self):
        random.seed(42)
        emps = generate_employees(3000)
        ft = [e["salary_usd"] for e in emps if e["employment_type"] == "Full-time"]
        pt = [e["salary_usd"] for e in emps if e["employment_type"] == "Part-time"]
        assert pt and ft
        assert (sum(pt) / len(pt)) < (sum(ft) / len(ft))

    def test_deterministic_with_same_seed(self):
        random.seed(42)
        a = generate_employees(10)
        random.seed(42)
        b = generate_employees(10)
        assert [e["name"] for e in a] == [e["name"] for e in b]

    def test_currency_matches_country(self):
        from seed import COUNTRIES
        for emp in generate_employees(200):
            expected = COUNTRIES[emp["country"]]["currency"]
            assert emp["currency"] == expected

    def test_base_salary_reflects_fx(self):
        """base_salary should equal salary_usd * fx (within rounding)."""
        from seed import COUNTRIES
        for emp in generate_employees(50):
            fx = COUNTRIES[emp["country"]]["fx"]
            expected = round(emp["salary_usd"] * fx, 2)
            assert abs(emp["base_salary"] - expected) < 1.0
