"""
Seed script: generates 10,000 realistic employees.

Run with:
    python seed.py              # 10,000 employees
    python seed.py --count 100  # quick test
"""

import random
import uuid
import sys
import os
import asyncio
import argparse
import aiosqlite
from datetime import date, timedelta

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "salary.db"))

SCHEMA = """
PRAGMA journal_mode = WAL;
CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY, employee_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,
    department TEXT NOT NULL, job_title TEXT NOT NULL,
    job_level TEXT NOT NULL, employment_type TEXT NOT NULL DEFAULT 'Full-time',
    country TEXT NOT NULL, currency TEXT NOT NULL DEFAULT 'USD',
    base_salary REAL NOT NULL, salary_usd REAL NOT NULL,
    hire_date TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS salary_history (
    id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    old_salary REAL NOT NULL, new_salary REAL NOT NULL, currency TEXT NOT NULL,
    changed_at TEXT NOT NULL, changed_by TEXT NOT NULL DEFAULT 'HR Manager',
    reason TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);
CREATE INDEX IF NOT EXISTS idx_employees_country     ON employees(country);
CREATE INDEX IF NOT EXISTS idx_employees_job_level   ON employees(job_level);
CREATE INDEX IF NOT EXISTS idx_employees_name        ON employees(name);
CREATE INDEX IF NOT EXISTS idx_history_employee_id   ON salary_history(employee_id);
"""

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

DEPARTMENTS = {
    "Engineering": 0.28, "Product": 0.08, "Sales": 0.15,
    "Marketing": 0.07, "Finance": 0.06, "Human Resources": 0.05,
    "Operations": 0.09, "Customer Success": 0.08, "Legal": 0.03,
    "Data & Analytics": 0.06, "Design": 0.05,
}

COUNTRIES = {
    "United States":  {"currency": "USD", "fx": 1.00,  "weight": 0.35},
    "India":          {"currency": "INR", "fx": 83.5,  "weight": 0.20},
    "United Kingdom": {"currency": "GBP", "fx": 0.79,  "weight": 0.10},
    "Germany":        {"currency": "EUR", "fx": 0.92,  "weight": 0.08},
    "Canada":         {"currency": "CAD", "fx": 1.36,  "weight": 0.06},
    "Australia":      {"currency": "AUD", "fx": 1.53,  "weight": 0.05},
    "Singapore":      {"currency": "SGD", "fx": 1.35,  "weight": 0.04},
    "Brazil":         {"currency": "BRL", "fx": 5.10,  "weight": 0.04},
    "France":         {"currency": "EUR", "fx": 0.92,  "weight": 0.04},
    "Japan":          {"currency": "JPY", "fx": 149.5, "weight": 0.02},
    "Netherlands":    {"currency": "EUR", "fx": 0.92,  "weight": 0.02},
}

JOB_LEVELS = {
    "IC1": (45_000, 70_000),   "IC2": (65_000, 95_000),
    "IC3": (90_000, 130_000),  "IC4": (120_000, 170_000),
    "IC5": (160_000, 220_000), "IC6": (200_000, 300_000),
    "M1":  (110_000, 160_000), "M2":  (150_000, 200_000),
    "M3":  (190_000, 260_000), "M4":  (240_000, 350_000),
}

LEVEL_WEIGHTS = {
    "IC1": 0.12, "IC2": 0.18, "IC3": 0.22, "IC4": 0.18,
    "IC5": 0.10, "IC6": 0.04,
    "M1":  0.08, "M2":  0.05, "M3":  0.02, "M4":  0.01,
}

EMPLOYMENT_TYPES = {"Full-time": 0.82, "Contractor": 0.12, "Part-time": 0.06}

