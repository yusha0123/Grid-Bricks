"""FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Wind Power Analytics API",
    description=(
        "UK national wind generation forecasts (Elexon WINDFOR) vs actuals "
        "(Elexon FUELHH) for January 2026 delivery days."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {"message": "Wind Power Analytics API is running. See /docs."}
