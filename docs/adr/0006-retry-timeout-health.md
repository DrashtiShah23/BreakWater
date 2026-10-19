# ADR 0006: Health checks, timeouts, and retry policy

- **Status:** Accepted
- **Date:** 2026-10-15

## Context

Milestone 6 requires active upstream health checking, explicit timeouts,
and a conservative retry policy. Blind retries on HTTP 5xx amplify load
during application failures. Retries on non-idempotent methods risk
duplicate side effects (none of our public Envoy routes are mutating
today, but the policy must stay safe as the surface grows).

## Decision

### Active health checks (control traffic)

- Probe: `GET /health` on each upstream endpoint
- Interval: 2s; timeout: 1s
- Unhealthy threshold: 2; healthy threshold: 2
- Expected success: HTTP 2xx
- Intentional upstream unhealthy (`/health` → 503) removes the endpoint
  from load balancing without requiring process death
- Compose runs two `upstream_api` endpoints so removal is observable

Health checks are **control traffic**, not client data-plane load.

### Timeouts

| Scope | Value | Rationale |
| --- | --- | --- |
| Cluster `connect_timeout` | 1s | Fail fast on dead sockets |
| Route timeout (items) | 3s | Bound client wait; not a benchmark target |
| Route timeout (health/live/status) | 2s | Short control/data probes |
| `per_try_timeout` (retried routes) | 1s | Cap each attempt under the route timeout |

### Retries (data traffic, bounded)

Apply only to **GET** `/api/v1/items` and `/api/v2/items`:

- `retry_on`: `connect-failure,refused-stream,reset`
- **Not** retried: HTTP 5xx, 429, timeouts as application success/failure,
  unknown host/path (edge direct responses)
- `num_retries`: 2 (at most 3 attempts)
- Short exponential backoff (50ms base, 250ms max)
- Cluster `retry_budget` ≈ 20% to limit amplification under concurrency

Do **not** attach retry policies to `/health` or `/live` routes.

### Amplification risk

Retrying every upstream 5xx would multiply load exactly when the app is
sick. Transport-only retries recover from brief connection loss without
turning one bad response into N identical errors.

## Consequences

- Tests must show HC removal via instance identity / admin clusters, not
  only YAML inspection.
- Injected HTTP 5xx remains visible as a single attempt.
- Slow upstream past route timeout yields gateway timeout without
  inventing performance numbers.
