"""
Analytics routes — all GET, all read-only.
"""

from fastapi import APIRouter, Depends
from ..database import get_db
from ..analytics import (
    get_summary_stats,
    get_dept_breakdown,
    get_country_breakdown,
    get_level_breakdown,
    get_salary_bands,
    get_employment_type_breakdown,
)
from ..schemas import (
    SummaryStats, DeptBreakdown, CountryBreakdown,
    LevelBreakdown, SalaryBand, EmploymentTypeBreakdown,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", response_model=SummaryStats, summary="Top-line salary stats")
async def summary(db=Depends(get_db)):
    return await get_summary_stats(db)


@router.get("/departments", response_model=list[DeptBreakdown], summary="Breakdown by department")
async def departments(db=Depends(get_db)):
    return await get_dept_breakdown(db)


@router.get("/countries", response_model=list[CountryBreakdown], summary="Breakdown by country")
async def countries(db=Depends(get_db)):
    return await get_country_breakdown(db)


@router.get("/levels", response_model=list[LevelBreakdown], summary="Breakdown by job level")
async def levels(db=Depends(get_db)):
    return await get_level_breakdown(db)


@router.get("/bands", response_model=list[SalaryBand], summary="Salary band distribution")
async def bands(db=Depends(get_db)):
    return await get_salary_bands(db)


@router.get(
    "/employment-types",
    response_model=list[EmploymentTypeBreakdown],
    summary="Breakdown by employment type",
)
async def employment_types(db=Depends(get_db)):
    return await get_employment_type_breakdown(db)
