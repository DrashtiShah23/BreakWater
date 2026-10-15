# Envoy edge configuration

Milestone 3 introduces a **plaintext HTTP** reverse proxy only.

| Listener | Port | Role |
| --- | --- | --- |
| `listener_http_data` | 8080 | **Data traffic** — client requests to upstream API |
| `admin` | 9901 | **Control** — Envoy admin (stats/config); not client load |

## Traffic path (current)

```text
Client --HTTP--> Envoy:8080 --HTTP--> upstream-api:8000
```

- TLS termination: deferred to Milestone 4
- Host-based routing (`api` / `status`): deferred to Milestone 5
- Rate limiting / Redis: deferred to Milestones 7–8

`upstream-status` remains reachable directly on the host port (default 9002)
until host routing lands.

## Validate config (CI-friendly, zero cost)

```bash
make validate-envoy
```

Uses the pinned Envoy image with `--mode validate`. Does not provision AWS.

## Local run

```bash
make up
make smoke
make test-integration
```
