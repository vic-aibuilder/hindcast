"""
Hindcast API server.
Victor's React frontend calls this at localhost:8000.
Single query endpoint: POST /query
"""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from pipeline.run import run_query

app = FastAPI(title="Hindcast API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    brief: str
    sub_slice: str


@app.post("/query")
async def query(request: QueryRequest) -> dict:
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
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104
