# ADR 0004: TLS termination at Envoy

- **Status:** Accepted
- **Date:** 2026-10-15

## Context

AWS NLB can terminate TLS with ACM. Doing so would move termination off
Envoy and weaken the project’s core claim that Envoy terminates TLS for
incoming traffic.

## Decision

- **Local and AWS:** Envoy terminates TLS.
- **AWS NLB:** TCP passthrough only (no TLS listener on the NLB for this
  demonstration).
- Upstream traffic on the private compose/host network is HTTP for v1;
  internal mTLS is documented as an extension, not required for proof.
- Development certificates are generated locally and never committed.

## Consequences

- Certificate distribution to EC2 must be handled at demo time (user-data,
  SSM, or manual copy) — documented in operations later.
- Interview defense stays consistent: L4 NLB vs L7 Envoy roles are clear.
