# Cost and cloud spend policy

**Hard rule:** Breakwater must be completable without spending money.
AWS Free Tier is **not** treated as free.

## Required path (zero cost)

- Local Docker / Docker Compose for the full data plane and failure demos
- Terraform `fmt` / `validate` / lint / policy / plan-fixture tests
- GitHub Actions without `terraform apply` or cloud provisioning

No ALB, NLB, EC2, EIP, NAT Gateway, Route 53 hosted zone, ECS, RDS,
ElastiCache, or other potentially billable resources are created by the
required workflow.

## Terraform in this repo

Modules **describe** a credible AWS shape (NLB TCP → EC2 + Compose,
Envoy terminates TLS, Redis on-instance). That is **infrastructure
design**, not a deployment claim.

| Evidence tier | When you may say it |
| --- | --- |
| Implemented and locally validated | Compose/tests/benchmarks actually ran |
| Terraform defined and statically validated | fmt/validate/lint/policy/plan fixtures passed |
| Optionally cloud validated | Only if `terraform apply` was deliberately run and recorded |

## Optional apply (outside Definition of Done)

If someone voluntarily applies, expect potential charges for NLB, EC2,
EBS, and public IPv4 among others. Document warnings in the optional
runbook (Milestone 16). Destroy promptly. Never imply that other
reviewers have deployed to AWS.
