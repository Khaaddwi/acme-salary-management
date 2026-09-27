"""
Pydantic v2 models for request validation and response serialization.
FastAPI uses these for automatic OpenAPI docs and input validation.
"""

from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


# Employee

class EmployeeRow(BaseModel):
    """Single employee as returned from list/detail endpoints."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    name: str
    email: str
    department: str
    job_title: str
    job_level: str
    employment_type: str
    country: str
    currency: str
    base_salary: float
    salary_usd: float
    hire_date: str
    updated_at: str


class EmployeeDetail(EmployeeRow):
    """Full employee detail including all fields."""
    created_at: str


class SalaryHistoryRow(BaseModel):
    """One salary change event."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    employee_id: str
    old_salary: float
    new_salary: float
    currency: str
    changed_at: str
    changed_by: str
    reason: str


class EmployeeDetailResponse(BaseModel):
    """Response for GET /employees/{id}"""
    employee: EmployeeDetail
    history: list[SalaryHistoryRow]


# Paginated list

class PaginatedEmployees(BaseModel):
    data: list[EmployeeRow]
    total: int
    page: int
    page_size: int
    pages: int


# Salary update

class SalaryUpdateRequest(BaseModel):
    """Body for PUT /employees/{id}/salary"""
    new_salary: float = Field(..., gt=0, description="New salary in the employee's local currency")
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for salary change")
    changed_by: str = Field(default="HR Manager", max_length=100)

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("reason cannot be blank")
        return v.strip()

    @field_validator("changed_by")
    @classmethod
    def changed_by_not_empty(cls, v: str) -> str:
        return v.strip() or "HR Manager"


class SalaryUpdateResponse(BaseModel):
    success: bool
    new_salary: float
    new_salary_usd: float


# Analytics

class SummaryStats(BaseModel):
    total_employees: int
    total_payroll_usd: float
    avg_salary_usd: float
    min_salary_usd: float
    max_salary_usd: float
    num_departments: int
    num_countries: int


class DeptBreakdown(BaseModel):
    department: str
    headcount: int
    avg_salary_usd: float
    min_salary_usd: float
    max_salary_usd: float
    total_payroll_usd: float


class CountryBreakdown(BaseModel):
    country: str
    currency: str
    headcount: int
    avg_salary_usd: float
    total_payroll_usd: float


class LevelBreakdown(BaseModel):
    job_level: str
    headcount: int
    avg_salary_usd: float
    min_salary_usd: float
    max_salary_usd: float


class SalaryBand(BaseModel):
    band: str
    count: int


class EmploymentTypeBreakdown(BaseModel):
    employment_type: str
    headcount: int
    avg_salary_usd: float
    total_payroll_usd: float


# Filter metadata

class FilterMeta(BaseModel):
    departments: list[str]
    countries: list[str]
    job_levels: list[str]
    currencies: list[str]
    employment_types: list[str]


# AI Q&A

class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500)


class AskResponse(BaseModel):
    explanation: str
    results: list[dict]
    sql: str


# Error

class ErrorResponse(BaseModel):
    detail: str
