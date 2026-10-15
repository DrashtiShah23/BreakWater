# Envoy TLS material (development only)

**These certificates are development certificates and are not production
credentials.** Do not use them outside local Compose demos.

## Generate locally

```bash
make certs
# or: ./scripts/generate_local_certs.sh
```

Creates (all **gitignored**):

| File | Role |
| --- | --- |
| `ca.crt` | Local Dev CA — clients must trust this to verify Envoy |
| `ca.key` | CA private key — **never commit** |
| `server.crt` | Certificate Envoy presents on `:8443` |
| `server.key` | Server private key — **never commit** |

SANs include `localhost`, `127.0.0.1`, `api.breakwater.local`, and
`status.breakwater.local` (hosts used later for routing demos).

## Where TLS terminates

```text
Client --HTTPS--> Envoy :8443  (TLS terminates HERE)
                 --HTTP--> upstream-api :8000  (compose network, plaintext)
```

TLS is **not** terminated in the FastAPI upstream. Upstream remains HTTP
so edge vs application latency and failures stay separable.

Envoy admin (`:9901`) stays plaintext and host-bound to `127.0.0.1` —
control traffic, not public data traffic.

## Client verification example

```bash
curl --cacert envoy/tls/ca.crt https://127.0.0.1:8443/api/v1/items
```

Without trusting `ca.crt`, verification fails (expected for an untrusted
dev CA).

## Production / optional AWS note

Production would use a real CA (or ACM with TCP passthrough to Envoy so
Envoy still terminates TLS). Internal mTLS between Envoy and upstreams
could be added later by configuring an upstream `UpstreamTlsContext`;
it is intentionally out of scope for Milestone 4.

See `docs/adr/0004-tls-termination-placement.md`.
