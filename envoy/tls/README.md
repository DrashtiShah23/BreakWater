# Envoy TLS material

Development certificates are generated locally in Milestone 4 via
`scripts/generate_local_certs.sh`.

**Do not commit private keys or certificates.** This directory’s key
material is gitignored.

TLS terminates at Envoy (see `docs/adr/0004-tls-termination-placement.md`).
Local certificates are development-only.
