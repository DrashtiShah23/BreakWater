# Breakwater upstream services

Controlled FastAPI test targets used to measure later edge behavior.
Not a real application backend.

## Surfaces

| Compose service | Env `SURFACE` | Data endpoints |
| --- | --- | --- |
| `upstream-api` | `api` | `GET /api/v1/items`, `GET /api/v2/items`, `GET /health` |
| `upstream-status` | `status` | `GET /api/v1/status`, `GET /health` |

Envoy host routing is **not** implemented here. Both services listen on
HTTP; later milestones will front them as `api.breakwater.local` and
`status.breakwater.local`.

## Health semantics

| Check | Meaning |
| --- | --- |
| Process accepts TCP | Process alive |
| `GET /live` → 200 | Process alive (ignores intentional unhealthy flag) |
| `GET /health` → 200/503 | Application ready for Envoy active health checks; respects intentional unhealthy |

## Test controls (development/test only)

Mounted only when `ENABLE_TEST_CONTROLS=true` (default for local compose).
Set `ENABLE_TEST_CONTROLS=false` for AWS validation so `/__test__/*` is
absent (404).

Allowlisted operations only — no arbitrary code execution:

- `GET /__test__/state`
- `POST /__test__/latency` — capped artificial delay
- `POST /__test__/errors` — controlled 5xx modes
- `POST /__test__/health` — mark healthy / intentionally unhealthy
- `POST /__test__/reset` — recover defaults
- `POST /__test__/crash` — exit process after acknowledging (process failure)

## Local run

```bash
# from repository root
make up-upstream
# or without Docker:
cd services/upstream && python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
SURFACE=api ENABLE_TEST_CONTROLS=true uvicorn app.main:app --port 9001
```

## Tests

```bash
make test-upstream
```
