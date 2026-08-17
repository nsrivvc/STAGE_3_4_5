"""
app.py
======
FastAPI application that impersonates NatGasHub for local development.

Run from the repository root:

    uvicorn src.mock_api.app:app --reload --host 0.0.0.0 --port 8000

Consumers point NATGASHUB_BASE_URL (e.g. http://localhost:8000) at this server
and call the /api/* endpoints below. Each endpoint returns the corresponding
/data fixture verbatim — this service never touches Neon/Postgres.

CORS origins for browser-based consumers default to common local dev ports and
can be overridden with a comma-separated MOCK_API_CORS_ORIGINS env var.
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .loader import load_fixture

_DEFAULT_CORS_ORIGINS = (
    "http://localhost:3000,http://localhost:5173,http://localhost:8080"
)

app = FastAPI(
    title="Mock NatGasHub API",
    description="Serves the JSON fixtures in /data as if it were NatGasHub.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv("MOCK_API_CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock-natgashub-api"}


@app.get("/api/firms")
def get_firms():
    return load_fixture("firms_test.json")


@app.get("/api/interruptibles")
def get_interruptibles():
    return load_fixture("interruptibles_test.json")


@app.get("/api/ioc")
def get_ioc():
    return load_fixture("ioc_test.json")


@app.get("/api/awards")
def get_awards():
    return load_fixture("awards_test.json")
