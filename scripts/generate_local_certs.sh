#!/usr/bin/env bash
# Generate development-only TLS material for Breakwater Envoy.
#
# Output (gitignored — never commit private keys or these certs):
#   envoy/tls/ca.key
#   envoy/tls/ca.crt
#   envoy/tls/server.key
#   envoy/tls/server.crt
#
# Trust model: clients that want verification must trust ca.crt explicitly.
# These certificates are NOT production credentials.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TLS_DIR="${ROOT_DIR}/envoy/tls"
DAYS="${BREAKWATER_CERT_DAYS:-825}"

mkdir -p "${TLS_DIR}"
cd "${TLS_DIR}"

if ! command -v openssl >/dev/null 2>&1; then
  echo "error: openssl is required to generate development certificates" >&2
  exit 1
fi

echo "Generating Breakwater development CA and server certificate in ${TLS_DIR}"
echo "WARNING: development certificates only — not for production use."

# Local development CA
openssl genrsa -out ca.key 2048 2>/dev/null
openssl req -x509 -new -nodes -key ca.key -sha256 -days "${DAYS}" \
  -subj "/O=Breakwater Dev/CN=Breakwater Local Dev CA" \
  -out ca.crt

# Server key + CSR
openssl genrsa -out server.key 2048 2>/dev/null
openssl req -new -key server.key \
  -subj "/O=Breakwater Dev/CN=breakwater.local" \
  -out server.csr

cat > server.ext <<'EOF'
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = breakwater.local
DNS.3 = api.breakwater.local
DNS.4 = status.breakwater.local
IP.1 = 127.0.0.1
EOF

openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out server.crt -days "${DAYS}" -sha256 -extfile server.ext

rm -f server.csr server.ext ca.srl

chmod 600 ca.key server.key
chmod 644 ca.crt server.crt

echo
echo "Generated:"
echo "  ${TLS_DIR}/ca.crt      (trust this for client verification)"
echo "  ${TLS_DIR}/ca.key      (PRIVATE — gitignored)"
echo "  ${TLS_DIR}/server.crt  (presented by Envoy)"
echo "  ${TLS_DIR}/server.key  (PRIVATE — gitignored)"
echo
echo "Next: make validate-envoy && make up && make smoke"
