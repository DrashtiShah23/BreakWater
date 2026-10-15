# Routing table

Contract for Breakwater Envoy host and path routing (Milestone 5).
TLS terminates at Envoy (`:8443`). Upstream hops remain HTTP on the
compose network.

## Hosts → upstream services

| Host (`Host` / `:authority`) | Upstream cluster | Compose service | Surface |
| --- | --- | --- | --- |
| `api.breakwater.local` | `upstream_api` | `upstream-api` | versioned items API |
| `status.breakwater.local` | `upstream_status` | `upstream-status` | small status surface |
| any other host | — | — | edge `404` `unknown_host` |

Host identity selects **which application** handles the request. It does
**not** assign rate-limit failure class (`standard` / `sensitive`). That
classification is a later per-route policy (Milestones 7–8) and must not
be inferred from hostname alone.

## Paths

### `api.breakwater.local`

| Method / path | Behavior |
| --- | --- |
| `GET /health` | Proxied to `upstream-api` (readiness) |
| `GET /live` | Proxied to `upstream-api` (liveness) |
| `GET /api/v1/items` | Proxied to `upstream-api` (v1 items) |
| `GET /api/v2/items` | Proxied to `upstream-api` (v2 items) |
| any other path | Edge `404` `unknown_path` |

### `status.breakwater.local`

| Method / path | Behavior |
| --- | --- |
| `GET /health` | Proxied to `upstream-status` |
| `GET /live` | Proxied to `upstream-status` |
| `GET /api/v1/status` | Proxied to `upstream-status` |
| any other path | Edge `404` `unknown_path` |

## Test-control isolation

`/__test__/*` is **not** part of the Envoy routing table.

Use direct upstream ports (local only, when `ENABLE_TEST_CONTROLS=true`):

| Target | Example |
| --- | --- |
| API controls | `http://127.0.0.1:9001/__test__/...` |
| Status controls | `http://127.0.0.1:9002/__test__/...` |

A request for `/__test__/…` through Envoy on a known host returns
`unknown_path` (404). On an unknown host it returns `unknown_host`.

## Listeners

| Listener | Port | Binding (compose) | Role |
| --- | --- | --- | --- |
| `listener_https_data` | 8443 | `0.0.0.0` | **Public data path** (TLS) |
| `listener_http_debug` | 8080 | `127.0.0.1` | Local plaintext debug; same routing contract |
| `admin` | 9901 | `127.0.0.1` | Control (not data traffic) |

## Local curl examples

```bash
# API v1 over HTTPS (SNI/Host via --resolve)
curl --cacert envoy/tls/ca.crt \
  --resolve api.breakwater.local:8443:127.0.0.1 \
  https://api.breakwater.local:8443/api/v1/items

# Status surface
curl --cacert envoy/tls/ca.crt \
  --resolve status.breakwater.local:8443:127.0.0.1 \
  https://status.breakwater.local:8443/api/v1/status

# Unknown host
curl --cacert envoy/tls/ca.crt \
  -H 'Host: other.example' \
  https://127.0.0.1:8443/api/v1/items
```

## Correlation and upstream identity

Envoy preserves / generates `x-request-id`. Upstream responses include
`instance_id`, `surface` / `api_version`, and `x-upstream-*` headers so
tests can prove which service handled the request.
