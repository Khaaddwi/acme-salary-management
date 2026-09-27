"""
Database layer: async SQLite via aiosqlite.
All schema, connection helpers, and init logic live here.
"""

import os
import aiosqlite

DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "..", "salary.db"))

SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS employees (
    id              TEXT PRIMARY KEY,
    employee_id     TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    department      TEXT NOT NULL,
    job_title       TEXT NOT NULL,
    job_level       TEXT NOT NULL,
    employment_type TEXT NOT NULL DEFAULT 'Full-time',
    country         TEXT NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'USD',
    base_salary     REAL NOT NULL,
    salary_usd      REAL NOT NULL,
    hire_date       TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS salary_history (
    id          TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    old_salary  REAL NOT NULL,
    new_salary  REAL NOT NULL,
    currency    TEXT NOT NULL,
    changed_at  TEXT NOT NULL,
    changed_by  TEXT NOT NULL DEFAULT 'HR Manager',
    reason      TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);
CREATE INDEX IF NOT EXISTS idx_employees_country     ON employees(country);
CREATE INDEX IF NOT EXISTS idx_employees_job_level   ON employees(job_level);
CREATE INDEX IF NOT EXISTS idx_employees_name        ON employees(name);
CREATE INDEX IF NOT EXISTS idx_history_employee_id   ON salary_history(employee_id);
"""


async def get_db():
    """Async context manager that yields a configured aiosqlite connection."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA journal_mode = WAL")
        yield db


async def init_db() -> None:
    """Create tables and indexes if they don't already exist."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()
