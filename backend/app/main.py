"""
ACME Salary Management System — FastAPI application.

Start with:
    uvicorn app.main:app --reload --port 8000

API docs auto-generated at:
    http://localhost:8000/docs      (Swagger UI)
    http://localhost:8000/redoc     (ReDoc)
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routers import analytics, employees, ask, meta

from dotenv import load_dotenv
load_dotenv()


# Lifespan: init DB on startup

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


# App

app = FastAPI(
    title="ACME Salary Management API",
    description=(
        "HR salary management for 10,000 employees across multiple countries.\n\n"
        "Provides employee CRUD, salary history, analytics dashboards, CSV export, "
        "and AI-powered natural language Q&A."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes

app.include_router(employees.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(meta.router, prefix="/api")
app.include_router(ask.router, prefix="/api")

# Static frontend

STATIC_DIR = Path(__file__).parent.parent / "static"

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_frontend():
        return FileResponse(str(STATIC_DIR / "index.html"))
