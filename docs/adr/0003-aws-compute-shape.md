# ADR 0003: AWS-shaped compute design (apply optional)

- **Status:** Accepted (amended for zero-cost DoD)
- **Date:** 2026-10-15

## Context

The project must remain architecturally credible for an AWS edge
deployment (NLB + compute + Envoy TLS) while being **fully completable
without spending money**. AWS Free Tier is not treated as free.

## Decision

1. **Design** Terraform for **one EC2 instance running Docker Compose**
   behind an **NLB with TCP passthrough**. Redis is a container on that
   host (not ElastiCache). Avoid NAT Gateway, ECS, and extra proxies in
   the default modules.
2. **Required validation** is static only: `fmt`, `validate`, lint,
   policy checks, module/config tests, and plan fixtures. No
   `terraform apply` in Definition of Done, CI, or default developer
   workflow.
3. **Real AWS apply** is optional validation for someone who explicitly
   opts into spend. It must never be implied by Terraform’s mere
   presence.

## Consequences

- Local Docker Compose carries the behavioral proof (TLS, routing, RL,
  failure, benchmarks).
- Interview defense still covers L4 NLB vs L7 Envoy and TLS placement.
- Resume/README must use evidence tiers: locally validated vs Terraform
  statically validated vs optionally cloud validated.
