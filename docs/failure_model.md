# Failure model (Milestone 6)

Breakwater is intentionally breakable. This document describes **current**
edge behavior for health, timeouts, and retries. It does not invent
throughput or latency claims.

## Control vs data

| Class | Examples |
| --- | --- |
| **Data traffic** | Client HTTPS to `/api/v1/items`, `/api/v2/items`, `/api/v1/status` |
| **Control traffic** | Envoy active health checks (`GET /health`), admin `:9901`, direct `/__test__/*` |

Active health checks are **not** counted as client load.

## Active health checking

Envoy probes each upstream endpoint with `GET /health` every 2s
(timeout 1s). After 2 consecutive failures the endpoint is removed from
load balancing; after 2 consecutive successes it returns.

| Upstream state | `/health` | Effect on data traffic |
| --- | --- | --- |
| Healthy | 200 | Eligible for LB |
| Intentionally unhealthy | 503 | Removed after HC failures |
| Process stopped | connection fail | Removed after HC failures |
| Injected HTTP 5xx on **data** paths only | `/health` still 200 | Endpoint **stays** eligible; clients see 5xx |

That last row is how tests distinguish **active HC removal** from
**ordinary request failure**.

`upstream_api` has two members (`api-1`, `api-2`) so removal is visible
via `instance_id` / `x-upstream-instance` without AWS.

## Timeouts

| Scope | Value |
| --- | --- |
| Connect | 1s |
| Items routes | 3s (per-try 1s when retrying) |
| Health / live / status routes | 2s |

Injected latency above the route timeout yields a gateway timeout to the
client (exact status depends on Envoy flags; tests assert timeout-class
failure, not a resume number).

## Retries

Only **GET** `/api/v1/items` and `/api/v2/items`:

| Retried | Not retried |
| --- | --- |
| `connect-failure`, `refused-stream`, `reset` | HTTP 5xx, 429, edge 404s, non-GET (none exposed) |

- Max `num_retries`: 2
- Cluster retry budget ≈ 20%
- No retry policy on `/health` or `/live`

See `docs/adr/0006-retry-timeout-health.md`.

## Recovery

Clear intentional unhealthy (`POST /__test__/health {"healthy":true}` or
`/__test__/reset`) or restart a stopped container. After healthy
threshold is met, the endpoint receives traffic again — no Envoy config
rewrite.

## Helpers

```bash
./scripts/inject_failure.sh unhealthy api-2
./scripts/inject_failure.sh healthy api-2
./scripts/inject_failure.sh latency api-1 4000
./scripts/inject_failure.sh errors api-1 http_500 3
./scripts/inject_failure.sh stop upstream-api-2
./scripts/inject_failure.sh start upstream-api-2
```

Inspect Envoy cluster health: `curl -s http://127.0.0.1:9901/clusters | grep health`.
