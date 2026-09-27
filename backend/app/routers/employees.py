"""
Employee routes:
  GET  /employees            — paginated, filtered, sorted list
  GET  /employees/export     — CSV download
  GET  /employees/{id}       — single employee + salary history
  PUT  /employees/{id}/salary — update salary with audit record
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ..database import get_db
from ..schemas import (
    EmployeeDetailResponse,
    EmployeeDetail,
    EmployeeRow,
    PaginatedEmployees,
    SalaryHistoryRow,
    SalaryUpdateRequest,
    SalaryUpdateResponse,
)

router = APIRouter(prefix="/employees", tags=["Employees"])

# Columns safe to sort by (whitelist against injection)
SORT_WHITELIST = frozenset({
    "name", "employee_id", "department", "country",
    "job_level", "salary_usd", "base_salary", "hire_date",
})


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _build_filters(
    search: str,
    department: str,
    country: str,
    job_level: str,
    employment_type: str,
    currency: str,
    salary_min: Optional[float],
    salary_max: Optional[float],
) -> tuple[str, list]:
    clauses, params = [], []

    if search:
        clauses.append("(name LIKE ? OR employee_id LIKE ? OR email LIKE ?)")
        p = f"%{search}%"
        params += [p, p, p]

    for col, val in [
        ("department", department),
        ("country", country),
        ("job_level", job_level),
        ("employment_type", employment_type),
        ("currency", currency),
    ]:
        if val:
            clauses.append(f"{col} = ?")
            params.append(val)

    if salary_min is not None:
        clauses.append("salary_usd >= ?")
        params.append(salary_min)
    if salary_max is not None:
        clauses.append("salary_usd <= ?")
        params.append(salary_max)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params


# List employees

@router.get("", response_model=PaginatedEmployees, summary="List employees")
async def list_employees(
    page:             int   = Query(default=1,   ge=1),
    page_size:        int   = Query(default=50,  ge=1, le=200),
    sort_by:          str   = Query(default="name"),
    sort_dir:         Literal["asc", "desc"] = Query(default="asc"),
    search:           str   = Query(default=""),
    department:       str   = Query(default=""),
    country:          str   = Query(default=""),
    job_level:        str   = Query(default=""),
    employment_type:  str   = Query(default=""),
    currency:         str   = Query(default=""),
    salary_min: Optional[float] = Query(default=None, ge=0),
    salary_max: Optional[float] = Query(default=None, ge=0),
    db=Depends(get_db),
):
    # Sanitise sort column
    safe_sort = sort_by if sort_by in SORT_WHITELIST else "name"
    direction = "DESC" if sort_dir == "desc" else "ASC"

    where, params = _build_filters(
        search, department, country, job_level,
        employment_type, currency, salary_min, salary_max,
    )

    # Total count
    count_cur = await db.execute(
        f"SELECT COUNT(*) AS total FROM employees {where}", params
    )
    total = (await count_cur.fetchone())["total"]

    # Paginated data
    offset = (page - 1) * page_size
    data_cur = await db.execute(
        f"""
        SELECT id, employee_id, name, email, department, job_title, job_level,
               employment_type, country, currency, base_salary, salary_usd,
               hire_date, updated_at
        FROM employees
        {where}
        ORDER BY {safe_sort} {direction}
        LIMIT ? OFFSET ?
        """,
        params + [page_size, offset],
    )
    rows = await data_cur.fetchall()

    return PaginatedEmployees(
        data=[EmployeeRow(**dict(r)) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=max(1, (total + page_size - 1) // page_size),
    )


# Export CSV

@router.get("/export", summary="Export filtered employees as CSV")
async def export_employees(
    search:          str   = Query(default=""),
    department:      str   = Query(default=""),
    country:         str   = Query(default=""),
    job_level:       str   = Query(default=""),
    employment_type: str   = Query(default=""),
    currency:        str   = Query(default=""),
    salary_min: Optional[float] = Query(default=None, ge=0),
    salary_max: Optional[float] = Query(default=None, ge=0),
    db=Depends(get_db),
):
    where, params = _build_filters(
        search, department, country, job_level,
        employment_type, currency, salary_min, salary_max,
    )
    cursor = await db.execute(
        f"""
        SELECT employee_id, name, email, department, job_title, job_level,
               employment_type, country, currency, base_salary, salary_usd, hire_date
        FROM employees {where} ORDER BY name ASC
        """,
        params,
    )
    rows = await cursor.fetchall()

    output = io.StringIO()
    fields = [
        "employee_id", "name", "email", "department", "job_title", "job_level",
        "employment_type", "country", "currency", "base_salary", "salary_usd", "hire_date",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        writer.writerow(dict(row))

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employees.csv"},
    )


# Get single employee

@router.get("/{emp_id}", response_model=EmployeeDetailResponse, summary="Get employee detail")
async def get_employee(emp_id: str, db=Depends(get_db)):
    emp_cur = await db.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    emp = await emp_cur.fetchone()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    hist_cur = await db.execute(
        "SELECT * FROM salary_history WHERE employee_id = ? ORDER BY changed_at DESC",
        (emp_id,),
    )
    history = await hist_cur.fetchall()

    return EmployeeDetailResponse(
        employee=EmployeeDetail(**dict(emp)),
        history=[SalaryHistoryRow(**dict(h)) for h in history],
    )


# Update salary

@router.put(
    "/{emp_id}/salary",
    response_model=SalaryUpdateResponse,
    summary="Update employee salary",
)
async def update_salary(
    emp_id: str,
    body: SalaryUpdateRequest,
    db=Depends(get_db),
):
    emp_cur = await db.execute("SELECT * FROM employees WHERE id = ?", (emp_id,))
    emp = await emp_cur.fetchone()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    old_salary = emp["base_salary"]
    old_usd    = emp["salary_usd"]
    currency   = emp["currency"]

    # Re-derive FX from stored values (avoids live API dependency)
    fx = (old_usd / old_salary) if old_salary else 1.0
    new_usd = round(body.new_salary * fx, 2)
    ts = _now()

    await db.execute(
        "UPDATE employees SET base_salary = ?, salary_usd = ?, updated_at = ? WHERE id = ?",
        (round(body.new_salary, 2), new_usd, ts, emp_id),
    )
    await db.execute(
        """INSERT INTO salary_history
           (id, employee_id, old_salary, new_salary, currency, changed_at, changed_by, reason)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            str(uuid.uuid4()), emp_id, old_salary,
            round(body.new_salary, 2), currency, ts,
            body.changed_by, body.reason,
        ),
    )
    await db.commit()

    return SalaryUpdateResponse(
        success=True,
        new_salary=round(body.new_salary, 2),
        new_salary_usd=new_usd,
    )