DEPT_TITLES = {
    "Engineering":      ["Software Engineer", "Senior Software Engineer", "Staff Engineer",
                         "Principal Engineer", "Engineering Manager", "Senior Engineering Manager",
                         "Backend Engineer", "Frontend Engineer", "Platform Engineer", "SRE"],
    "Product":          ["Product Manager", "Senior Product Manager", "Principal Product Manager",
                         "Director of Product", "Group Product Manager"],
    "Sales":            ["Account Executive", "Senior Account Executive", "Enterprise AE",
                         "Sales Manager", "Regional Sales Director", "Solutions Engineer"],
    "Marketing":        ["Marketing Manager", "Senior Marketing Manager", "Content Strategist",
                         "Growth Marketing Manager", "Brand Manager"],
    "Finance":          ["Financial Analyst", "Senior Financial Analyst", "Finance Manager",
                         "Controller", "VP Finance"],
    "Human Resources":  ["HR Business Partner", "Senior HRBP", "Recruiter", "HR Manager",
                         "Director of HR"],
    "Operations":       ["Operations Manager", "Senior Operations Manager", "Program Manager",
                         "Director of Operations"],
    "Customer Success": ["Customer Success Manager", "Senior CSM", "Enterprise CSM",
                         "Director of Customer Success"],
    "Legal":            ["Legal Counsel", "Senior Legal Counsel", "Corporate Counsel",
                         "Head of Legal"],
    "Data & Analytics": ["Data Analyst", "Senior Data Analyst", "Data Scientist",
                         "Senior Data Scientist", "Data Engineer", "Analytics Manager"],
    "Design":           ["Product Designer", "Senior Product Designer", "UX Researcher",
                         "Design Manager", "Staff Designer"],
}

FIRST_NAMES = [
    "James","Emma","Oliver","Ava","William","Sophia","Benjamin","Isabella","Lucas","Mia",
    "Henry","Charlotte","Alexander","Amelia","Mason","Evelyn","Ethan","Abigail","Daniel","Harper",
    "Raj","Priya","Arjun","Ananya","Vikram","Neha","Rohit","Divya","Wei","Li","Ming","Fang",
    "Mohammed","Fatima","Ahmed","Leila","Omar","Nadia","Hassan","Sara","Carlos","Maria",
    "Alejandro","Carmen","Diego","Valentina","Lars","Ingrid","Erik","Astrid","Yuki","Hana",
    "Kenji","Akiko","Kwame","Abena","Kofi","Akosua","Luca","Giulia","Marco","Francesca",
    "Noah","Grace","Liam","Chloe","Elijah","Lily","David","Sarah","Michael","Jennifer",
    "Ryan","Stephanie","Nicholas","Nicole","Tyler","Amanda","Andrew","Melissa","Patrick","Rachel",
    "Nguyen","Tran","Pham","Hoang","Lan","Hoa","Linh","Kevin","Brian","Lauren","Jonathan","Kelly",
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis","Wilson","Anderson",
    "Taylor","Thomas","Jackson","White","Harris","Martin","Thompson","Young","Allen","King",
    "Patel","Sharma","Singh","Kumar","Gupta","Mehta","Shah","Zhang","Wang","Li","Liu","Chen",
    "Kim","Lee","Park","Choi","Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Perez",
    "Müller","Schmidt","Schneider","Fischer","Weber","Johansson","Andersson","Nilsson","Karlsson",
    "Tanaka","Suzuki","Sato","Watanabe","Yamamoto","Nakamura","Nguyen","Tran","Le","Pham",
    "Ferrari","Rossi","Bianchi","Russo","Osei","Mensah","Asante","Boateng","Owusu","Darko",
    "O'Brien","Murphy","McCarthy","Walsh","Kelly","Ryan","Sullivan","Ibrahim","Hassan","Ali",
    "Scott","Green","Baker","Adams","Nelson","Carter","Mitchell","Perez","Roberts","Turner",
]


def _weighted_choice(options: dict) -> str:
    keys = list(options.keys())
    weights = list(options.values())
    return random.choices(keys, weights=weights, k=1)[0]


def _gen_employee_id(n: int) -> str:
    return f"ACME-{n:05d}"


