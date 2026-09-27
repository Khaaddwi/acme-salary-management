"""
Analytics queries — all async, all read-only.
Each function accepts an aiosqlite connection so the caller controls the transaction.
"""

from __future__ import annotations
from typing import Any
import aiosqlite

from .schemas import (
    SummaryStats, DeptBreakdown, CountryBreakdown,
    LevelBreakdown, SalaryBand, EmploymentTypeBreakdown,
)


def _row_to_dict(row: Any) -> dict:
    """Safely convert an aiosqlite Row to a dict."""
    if row is None:
        return {}
    return dict(row)


async def get_summary_stats(db: aiosqlite.Connection) -> SummaryStats:
    cursor = await db.execute("""
        SELECT
            COUNT(*)                        AS total_employees,
            ROUND(SUM(salary_usd), 2)       AS total_payroll_usd,
            ROUND(AVG(salary_usd), 2)       AS avg_salary_usd,
            ROUND(MIN(salary_usd), 2)       AS min_salary_usd,
            ROUND(MAX(salary_usd), 2)       AS max_salary_usd,
            COUNT(DISTINCT department)      AS num_departments,
            COUNT(DISTINCT country)         AS num_countries
        FROM employees
    """)
    row = await cursor.fetchone()
    if row is None:
        raise RuntimeError("No data found — did you run seed.py?")
    return SummaryStats(**_row_to_dict(row))


async def get_dept_breakdown(db: aiosqlite.Connection) -> list[DeptBreakdown]:
    cursor = await db.execute("""
        SELECT
            department,
            COUNT(*)                        AS headcount,
            ROUND(AVG(salary_usd), 0)       AS avg_salary_usd,
            ROUND(MIN(salary_usd), 0)       AS min_salary_usd,
            ROUND(MAX(salary_usd), 0)       AS max_salary_usd,
            ROUND(SUM(salary_usd), 0)       AS total_payroll_usd
        FROM employees
        GROUP BY department
        ORDER BY total_payroll_usd DESC
    """)
    rows = await cursor.fetchall()
    return [DeptBreakdown(**_row_to_dict(r)) for r in rows]


async def get_country_breakdown(db: aiosqlite.Connection) -> list[CountryBreakdown]:
    cursor = await db.execute("""
        SELECT
            country,
            currency,
            COUNT(*)                    AS headcount,
            ROUND(AVG(salary_usd), 0)   AS avg_salary_usd,
            ROUND(SUM(salary_usd), 0)   AS total_payroll_usd
        FROM employees
        GROUP BY country
        ORDER BY headcount DESC
    """)
    rows = await cursor.fetchall()
    return [CountryBreakdown(**_row_to_dict(r)) for r in rows]


async def get_level_breakdown(db: aiosqlite.Connection) -> list[LevelBreakdown]:
    cursor = await db.execute("""
        SELECT
            job_level,
            COUNT(*)                    AS headcount,
            ROUND(AVG(salary_usd), 0)   AS avg_salary_usd,
            ROUND(MIN(salary_usd), 0)   AS min_salary_usd,
            ROUND(MAX(salary_usd), 0)   AS max_salary_usd
        FROM employees
        GROUP BY job_level
        ORDER BY avg_salary_usd DESC
    """)
    rows = await cursor.fetchall()
    return [LevelBreakdown(**_row_to_dict(r)) for r in rows]


async def get_salary_bands(db: aiosqlite.Connection) -> list[SalaryBand]:
    bands = [
        ("< $50k",        0,         50_000),
        ("$50k–$75k",     50_000,    75_000),
        ("$75k–$100k",    75_000,   100_000),
        ("$100k–$125k",  100_000,   125_000),
        ("$125k–$150k",  125_000,   150_000),
        ("$150k–$175k",  150_000,   175_000),
        ("$175k–$200k",  175_000,   200_000),
        ("$200k–$250k",  200_000,   250_000),
        ("> $250k",      250_000, 999_999_999),
    ]
    result = []
    for label, low, high in bands:
        cursor = await db.execute(
            "SELECT COUNT(*) AS count FROM employees WHERE salary_usd >= ? AND salary_usd < ?",
            (low, high),
        )
        row = await cursor.fetchone()
        count = _row_to_dict(row).get("count", 0)
        result.append(SalaryBand(band=label, count=count))
    return result


async def get_employment_type_breakdown(db: aiosqlite.Connection) -> list[EmploymentTypeBreakdown]:
    cursor = await db.execute("""
        SELECT
            employment_type,
            COUNT(*)                    AS headcount,
            ROUND(AVG(salary_usd), 0)   AS avg_salary_usd,
            ROUND(SUM(salary_usd), 0)   AS total_payroll_usd
        FROM employees
        GROUP BY employment_type
        ORDER BY headcount DESC
    """)
    rows = await cursor.fetchall()
    return [EmploymentTypeBreakdown(**_row_to_dict(r)) for r in rows]