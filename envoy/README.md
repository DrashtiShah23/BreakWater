# Envoy edge configuration

Milestone 5: **host + path routing** with TLS termination at Envoy.

| Listener | Port | Host bind (compose) | Role |
| --- | --- | --- | --- |
| `listener_https_data` | 8443 | all interfaces | **Data traffic** — HTTPS; TLS terminates here |
| `listener_http_debug` | 8080 | `127.0.0.1` | Local plaintext debug; same routing; not public |
| `admin` | 9901 | `127.0.0.1` | **Control** — Envoy admin |

## Traffic path

```text
Client --HTTPS--> Envoy:8443 --HTTP--> upstream-api | upstream-status
                 (Host selects cluster)
```

Routing contract: [`docs/routing_table.md`](../docs/routing_table.md).

`/__test__/*` is **not** routed through Envoy. Use upstream ports directly.

Rate-limit route class (standard/sensitive) is **not** assigned by hostname.

## Validate / run

```bash
make certs
make validate-envoy
make up
make smoke
make test-integration
```
