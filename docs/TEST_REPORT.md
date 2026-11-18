# Test report (observed)
Environment: Python 3.12, SQLite in-memory, FakeLLM. Command: `pytest -q`.
Result: **30 passed, 1 skipped (live-stack smoke, needs E2E_BASE_URL), 0 failed, ~0.3 s.**

| Layer | Tests | Verifies |
|---|---|---|
| Unit | tools (8), classifier/router/json/memory (8) | tool validation, SQL-injection-shaped input rejected, window + session isolation |
| Integration | orchestrator (5), API (5) | multi-step run, guardrail, failure capture, memory across turns, 422/404 handling |
| E2E | 4 (+1 opt-in live) | API->queue->worker->agent->DB->API, failure persistence |

## Issues log
| # | Observation | Status |
|---|---|---|
| 1 | Not yet run: Postgres via docker compose, OpenAI-backed LLM path (no Docker/API key in build sandbox) | OPEN - run `make test` and `E2E_BASE_URL=... pytest` |
| 2 | FakeLLM is keyword-based; real-LLM routing accuracy is unmeasured | OPEN - add golden-set eval (Phase 3) |
| 3 | `create_all` instead of migrations | Phase 2 |
| 4 | Worker has no retry/backoff or stuck-`running` recovery | Phase 2 |
| 5 | No auth/rate limiting on endpoints | Phase 2 |
| 6 | httpx/starlette TestClient deprecation warning | cosmetic |
