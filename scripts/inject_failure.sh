#!/usr/bin/env bash
# Local failure-injection helpers for Breakwater upstreams (Milestone 6+).
# Test controls are direct-to-upstream only — never via Envoy public routes.
#
# Usage:
#   ./scripts/inject_failure.sh unhealthy api-2
#   ./scripts/inject_failure.sh healthy api-2
#   ./scripts/inject_failure.sh latency api-1 4000
#   ./scripts/inject_failure.sh errors api-1 http_500 5
#   ./scripts/inject_failure.sh reset api-1
#   ./scripts/inject_failure.sh stop upstream-api-2
#   ./scripts/inject_failure.sh start upstream-api-2

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

API1="${UPSTREAM_API_PORT:-9001}"
API2="${UPSTREAM_API_2_PORT:-9003}"
STATUS="${UPSTREAM_STATUS_PORT:-9002}"

port_for() {
  case "$1" in
    api-1|upstream-api) echo "${API1}" ;;
    api-2|upstream-api-2) echo "${API2}" ;;
    status|upstream-status) echo "${STATUS}" ;;
    *) echo "unknown target: $1" >&2; exit 1 ;;
  esac
}

cmd="${1:-}"
target="${2:-api-1}"

case "${cmd}" in
  unhealthy)
    curl -sf -X POST "http://127.0.0.1:$(port_for "${target}")/__test__/health" \
      -H 'content-type: application/json' -d '{"healthy":false}'
    echo
    ;;
  healthy)
    curl -sf -X POST "http://127.0.0.1:$(port_for "${target}")/__test__/health" \
      -H 'content-type: application/json' -d '{"healthy":true}'
    echo
    ;;
  latency)
    ms="${3:-2000}"
    curl -sf -X POST "http://127.0.0.1:$(port_for "${target}")/__test__/latency" \
      -H 'content-type: application/json' -d "{\"delay_ms\":${ms}}"
    echo
    ;;
  errors)
    mode="${3:-http_500}"
    count="${4:-1}"
    curl -sf -X POST "http://127.0.0.1:$(port_for "${target}")/__test__/errors" \
      -H 'content-type: application/json' \
      -d "{\"mode\":\"${mode}\",\"count\":${count}}"
    echo
    ;;
  reset)
    curl -sf -X POST "http://127.0.0.1:$(port_for "${target}")/__test__/reset"
    echo
    ;;
  stop)
    docker compose stop "${target}"
    ;;
  start)
    docker compose start "${target}"
    ;;
  *)
    echo "Usage: $0 {unhealthy|healthy|latency|errors|reset|stop|start} [target] [args...]" >&2
    exit 1
    ;;
esac
