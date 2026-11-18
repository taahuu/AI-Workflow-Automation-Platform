"""Smoke test against a running compose stack: E2E_BASE_URL=http://localhost:8000 pytest tests/e2e/test_live_stack.py"""
import os
import time

import httpx
import pytest

BASE = os.environ.get("E2E_BASE_URL")
pytestmark = pytest.mark.skipif(not BASE, reason="E2E_BASE_URL not set")


def test_live_async_run_completes_via_worker():
    c = httpx.Client(base_url=BASE, timeout=10)
    assert c.get("/health").json()["status"] == "ok"
    rid = c.post("/api/v1/workflows/runs", json={"session_id": "live", "message": "show pending orders"}).json()["run_id"]
    for _ in range(30):
        r = c.get(f"/api/v1/workflows/runs/{rid}").json()
        if r["status"] not in ("queued", "running"):
            break
        time.sleep(1)
    assert r["status"] == "completed"
