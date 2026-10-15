# ADR 0005: Demonstration client identity

- **Status:** Accepted
- **Date:** 2026-10-15

## Context

Distributed rate limiting needs a client key. Real production systems
derive identity from authenticated principals or trusted upstream
identity mechanisms. A demo that silently treats a client-supplied header
as strong identity is misleading.

## Decision

- Use the request header **`x-client-id`** as a **controlled demonstration
  identity** for rate-limit descriptors.
- Document clearly that the header is **spoofable** and is **not**
  production authentication.
- Implement identity extraction behind an **abstraction** so a trusted
  identity source could replace the header later without rewriting the
  token-bucket core.

## Consequences

- Tests set `x-client-id` explicitly.
- Threat model and README call out bypass/spoofing considerations.
- Interview discussion: demo identity vs authenticated principal.
