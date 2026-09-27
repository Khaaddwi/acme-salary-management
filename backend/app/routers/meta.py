"""
Meta route — filter dropdown values.
"""

from fastapi import APIRouter, Depends
from ..database import get_db
from ..schemas import FilterMeta

router = APIRouter(prefix="/meta", tags=["Meta"])


@router.get("/filters", response_model=FilterMeta, summary="Distinct values for filter dropdowns")
async def get_filters(db=Depends(get_db)):
    async def distinct(col: str) -> list[str]:
        cur = await db.execute(
            f"SELECT DISTINCT {col} FROM employees ORDER BY {col}"
        )
        return [r[0] for r in await cur.fetchall()]

    return FilterMeta(
        departments=await distinct("department"),
        countries=await distinct("country"),
        job_levels=await distinct("job_level"),
        currencies=await distinct("currency"),
        employment_types=await distinct("employment_type"),
    )
