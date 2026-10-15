# ADR 0002: Rate-limit failure policy by route class

- **Status:** Accepted
- **Date:** 2026-10-15

## Context

When Redis or the rate-limit service is unavailable, the edge must choose
between availability (fail open) and protection (fail closed). There is
no universally correct answer; it is a policy decision.

## Decision

Make failure behavior **configurable by route class**:

| Class | Behavior when Redis or RL unavailable |
| --- | --- |
| **Standard** | Fail open (allow); emit metrics and logs |
| **Sensitive** | Fail closed (deny/error per wiring); emit metrics and logs |

Default demo API data path uses **standard**. At least one sensitive
route exists so both policies are exercised.

## Consequences

- Integration and failure tests must cover both classes (Milestone 8/14).
- Metrics must make the chosen policy and outage visible.
- Operators can defend the tradeoff in review without pretending one
  policy fits all traffic.
