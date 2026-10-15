# Envoy edge configuration

Milestone 4: **TLS terminates at Envoy**. Upstream remains HTTP on the
compose network.

| Listener | Port | Role |
| --- | --- | --- |
| `listener_https_data` | 8443 | **Data traffic** — client HTTPS; TLS terminates here |
| `listener_http_debug` | 8080 | Optional plaintext debug only (not the intended demo path) |
| `admin` | 9901 | **Control** — Envoy admin; host-bound to 127.0.0.1 |

## Traffic path (current)

```text
Client --HTTPS--> Envoy:8443 --HTTP--> upstream-api:8000
```

Development certificates: see `tls/README.md` and `scripts/generate_local_certs.sh`.

Still deferred: host routing (M5), rate limiting (M7–8), Prometheus (M9).

## Validate config (CI-friendly, zero cost)

```bash
make certs           # local only; keys are gitignored
make validate-envoy
```

## Local run

```bash
make certs
make up
make smoke
make test-integration
```
