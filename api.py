"""
Hindcast API server.
Victor's React frontend calls this at localhost:8000.
Single query endpoint: POST /query
"""

from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from pipeline.run import run_query

app = FastAPI(title="Hindcast API")

# Comma-separated allowed origins. Defaults to the local Vite dev server; on
# the host (Railway), set ALLOWED_ORIGINS to the deployed Netlify origin —
# e.g. "https://hindcast.netlify.app".
_allowed_origins = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    brief: str = Field(..., min_length=10, max_length=500)
    sub_slice: str


@app.post("/query")
def query(request: QueryRequest) -> dict:
    # Sync (not async) on purpose: run_query() is blocking (network I/O,
    # extraction, SQLite), so FastAPI runs this handler in its threadpool and
    # the event loop stays free to serve /health and overlap queries (#54).
    # Do NOT re-add `async` — see tests/test_api.py.
    if request.sub_slice not in [
        "sneaker_streetwear",
        "contemporary_fashion",
    ]:
        raise HTTPException(
            status_code=400,
            detail=("sub_slice must be 'sneaker_streetwear' or 'contemporary_fashion'"),
        )
    return run_query(brief=request.brief, sub_slice=request.sub_slice)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)  # nosec B104
