# ADR 0001: Envoy external rate-limit service

- **Status:** Accepted
- **Date:** 2026-10-15

## Context

Breakwater needs distributed rate limiting shared across Envoy instances,
with clear semantics under Redis or limiter outages. Envoy supports local
rate limits, Redis-based extensions, and an external gRPC rate-limit
service API.

## Decision

Use Envoy’s **external rate-limit filter** and implement a **Python gRPC
service** compatible with the Envoy RateLimit service API, backed by
Redis token buckets.

## Consequences

- Descriptors and proto compatibility become first-class integration work
  (Milestone 7–8).
- We can demonstrate standard vs sensitive failure policies in one place.
- We do not claim the official Go `envoyproxy/ratelimit` binary is what
  we built; comparison may appear under future work only.
