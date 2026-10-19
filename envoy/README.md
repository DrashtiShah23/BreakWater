# Envoy edge configuration

Milestone 6: TLS + host/path routing + **active health checks**, explicit
timeouts, and **bounded transport-only retries**.

| Listener | Port | Host bind | Role |
| --- | --- | --- | --- |
| `listener_https_data` | 8443 | all interfaces | Data (HTTPS; TLS ends here) |
| `listener_http_debug` | 8080 | `127.0.0.1` | Local plaintext debug |
| `admin` | 9901 | `127.0.0.1` | Control / cluster health |

## Reliability policy (summary)

| Concern | Setting |
| --- | --- |
| Active HC | `GET /health` every 2s; remove after 2 failures |
| Connect timeout | 1s |
| Items route timeout | 3s (`per_try_timeout` 1s) |
| Retries | GET items only: `connect-failure,refused-stream,reset`; `num_retries=2`; ~20% retry budget |
| Not retried | HTTP 5xx / 429 / edge 404s |

Details: `docs/adr/0006-retry-timeout-health.md`, `docs/failure_model.md`.

## Validate / run

```bash
make certs && make validate-envoy && make up && make smoke && make test-integration
./scripts/inject_failure.sh unhealthy api-2
curl -s http://127.0.0.1:9901/clusters | grep health
```
