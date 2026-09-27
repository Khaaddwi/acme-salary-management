"""
AI Q&A route — converts natural language HR questions to SQL using Groq,
executes read-only SQL against SQLite, and returns results.

Requires: GROQ_API_KEY environment variable
Get free key at: console.groq.com
"""

from __future__ import annotations

import json
import os

from fastapi import APIRouter, Depends, HTTPException
from groq import AsyncGroq, APIConnectionError, APIStatusError

from ..database import get_db
from ..schemas import AskRequest, AskResponse


router = APIRouter(
    prefix="/ask",
    tags=["AI Q&A"],
)


GROQ_MODEL = "openai/gpt-oss-20b"


SCHEMA_CONTEXT = """
You are an expert SQL analyst for ACME's HR database.

The SQLite database has:

employees (
  id TEXT,
  employee_id TEXT,
  name TEXT,
  email TEXT,
  department TEXT,
  job_title TEXT,
  job_level TEXT,             -- IC1, IC2, IC3, IC4, IC5, IC6, M1, M2, M3, M4
  employment_type TEXT,       -- Full-time, Part-time, Contractor
  country TEXT,
  currency TEXT,
  base_salary REAL,           -- local currency
  salary_usd REAL,            -- USD equivalent
  hire_date TEXT,
  created_at TEXT,
  updated_at TEXT
)

salary_history (
  id TEXT,
  employee_id TEXT,
  old_salary REAL,
  new_salary REAL,
  currency TEXT,
  changed_at TEXT,
  changed_by TEXT,
  reason TEXT
)

Rules:
- Always use salary_usd for salary comparisons.
- Return ONLY a valid JSON object.
- Do not return markdown or backticks.
- Response format:
  {"sql": "<SELECT statement>", "explanation": "<plain English explanation>"}
- SQL must be SELECT only.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or other DDL.
- Use LIMIT 50 for row queries unless asked for more.
- Aggregate queries like COUNT, AVG, MIN, MAX, and SUM do not need LIMIT.
"""


@router.post(
    "",
    response_model=AskResponse,
    summary="Ask a natural language question about salary data",
)
async def ask(
    body: AskRequest,
    db=Depends(get_db),
):
    # Get Groq API key
    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "GROQ_API_KEY not configured. "
                "Get a free key at console.groq.com"
            ),
        )

    # Create async Groq client
    client = AsyncGroq(
        api_key=api_key,
    )

    # Ask Groq to convert question into SQL
    try:
        completion = await client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": SCHEMA_CONTEXT,
                },
                {
                    "role": "user",
                    "content": body.question,
                },
            ],
            temperature=0,
            max_tokens=1000,
        )

    except APIStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Groq API error {e.status_code}: "
                f"{e.response.text}"
            ),
        )

    except APIConnectionError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Groq connection error: {str(e)}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Groq error: {str(e)}",
        )

    # Extract model response
    text = completion.choices[0].message.content or ""
    text = text.strip()

    # Remove markdown fences if model adds them
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])

    if text.endswith("```"):
        text = text[:text.rfind("```")]

    # Convert Groq response to JSON
    try:
        ai_data = json.loads(text.strip())

    except json.JSONDecodeError:
        return AskResponse(
            explanation=text,
            results=[],
            sql="",
        )

    sql = ai_data.get("sql", "").strip()
    explanation = ai_data.get("explanation", "").strip()

    # Safety check
    if not sql.upper().startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail=(
                "AI returned a non-SELECT statement "
                "— blocked for safety."
            ),
        )

    # Prevent multiple SQL statements
    cleaned_sql = sql.rstrip(";").strip()

    if ";" in cleaned_sql:
        raise HTTPException(
            status_code=400,
            detail="Multiple SQL statements are not allowed.",
        )

    # Execute SQL as read-only
    try:
        await db.execute(
            "PRAGMA query_only = ON"
        )

        cursor = await db.execute(
            cleaned_sql
        )

        rows = await cursor.fetchall()

        results = [
            {
                key: row[key]
                for key in row.keys()
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SQL error: {str(e)}",
        )

    return AskResponse(
        explanation=explanation,
        results=results,
        sql=cleaned_sql,
    )