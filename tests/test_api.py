"""Tests for the FastAPI app (api.py)."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import api


def test_query_handler_is_sync_for_threadpool_offload():
    """#54 regression guard.

    The `/query` handler must be a plain ``def``, not ``async def``. A sync
    handler is run by FastAPI in its worker threadpool, so the blocking
    pipeline never occupies the event loop and ``/health`` stays responsive.
    If someone re-adds ``async``, the blocking call would freeze the whole
    server — this test catches that.
    """
    assert not asyncio.iscoroutinefunction(api.query)


def test_health_ok():
    client = TestClient(api.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_query_rejects_invalid_sub_slice():
    client = TestClient(api.app)
    resp = client.post(
        "/query",
        json={"brief": "a representative ten-plus char brief", "sub_slice": "nope"},
    )
    assert resp.status_code == 400