def _gen_email(name: str, existing: set) -> str:
    parts = name.lower().split()
    base = "".join(c for c in f"{parts[0]}.{parts[-1]}" if c.isascii() and (c.isalpha() or c == "."))
    email = f"{base}@acme.com"
    n = 1
    while email in existing:
        email = f"{base}{n}@acme.com"
        n += 1
    return email


def _gen_hire_date() -> str:
    start = date(2015, 1, 1)
    delta = (date(2024, 12, 31) - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def generate_employees(count: int = 10_000) -> list[dict]:
    employees = []
    existing_emails: set = set()
    dept_keys  = list(DEPARTMENTS.keys())
    dept_w     = list(DEPARTMENTS.values())
    country_keys = list(COUNTRIES.keys())
    country_w    = [COUNTRIES[c]["weight"] for c in country_keys]
    level_keys   = list(LEVEL_WEIGHTS.keys())
    level_w      = list(LEVEL_WEIGHTS.values())
    emp_keys     = list(EMPLOYMENT_TYPES.keys())
    emp_w        = list(EMPLOYMENT_TYPES.values())

    now = "2026-09-27T00:13:30"

    for i in range(1, count + 1):
        first  = random.choice(FIRST_NAMES)
        last   = random.choice(LAST_NAMES)
        name   = f"{first} {last}"
        dept   = random.choices(dept_keys, weights=dept_w, k=1)[0]
        country = random.choices(country_keys, weights=country_w, k=1)[0]
        level  = random.choices(level_keys, weights=level_w, k=1)[0]
        emp_type = random.choices(emp_keys, weights=emp_w, k=1)[0]
        title  = random.choice(DEPT_TITLES[dept])

        currency = COUNTRIES[country]["currency"]
        fx       = COUNTRIES[country]["fx"]
        sal_min, sal_max = JOB_LEVELS[level]
        salary_usd = round(random.uniform(sal_min, sal_max), 2)
        if emp_type == "Contractor":
            salary_usd *= 1.20
        elif emp_type == "Part-time":
            salary_usd *= 0.60
        salary_usd  = round(salary_usd, 2)
        base_salary = round(salary_usd * fx, 2)

        email = _gen_email(name, existing_emails)
        existing_emails.add(email)

        employees.append({
            "id":              str(uuid.uuid4()),
            "employee_id":     _gen_employee_id(i),
            "name":            name,
            "email":           email,
            "department":      dept,
            "job_title":       title,
            "job_level":       level,
            "employment_type": emp_type,
            "country":         country,
            "currency":        currency,
            "base_salary":     base_salary,
            "salary_usd":      salary_usd,
            "hire_date":       _gen_hire_date(),
            "created_at":      now,
            "updated_at":      now,
        })

    return employees


async def seed(count: int = 10_000, batch_size: int = 500):
    employees = generate_employees(count)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.execute("DELETE FROM salary_history")
        await db.execute("DELETE FROM employees")
        await db.commit()

        for i in range(0, len(employees), batch_size):
            batch = employees[i: i + batch_size]
            await db.executemany(
                """INSERT INTO employees
                   (id, employee_id, name, email, department, job_title, job_level,
                    employment_type, country, currency, base_salary, salary_usd,
                    hire_date, created_at, updated_at)
                   VALUES
                   (:id,:employee_id,:name,:email,:department,:job_title,:job_level,
                    :employment_type,:country,:currency,:base_salary,:salary_usd,
                    :hire_date,:created_at,:updated_at)""",
                batch,
            )
            await db.commit()
            print(f"  Seeded {min(i + batch_size, count):,} / {count:,} employees")

    print(f"\n✓ Seeded {count:,} employees into {DB_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the salary database")
    parser.add_argument("--count", type=int, default=10_000)
    args = parser.parse_args()
    print(f"Seeding {args.count:,} employees …")
    asyncio.run(seed(args.count))
