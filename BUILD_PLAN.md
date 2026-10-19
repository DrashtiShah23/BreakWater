# Breakwater Build Plan

This document is the engineering plan derived from `BREAKWATER_BUILD_SPEC.md`.
It is intentionally written before any application code.

No benchmark numbers, AWS validation results, or integration claims appear
here as completed work. Those must be earned by later milestones.

**Status:** Plan approved (including zero-cost constraint and owner-only
Git). Milestones 0–6 complete (health checks / timeouts / retries).
Milestone 7+ not started.

---

## 0. Approved Decisions (binding)

These decisions supersede earlier open questions in this plan.

### 0.0 Permanent Git ownership rule (hard requirement)

**The human repository owner is the only person allowed to create Git
commits or push changes.** The coding agent must never commit or push.

The agent **may:**

- inspect `git status` / `git diff` / `git log`
- modify, create, or delete files as required by approved work
- run tests, formatting, linting, type checking, and validation
- suggest commit boundaries and commit messages

The agent **must not** run:

- `git commit`, `git push`, `git merge`, `git rebase`, `git tag`
- `git reset --hard`, `git clean`
- `git checkout` / `git restore` commands that discard changes
- `git add` unless the owner **explicitly** requests it

At the end of every milestone the agent must:

1. Stop before staging or committing anything.
2. Show validation results.
3. Show a concise summary of `git diff`.
4. List files created, modified, or deleted.
5. Separate changes into logical commit groups when more than one commit
   is appropriate.
6. Give exact suggested commit message(s).
7. Give exact `git` commands for the owner to run.
8. Wait for the owner to confirm commits before the next milestone.

Phrases like “finish the milestone,” “proceed,” or “continue” are **not**
permission to commit. This rule overrides any earlier plan language that
implied the agent should commit automatically.

### Permanent authorship and attribution rule (hard requirement)

**The repository owner is the sole author and committer of repository
commits.**

Never add any of the following to commit messages, Git metadata, source
headers, documentation, patches, or generated files:

- `Co-authored-by`
- `Signed-off-by` (unless the owner explicitly requests it for their own
  sign-off)
- `Generated-by`
- Cursor / Cursor Agent
- Claude / other model or product names used as attribution
- “AI”, “AI-assisted”, or any tool/agent authorship credit

The agent must not stage, commit, push, rewrite history, or modify Git
attribution. This rule applies permanently to every future milestone.

---

### 0.1 Zero-cost completeness (hard requirement)

**The project must be completable and fully defensible without spending
any money.** Zero cost is an architectural requirement from this point
forward—not a preference.

1. **No milestone requires paid AWS resources** to satisfy Definition of
   Done.
2. **Terraform remains in the repository** because infrastructure design
   and IaC are core engineering artifacts. **Real AWS provisioning is
   optional validation only**—never required for DoD, CI, README claims,
   or resume claims.
3. **Default zero-cost AWS/IaC validation path:** `terraform fmt`,
   `terraform validate`, tflint (if used), policy evaluation (e.g. OPA /
   Checkov / Sentinel-style checks as chosen later), module tests,
   configuration tests, and **plan fixture / expected-plan tests**. No
   `terraform apply` in the required path.
4. **Required workflow must not create** ALBs, NLBs, EC2 instances,
   Route 53 hosted zones, NAT Gateways, Elastic IPs, ECS services, RDS,
   ElastiCache, or any other potentially billable cloud resource.
5. **Do not assume AWS Free Tier makes a resource free.** If a cloud
   action can potentially generate a charge, it must not be required.
6. **Local Docker / Docker Compose** reproduce as much of the architecture
   and failure behavior as technically reasonable (Envoy TLS, routing,
   Redis RL, multi-instance health, Prom/Grafana, k6).
7. **GitHub Actions** stay within free-usage assumptions and **must not
   require cloud deployment**.
8. Any acceptance criterion that previously required real AWS is split
   into:
   - **zero-cost required validation**
   - **optional real AWS validation**
9. Documentation must distinguish evidence tiers (see §0.2).
10. Resume and README claims reflect **what was actually executed**.
    Terraform configuration alone is never a deployment claim.
11. The design stays **architecturally credible for AWS** even though AWS
    execution is optional.
12. **Do not weaken engineering depth** to avoid cloud cost. Replace
    cloud-dependent proof with local integration tests, infrastructure
    tests, policy tests, config validation, failure injection, and
    reproducible local benchmarks.

### 0.2 Evidence claim tiers

| Tier | Meaning | Allowed claim language |
| --- | --- | --- |
| **Implemented and locally validated** | Code/config ran under Docker Compose / local tools; tests exercised it | “Works locally”; “validated in Compose”; cite test/bench artifacts |
| **Terraform defined and statically validated** | Modules exist; fmt/validate/lint/policy/plan-fixtures pass | “Designed for AWS”; “IaC validated without apply” |
| **Optionally cloud validated** | Someone voluntarily applied and smoked real AWS | Only if apply actually happened; never implied by Terraform alone |

Never claim something was deployed to AWS unless it actually was.

### 0.3 Product and traffic decisions

1. **Configurable rate-limiter failure behavior.** Standard traffic
   **fails open** when Redis or the rate-limit service is unavailable.
   A **sensitive** route class **fails closed**. Both behaviors require
   integration tests and observable metrics. Availability versus
   protection is an explicit policy choice, not a single universal answer.

2. **AWS-shaped design (IaC, not required apply):** EC2 + Docker Compose
   behind an NLB using **TCP passthrough**, expressed in Terraform for
   architectural credibility. Envoy remains the TLS termination point.
   Do not replace this with ECS or managed Redis unless a later measured
   need genuinely justifies it. **Applying this stack is optional and
   explicitly out of Definition of Done.**

3. **Demonstration hosts:** `api.breakwater.local` and
   `status.breakwater.local`. Keep the status surface deliberately small;
   do not expand into an administration product.

4. **Demo identity:** `x-client-id` for rate limiting only. Document that
   it is spoofable and not production authentication. Keep identity
   extraction behind an abstraction so a trusted identity source could
   replace it later.

5. **License:** Apache License 2.0.

6. **Redis via Compose** (local required path; same pattern on optional
   EC2 if someone applies). Not ElastiCache.

7. **Preserve NLB TCP passthrough in the Terraform design.** Do not
   terminate TLS at the NLB. Local Compose has no NLB; Envoy is still
   the TLS termination point on the required path.

8. **Benchmark order:** (1) direct upstream, (2) Envoy without rate
   limiting, (3) Envoy with rate limiting. Edge overhead is calculated
   from those measurements, never inferred.

9. **Do not optimize** toward provisional resume numbers (e.g. 20K RPS
   or 4 ms p99 add). Replace claims with measured results only.

10. **Keep raw k6 outputs and benchmark metadata** under version control
    where size permits. Generated summaries must trace back to raw
    results.

11. **Do not introduce** Kubernetes, ECS, service mesh tooling, WAF, or
    additional proxies unless a measured limitation creates a real reason.

### Control traffic vs data traffic (preserve throughout)

| Class | Examples | Role |
| --- | --- | --- |
| **Data traffic** | Client HTTPS requests through Envoy to upstreams | The path under study: TLS, routing, rate limits, failure isolation, edge latency |
| **Control traffic** | Health checks, Prometheus scrapes, Grafana, Envoy admin/config, status host, failure-injection controls | Operates and observes the system; must not be confused with client data-plane load in benchmarks or failure analysis |

Breakwater is a **data-plane** demonstration (how traffic enters, is
routed, protected, observed, and delivered). It is intentionally separate
from control-plane change-management systems (e.g. a project like
Switchyard). Do not merge those concerns into this repository.

---

## 1. Architecture Restatement

Breakwater is a small, inspectable **edge traffic tier** in front of sample
HTTP APIs. It is not an API gateway, service mesh, or auth product.

### Intended data-plane request path

**Required (zero-cost) path — local Compose:**

```text
Client
  → Envoy :443 (TLS termination)
      → host + path route match
      → external rate-limit check (gRPC → rate-limit service → Redis)
      → healthy upstream cluster member
      → FastAPI sample service
         api.breakwater.local  → /api/v1|v2/items (primary data API)
         status.breakwater.local → small status surface (host-routing demo)
      Rate-limit failure class is per route (standard fail-open vs
      sensitive fail-closed), not automatically per entire host.
```

**Optional cloud path (Terraform-defined; apply not required for DoD):**

```text
Client → NLB TCP passthrough → Envoy :443 → (same as above on EC2+Compose)
```

### Intended control / observability path (not client data traffic)

```text
Health checks (Envoy → upstreams)
Prometheus scrapes (→ Envoy, rate-limit, upstreams)
Grafana (reads Prometheus)
Operator tooling (inject_failure, Envoy admin if exposed locally)
```

### Design intent

| Concern | Owner |
| --- | --- |
| TLS termination | Envoy |
| L7 routing, timeouts, health, safe retries | Envoy |
| Distributed rate-limit decision | Python rate-limit service + Redis |
| Application behavior under test | FastAPI upstreams |
| L4 distribution / stable public entry (optional AWS design) | Network Load Balancer (Terraform only unless optionally applied) |
| Measurement | k6 + latency comparison scripts (local) |
| Cloud recreation design | Terraform (statically validated; apply optional) |

On the optional AWS design, the NLB stays at L4 (TCP). Envoy remains the
L7 control point so “Envoy terminates TLS” stays true if cloud-validated.
Terminating TLS on the NLB would invalidate that architecture. Local
Compose proves the same Envoy TLS claim without an NLB.

---

## 2. Major Components and Responsibilities

### Envoy edge tier

- Terminate TLS for inbound HTTPS.
- Route by host and path to versioned upstream clusters.
- Enforce request timeouts; retry only idempotent GETs where safe
  (never on 429; limited attempts; no retry amplification of 5xx storms
  without explicit policy).
- Call the external rate-limit service via Envoy’s standard rate-limit
  filter / gRPC API.
- Active health checks; remove unhealthy upstreams from load balancing.
- Emit Prometheus metrics and structured access logs.

Configuration starts as readable static YAML. Templating is added only
if later milestones prove it necessary for multi-environment deploy.

### Sample upstreams (FastAPI)

At least two **logical applications** (host-based) and two **API
versions** (path-based), implemented as small FastAPI apps (or one
codebase with distinct route mounts / compose services).

Responsibilities:

- Serve `GET /api/v1/items`, `GET /api/v2/items`, `GET /health`.
- Expose controllable failure modes for demos/tests:
  normal, artificial latency, 5xx, process exit, recovery.
- Exist to make edge behavior measurable — not to host real business
  logic.

### Rate-limit service (Python)

- Implement Envoy-compatible external rate limiting over gRPC
  (`envoy.service.ratelimit.v3.RateLimitService` or the current stable
  equivalent at implementation time).
- Token bucket semantics in Redis (shared state across Envoy replicas).
- Support per-client and per-route descriptors, burst, configurable
  refill.
- Return clear decide/OK/OVER_LIMIT behavior and useful response
  metadata where Envoy can surface it.
- Development-only in-memory fallback, if present, must be explicitly
  labeled and disabled by default in “real” compose/AWS profiles.

### Redis

- Store distributed token-bucket state.
- Documented key layout, TTL/expiration, and failure behavior.
- Not publicly exposed.

### Prometheus + Grafana

- Scrape Envoy, rate-limit service, and upstreams as useful.
- Dashboards as code answering operator questions from the spec
  (traffic, throttle, upstream health, error origin, latency source).

### k6 + benchmark scripts

- Reproducible scenarios: baseline, edge-only, rate-limited, mixed,
  abusive, failure, saturation.
- Environment metadata recorded with every published result.
- `compare_latency.py` (or equivalent) computes **edge-added latency**
  from paired runs — never invented.

### Terraform

- Express a credible AWS edge design: VPC, public subnets (no NAT),
  security groups, NLB (TCP passthrough), EC2 + Compose-shaped compute,
  Redis on-instance (not ElastiCache).
- **Required validation is static only:** fmt, validate, lint, policy
  checks, module/config tests, plan fixtures.
- **`terraform apply` is optional** and must never be part of CI, DoD,
  or default Makefile targets that a reviewer is told they must run.
- Document which resources would be billable **if** someone applies;
  document that Free Tier is not treated as free.
- If optional apply docs exist, they must warn about cost and require
  explicit opt-in (not a silent default).

### CI

- PR: format, lint, unit tests, Envoy config validate, image builds,
  compose integration tests, Terraform fmt/validate/tflint/policy/plan
  fixtures as implemented.
- **No AWS credentials required for PR CI.**
- Optional apply workflow, if present at all, is manually triggered,
  approval-gated, cost-warned, and **outside Definition of Done.**

---

## 3. Hardest Technical and Operational Risks

| Risk | Why it is hard | Mitigation in plan |
| --- | --- | --- |
| Correct Envoy ↔ rate-limit gRPC integration | Protocol/descriptor mismatch silently fails open/closed or never limits | Milestone dedicated to proto compatibility, descriptor docs, and real 429 integration tests |
| Distributed token bucket correctness under concurrency | Race conditions and clock/refill math produce wrong limits | Redis atomic ops (Lua or equivalent); unit tests for accounting; multi-Envoy compose test |
| Fail-open vs fail-closed under Redis/RL outage | Wrong default looks “broken” or unsafe in review | Explicit policy per traffic class in docs + failure tests that assert it |
| Isolating edge-added latency | Confounding TLS, RL, upstream variance, noisy laptop | Paired methodology; disable RL for edge-only run; record env metadata; no resume numbers until measured |
| Health check vs retry amplification | Bad retries turn one slow upstream into a storm | Conservative retry policy; document non-retry cases; failure tests |
| Accidental paid AWS usage | Apply in CI/docs “quick start” causes charges | Zero-cost DoD; no apply in required path; Free Tier not trusted; Makefile defaults local-only |
| Weakening depth because cloud apply is optional | Skipping real failure/bench proof | Stronger Compose integration, failure injection, k6, IaC policy/plan tests |
| Claiming AWS deployment from Terraform alone | Resume/README overclaim | Evidence tiers in §0.2; honest language only |
| Local compose reliability | Flaky smoke/benchmarks destroy reviewer trust | Pin images/versions; Makefile targets; CI runs the same smoke path |
| Certificate / secret hygiene | Accidental key commit | Generate locally; gitignore; TLS README; no keys in Terraform state examples |
| CI “promotion” vs zero cost | Deploy workflow implies required AWS | PR CI = zero-cost only; optional apply (if any) never required |

---

## 4. Spec Ambiguities, Tensions, and Proposed Resolutions

### 4.1 Ambiguous or underspecified

| Item | Issue | Proposed resolution |
| --- | --- | --- |
| “Selected Envoy rate limit integration approach” | Spec does not name the API | Use Envoy **external rate limit filter** + Python gRPC service implementing the Envoy RateLimit service API. Document why not local ratelimit-only or a Redis filter extension. |
| “Two logical applications” vs one items API | Host routing needs two apps; examples only show versioned items | **Approved:** `api.breakwater.local` → versioned items. `status.breakwater.local` → deliberately small status surface (not an admin product). |
| Client identity | Header-based demo identity | **Approved:** `x-client-id` as controlled demo identity only; identity extraction behind an abstraction; README documents spoofability. |
| Cloud certificate strategy | ACM on NLB would steal TLS termination from Envoy | **NLB TCP passthrough**; Envoy presents certs loaded on the instance (dev/self-signed or operator-supplied). Document how ACM + ALB or cert distribution would work in production without claiming we built that. |
| Terraform `observability` module | Spec warns against public Prom/Grafana | Local: full Prom/Grafana. AWS: either omit public dashboards or private-only / SSH tunnel; optional CloudWatch agent metrics. Module exists only if it adds proof without cost/exposure. |
| “Controlled CI promotion” | Spec assumed AWS deploy | **Zero-cost:** CI promotes confidence via tests + static IaC checks. Optional apply workflow (if kept) is manual, approval-gated, cost-warned, and **not** DoD. |
| Multiple Envoy replicas “if practical” | Soft requirement | Local compose: `--scale envoy=2` (or dual services) in a milestone for shared Redis RL proof. |
| Retry policy “where safe” | Easy to over-retry | Default: retry GET only, bounded attempts, no retry on 429/connect-failure storms without evidence. ADR required. |

### 4.2 Internally tense (not contradictory if resolved explicitly)

- **Envoy terminates TLS** vs **AWS NLB**: resolved by TCP passthrough in the Terraform design; local Compose proves Envoy TLS without NLB.
- **Distributed Redis limiter** vs **zero-cost**: Redis in Compose locally (and on-instance in the optional AWS design), **not** ElastiCache.
- **Resume hypotheses (e.g. 20k RPS, &lt;4ms p99 add)** vs **honesty rule**: treat as unverified hypotheses; README only shows measured artifacts.
- **Spec “AWS deployment” language** vs **zero-cost DoD**: satisfy with Terraform design + static validation + local behavioral proof; live apply optional only.

### 4.3 Potentially outdated / implementation-sensitive

- Envoy bootstrap/filter names and the rate-limit protobuf package evolve. Pin an Envoy minor version early; generate or vendor stubs against that version.
- Prefer current stable Envoy + Redis + Python versions at implementation time; record pins in README/benchmark metadata.

### 4.4 Forbidden on the required (zero-cost) path

Do not create as part of required workflow or DoD:

- ALB, NLB, EC2, EIP, NAT Gateway, Route 53 hosted zones
- ECS/Fargate, RDS, ElastiCache, ACM Private CA billable paths
- Any other potentially billable cloud resource
- `terraform apply` in CI or default developer instructions

Terraform may **define** NLB/EC2/etc. for design credibility; defining ≠
provisioning.

### 4.5 Technically questionable if done naively

| Approach | Why questionable | Better default |
| --- | --- | --- |
| In-memory limiter called “distributed” | Spec forbids this | Redis-backed only for real claims |
| NLB TLS termination + plaintext to Envoy | Breaks “Envoy terminates TLS” claim | TCP → Envoy TLS (design + local Envoy) |
| Heavy Helm/templating on day one | Hides Envoy config from reviewers | Static YAML first |
| Custom UDP/TCP edge | Out of scope | HTTP/HTTPS L7 only |
| Claiming graceful shedding without saturation evidence | Spec forbids | Only claim what k6 shows |
| Using official Go `envoyproxy/ratelimit` only | Faster, but skips the Python service the spec asks to build | Build Python service; optionally compare in “Future work” |
| “Deployed on AWS” because Terraform exists | False resume claim | Evidence tiers; local validation language |
| Relying on Free Tier | Can still bill | Treat any chargeable API as non-required |

### 4.6 Design choices (approved)

1. **AWS-shaped IaC:** EC2 + Compose behind NLB TCP — approved as
   **Terraform design**. Apply is optional and outside DoD. No ECS /
   ElastiCache unless later justified.
2. **Configurable fail policy by route class** — approved: **standard → fail open**, **sensitive → fail closed**, with integration tests and metrics for both.
3. **Repo root = project root** (no nested `breakwater/` folder).
4. **Out of scope unless measured need:** Kubernetes, ECS, service mesh, WAF, extra proxies, ElastiCache.
5. **Zero-cost completeness** — approved (§0.1).

---

## 5. Final Repository Structure

```text
.
├── README.md
├── LICENSE
├── BUILD_PLAN.md                 # this plan
├── BREAKWATER_BUILD_SPEC.md      # engineering contract
├── Makefile
├── docker-compose.yml
├── docker-compose.test.yml       # optional overrides for CI/integration
├── .env.example
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml                # zero-cost: tests + static IaC checks only
│       └── apply-aws.yml         # OPTIONAL manual/cost-warned; not DoD; may omit
├── envoy/
│   ├── envoy.yaml
│   ├── ratelimit_descriptors.yaml  # or documented inline descriptors
│   └── tls/
│       └── README.md             # how to generate; no keys committed
├── services/
│   ├── upstream/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml        # or requirements.txt — choose in M2
│   │   ├── app/
│   │   └── tests/
│   └── rate_limit/
│       ├── Dockerfile
│       ├── proto/                # vendored/pinned Envoy ratelimit API
│       ├── app/
│       └── tests/
├── load/
│   ├── k6/
│   │   ├── baseline.js
│   │   ├── edge.js
│   │   ├── mixed_traffic.js
│   │   ├── abusive_client.js
│   │   ├── upstream_failure.js
│   │   └── saturation.js
│   └── results/
│       ├── .gitkeep
│       └── README.md             # what to commit vs keep local
├── observability/
│   ├── prometheus/
│   │   └── prometheus.yml
│   └── grafana/
│       ├── provisioning/
│       └── dashboards/
├── terraform/
│   ├── modules/
│   │   ├── network/
│   │   ├── nlb/
│   │   └── compute/
│   └── environments/
│       └── dev/                  # staging only if needed later
├── tests/
│   ├── integration/
│   └── failure/
├── scripts/
│   ├── generate_local_certs.sh
│   ├── benchmark.sh
│   ├── compare_latency.py
│   └── inject_failure.sh
└── docs/
    ├── architecture.md
    ├── benchmark_methodology.md
    ├── failure_model.md
    ├── threat_model.md
    ├── operations.md
    ├── routing_table.md
    ├── cost.md
    └── adr/
        ├── 0001-envoy-external-ratelimit.md
        ├── 0002-ratelimit-failure-policy.md
        ├── 0003-aws-compute-shape.md
        ├── 0004-tls-termination-placement.md
        └── 0005-demo-client-identity.md
```

Notes:

- `terraform/modules/observability/` is **deferred**; local Grafana is the
  required observability evidence path.
- **LICENSE:** Apache License 2.0 (approved).
- Terraform modules may describe NLB/EC2; **required tests never apply them.**

---

## 6. Ordered Milestones and Acceptance Criteria

Each milestone should end in small, reviewable commits **created by the
repository owner** (see §0.0). The agent proposes boundaries and messages
only; it never stages or commits. Acceptance criteria are binary: met
only when exercised as stated. Mocks count for unit tests only.

### Milestone 0 — Plan and contract locked

**Deliverables:** `BREAKWATER_BUILD_SPEC.md` (existing), `BUILD_PLAN.md`
(this file).

**Acceptance:**

- [x] Plan reviewed before application code starts.
- [x] Open decisions accepted and recorded in §0.

**Local:** yes · **AWS:** no

---

### Milestone 1 — Repository skeleton and architecture docs

**Deliverables:** README stub (problem statement + diagram),
`docs/architecture.md` with Mermaid (data traffic vs control/metrics
paths labeled), Makefile stubs, `.gitignore`, `.env.example`, Apache 2.0
LICENSE, ADR stubs for approved decisions, empty/target dirs per §5.

**Acceptance:**

- [x] Fresh clone shows clear layout and “how this will be built.”
- [x] Mermaid diagram matches the intended architecture and distinguishes
      data traffic from control/observability traffic.
- [x] Approved hosts, AWS shape, fail-policy classes, and identity
      caveats appear in architecture/ADR stubs.
- [x] No application runtime claimed to work yet.

**Local:** yes · **AWS:** no

---

### Milestone 2 — Sample upstream service

**Deliverables:** FastAPI upstream with health, v1/v2 items, control
endpoints for latency/5xx/crash; unit tests; Dockerfile; compose service
for upstream only.

**Acceptance:**

- [x] `GET /health` returns healthy.
- [x] v1 and v2 items routes respond.
- [x] Control endpoints demonstrably change latency/5xx/kill behavior.
- [x] Unit tests pass without Docker where practical.

**Local:** yes · **AWS:** no

**Notes (M2):** Two compose services from one image (`SURFACE=api|status`).
Test controls under `/__test__/*` when `ENABLE_TEST_CONTROLS=true`; disable
for production-like / optional cloud profiles. `/live` vs `/health`
distinguish process-alive from intentional unhealthy. Crash control is
allowlisted (`confirm: true`) and scheduled process exit — covered by
schema tests; full process death is for manual/compose failure demos.
**Zero-cost:** M2 is entirely local; no cloud resources required.

---

### Milestone 3 — Basic Envoy reverse proxy (plaintext)

**Deliverables:** Minimal `envoy.yaml` proxying to upstream over HTTP;
compose: Envoy + upstream; smoke script or make target.

**Acceptance:**

- [x] Request through Envoy reaches upstream.
- [x] Envoy config passes `envoy --mode validate` (or image equivalent).
- [x] No TLS required yet.

**Local:** yes · **AWS:** no

**Notes (M3):** Plaintext HTTP only. Catch-all host; routes `/health`,
`/live`, `/api/*`, `/__test__/*` to `upstream-api`; other paths get an
explicit edge 404. Host routing to `status` deferred to M5. Admin :9901
is control traffic (localhost-bound on host).

---

### Milestone 4 — TLS termination

**Deliverables:** `scripts/generate_local_certs.sh`; Envoy HTTPS listener;
`envoy/tls/README.md`; gitignore for keys/certs.

**Acceptance:**

- [x] HTTPS to Envoy succeeds with generated dev certs.
- [x] README states certs are development-only.
- [x] `git status` never requires committing private keys.
- [x] Document where TLS terminates and that upstream is HTTP on the
      compose network (and how mTLS could be added later).

**Local:** yes · **AWS:** no

**Notes (M4):** Primary data listener `:8443` (HTTPS). Upstream hop remains
plaintext HTTP. Admin `:9901` stays control/plaintext on localhost. Optional
`:8080` plaintext debug listener only.

---

### Milestone 5 — Host and path routing

**Deliverables:** Two logical hosts; path routing to v1/v2; default and
unknown host/path behavior; routing table in docs/README.

**Acceptance:**

- [x] Host A and Host B route as documented.
- [x] Path version selection works.
- [x] Unknown host and unknown path return explicit documented behavior.
- [x] Integration tests cover the routing table (compose-based).

**Local:** yes · **AWS:** no

**Notes (M5):** `api.breakwater.local` → `upstream_api`; 
`status.breakwater.local` → `upstream_status`. Exact paths only (no broad
`/api/` or `/__test__/` catch-alls). Unknown host/path → edge 404.
Route-class ≠ hostname. `:8080` kept as local-dev plaintext debug bound to
`127.0.0.1`.

---

### Milestone 6 — Health checks and upstream failure handling

**Deliverables:** Active health checks; multi-instance upstream cluster
where practical; timeout policy; conservative retry policy + ADR note;
`scripts/inject_failure.sh` for upstream kill/latency.

**Acceptance:**

- [x] Stopping one upstream removes it from serving (verified by
      traffic/metrics or admin endpoint observation).
- [x] Restoration brings it back without manual Envoy rewrite.
- [x] Timeout behavior verified with injected latency.
- [x] Failure test documents observed 5xx/timeout behavior (no invented
      numbers required beyond pass/fail assertions).

**Local:** yes · **AWS:** no

**Notes (M6):** Dual `upstream_api` members; HC on `/health`; transport-only
retries on GET items; no HTTP 5xx retries; ADR 0006 + `docs/failure_model.md`.

---

### Milestone 7 — Redis-backed rate-limit service (standalone)

**Deliverables:** Python token bucket + Redis; gRPC server implementing
Envoy rate-limit API; unit tests for accounting, identity extraction,
failure policy; key schema docs; Dockerfile; compose: Redis + service.

**Acceptance:**

- [ ] Unit tests prove token bucket math and burst/refill.
- [ ] Service decides OK vs OVER_LIMIT against Redis without Envoy.
- [ ] Key structure and TTL documented.
- [ ] Dev in-memory mode (if any) cannot be mistaken for distributed mode.

**Local:** yes · **AWS:** no

---

### Milestone 8 — Envoy rate-limit integration

**Deliverables:** Envoy external rate-limit filter wired to service;
descriptors for per-client and per-route; 429 path; metadata/headers as
designed; **standard (fail-open) and sensitive (fail-closed)** route
classes; integration tests and metrics for both failure policies.

**Acceptance:**

- [ ] Compliant client under limit succeeds end-to-end through Envoy.
- [ ] Exceeding client receives 429 through Envoy (not merely unit mock).
- [ ] Burst behavior matches documented config.
- [ ] Optional: two Envoy containers share Redis limits (if compose scale
      exercised).
- [ ] When Redis or RL is unavailable: **standard** routes fail open and
      **sensitive** routes fail closed — both asserted by integration
      tests and visible in metrics.
- [ ] RL service slow path matches documented behavior.

**Local:** yes · **AWS:** no

---

### Milestone 9 — Prometheus metrics

**Deliverables:** Prometheus scrape config; Envoy metrics; rate-limit
latency/decision metrics; upstream metrics as useful; make target to
open/query smoke checks.

**Acceptance:**

- [ ] Prometheus is up via compose and scrapes Envoy successfully.
- [ ] 429 and 5xx related signals are queryable after generating traffic.
- [ ] Rate-limit service exposes decision and latency metrics.

**Local:** yes · **AWS:** no

---

### Milestone 10 — Grafana provisioning

**Deliverables:** Datasource + dashboard JSON as code; panels listed in
the spec; thresholds only with rationale.

**Acceptance:**

- [ ] Fresh compose brings Grafana up with dashboards **without** manual
      UI import.
- [ ] Operator questions in the spec can be answered from the dashboard
      after generating sample traffic (qualitative check + screenshot
      later in docs milestone).

**Local:** yes · **AWS:** no

---

### Milestone 11 — Structured access logging

**Deliverables:** Envoy JSON (or clearly structured) access logs;
correlation/request id where practical; ops notes on how to distinguish
edge vs upstream failures in logs.

**Acceptance:**

- [ ] Sample request produces structured log fields needed for debugging
      route, response code, upstream, and timing.
- [ ] Documented how logs complement metrics.

**Local:** yes · **AWS:** no

---

### Milestone 12 — Baseline and edge k6 benchmarks

**Deliverables:** `baseline.js` (direct upstream), edge scenario with RL
disabled, then RL-enabled companion (or Milestone 13 if split);
`scripts/benchmark.sh`; `scripts/compare_latency.py`;
`docs/benchmark_methodology.md` draft; `load/results/README.md`.

**Acceptance:**

- [ ] From clean checkout + documented setup, runs in order:
      (1) direct upstream, (2) Envoy without rate limiting,
      (3) Envoy with rate limiting (may land with M13 if scoped).
- [ ] Edge-added latency is **calculated** from (1) vs (2); RL overhead
      from (2) vs (3) — never inferred.
- [ ] Raw k6 outputs and metadata retained under `load/results/` when
      size permits; summaries trace to raw files.
- [ ] Result bundle includes required environment metadata fields from
      the spec (versions, hardware, flags, commit, date).
- [ ] No provisional resume numbers presented as results.

**Required validation:** local Compose / host only (zero-cost).  
**Optional:** re-run on personal hardware variants; not AWS.

---

### Milestone 13 — Mixed / abusive traffic benchmarks

**Deliverables:** `mixed_traffic.js`, `abusive_client.js`; methodology
updates.

**Acceptance:**

- [ ] Abusive clients observe 429s.
- [ ] Compliant clients in the same run remain successful within the
      test’s stated success criteria (assertions in script or post-process).
- [ ] Raw outputs retained per results policy.

**Local:** yes · **AWS:** no

---

### Milestone 14 — Failure injection suite

**Deliverables:** k6 or scripted failure scenarios; `tests/failure/`;
`docs/failure_model.md`; inject Redis/RL/upstream/Envoy restart cases.

**Acceptance:**

- [ ] Each failure class in the spec has an automated or documented
      one-command reproduction.
- [ ] Observed behavior matches the failure policy table (or the table
      is updated to match reality — never the reverse by faking output).
- [ ] No claim of “graceful shedding” unless saturation evidence exists.

**Local:** yes · **AWS:** no

---

### Milestone 15 — Terraform modules + zero-cost IaC validation

**Deliverables:** Modules describing VPC/public subnets/SGs, NLB TCP,
EC2+Compose-shaped compute; `docs/cost.md` listing what would bill **if
applied**; tags; **static** validation harness (fmt, validate, tflint,
policy checks, plan fixtures / expected plan tests).

**Acceptance — zero-cost required:**

- [ ] `terraform fmt` + `validate` succeed for `environments/dev`.
- [ ] Lint/policy/config tests pass without AWS credentials or apply.
- [ ] Plan-fixture (or equivalent) tests assert critical invariants:
      no NAT Gateway, no public Redis, NLB is TCP (not TLS terminator),
      no ElastiCache/ECS/ALB unless explicitly absent.
- [ ] Docs state clearly: modules are **designed for AWS**; **not
      deployed** unless optional path is used.
- [ ] ADR `0003` records EC2+Compose behind NLB TCP as the **design**,
      with apply optional / outside DoD.

**Acceptance — optional real AWS:** none for this milestone.

**Required path:** local/CI static only · **Paid AWS:** not required

---

### Milestone 16 — Optional AWS apply runbook (outside DoD)

**Deliverables:** Documented **optional** apply/destroy runbook with
explicit cost warnings; optional manual workflow if desired. **No
required Makefile target that applies infrastructure.**

**Acceptance — zero-cost required:**

- [ ] README / ops docs state that cloud apply is **optional** and
      **not required** to complete the project.
- [ ] Default developer path never runs `terraform apply`.
- [ ] If wrappers exist, they require explicit opt-in (e.g.
      `BREAKWATER_ALLOW_AWS_SPEND=1`) and print billable-resource warnings.
- [ ] Evidence tiers (§0.2) documented for reviewers.

**Acceptance — optional real AWS validation** (only if someone
voluntarily spends money):

- [ ] Apply creates reachable HTTPS edge via NLB → Envoy TLS.
- [ ] Smoke: routing + health through public entry.
- [ ] Destroy completes; no orphaned billable resources.
- [ ] Docs record that this run was optionally cloud-validated (date,
      region, commit)—never implied for readers who did not apply.

**Required path:** documentation + guardrails only · **Paid AWS:** optional

---

### Milestone 17 — CI validation (zero-cost)

**Deliverables:** `ci.yml` for PRs: Python fmt/lint/tests, Envoy
validate, Compose integration, Terraform fmt/validate/lint/policy/plan
fixtures; lightweight security scan if free and non-flaky.

**Acceptance — zero-cost required:**

- [ ] PR pipeline red on broken unit tests / invalid Envoy config.
- [ ] Integration tests run in CI via Docker Compose (no AWS).
- [ ] Terraform static checks run in CI **without** AWS credentials.
- [ ] No workflow step performs `terraform apply` or creates billable
      resources.
- [ ] Stays within free GitHub Actions assumptions (no self-hosted paid
      requirement; no cloud deploy).

**Acceptance — optional real AWS:** not part of CI.

**Required path:** GHA free tier assumptions · **Paid AWS:** none

---

### Milestone 18 — Benchmark documentation and evidence hygiene

**Deliverables:** Final methodology; how to reproduce; where artifacts
live; README section wired to **actual local** results only.

**Acceptance — zero-cost required:**

- [ ] Another engineer can reproduce baseline/edge/mixed from docs alone
      on local Docker—no cloud account required.
- [ ] Any number in README maps to a retained artifact + commit hash.
- [ ] Hypotheses from old resume drafts are labeled hypotheses or removed.
- [ ] No AWS performance claims unless optional cloud validation occurred.

**Required path:** local · **Paid AWS:** optional only if already done

---

### Milestone 19 — Threat model and operations guide

**Deliverables:** `docs/threat_model.md`, `docs/operations.md`, failure
policy table finalized, trust boundaries, identity limitations, RL bypass
notes, cert rotation story, Redis exposure controls, cost/optional-apply
warnings.

**Acceptance — zero-cost required:**

- [ ] Threat model covers trust boundaries and demo identity caveats.
- [ ] Ops guide covers local start/stop, cert regen, failure injection,
      and (separately) optional AWS apply warnings.
- [ ] Security requirements in the spec are addressed for the **local**
      demonstration path; AWS SG design covered as Terraform intent.

**Required path:** docs · **Paid AWS:** docs may describe design only

---

### Milestone 20 — Final README and demo assets

**Deliverables:** Public README meeting the spec’s section list;
architecture diagram; Grafana screenshot from a **local** running stack;
failure injection example; tradeoffs and known limitations; future work;
explicit evidence-tier language for AWS.

**Acceptance — zero-cost required:**

- [ ] README opens with the engineering problem.
- [ ] Quick start, test, and benchmark commands work from a clean
      checkout **without AWS**.
- [ ] AWS section describes Terraform design + static validation; uses
      “optionally cloud validated” only if that actually happened.
- [ ] No invented performance or AWS deployment claims.
- [ ] Definition of Done (zero-cost) checklist reviewed item-by-item.

**Required path:** local evidence · **Paid AWS:** never implied

---

## 7. Milestone cost map

| Milestone | Zero-cost required path | Real AWS required for DoD? |
| --- | --- | --- |
| 0–14 | Local Docker/Compose + tests + benches | **No** |
| 15 | Terraform fmt/validate/lint/policy/plan fixtures | **No** |
| 16 | Guardrails + optional-apply docs | **No** (apply optional) |
| 17 | GHA: tests + static IaC only | **No** |
| 18–20 | Local evidence + honest docs | **No** |

**Default path to “done”:** M1–M15 + M17–M20 entirely without AWS
credentials or spend. M16 optional forever.

---

## 8. AWS design (credible IaC) vs optional apply

### 8.1 What we design in Terraform (architectural credibility)

Even though apply is optional, modules should remain interview-defensible:

1. VPC with public subnets, **no NAT Gateway**.
2. NLB, **TCP :443** passthrough → instance target (Envoy terminates TLS).
3. Single EC2-shaped compute intended to run Docker Compose (Envoy,
   Redis container, rate-limit, upstreams).
4. Security groups: no public Redis/Prometheus/Grafana.
5. Tags: `Project=breakwater`, etc.
6. Explicit absence of ElastiCache, ECS, ALB, Route 53 zones on the
   default module path.

### 8.2 Zero-cost required validation (DoD)

| Check | Purpose |
| --- | --- |
| `terraform fmt` / `validate` | Syntax and provider config soundness |
| tflint (if used) | Common mistakes |
| Policy evaluation | Block NAT/public Redis/TLS-on-NLB/etc. |
| Module / config tests | Unit-level Terraform logic |
| Plan fixtures / expected plan | Assert resource shapes **without apply** |

No AWS account is required if fixtures use known providers / mocked plan
inputs as designed in M15.

### 8.3 Optional real AWS validation (never required)

If a reviewer **chooses** to spend money:

- Explicit opt-in env var / documented danger.
- Short-lived apply → smoke → destroy.
- Record evidence under “optionally cloud validated.”
- Do **not** update resume/README deployment claims for others who did
  not apply.

### 8.4 Billable if applied (document; do not require)

| Resource | Why it can cost | Required path stance |
| --- | --- | --- |
| NLB | Hourly + LCU | Define only; do not apply for DoD |
| EC2 + EBS | Instance + disk hours | Define only |
| Public IPv4 | May be charged | Define only |
| NAT / ElastiCache / ALB / ECS / R53 zones | Easy spend | **Do not include** in default modules |
| CloudWatch | Ingestion | Avoid / omit on optional path too if unused |

**Free Tier is not treated as free.**

### 8.5 Depth substitutes for cloud apply

To keep senior-engineer bar without spend:

- Multi-container Compose matching the intended data plane
- Failure injection for upstream/Redis/RL/Envoy
- Shared Redis limits across scaled Envoy replicas locally
- Reproducible k6 with raw artifacts
- Strict IaC policy + plan-fixture tests
- Clear L4-vs-L7 / TLS-placement ADRs

---

## 9. Git History Intent

Milestones map to natural commits so history reads like engineering
progress, not a single dump. **Only the repository owner creates those
commits** (§0.0). The agent suggests groupings and messages at milestone
end.

Suggested progression:

1. Skeleton + architecture  
2. Upstream  
3. Plain Envoy proxy  
4. TLS  
5. Routing  
6. Health/failure  
7. Rate-limit service  
8. Envoy integration  
9–11. Observability + logs  
12–14. Load and failure evidence tooling  
15. Terraform modules + static IaC tests  
16. Optional AWS runbook (docs/guardrails; apply not required)  
17. Zero-cost CI  
18–20. Docs and polish  

Prefer small commits inside a milestone when that clarifies review
(e.g., “add token bucket,” then “add gRPC server”).

---

## 10. Working Rules for Implementation Phases

Carried forward from the spec and §0; binding for later milestones:

- Spec = requirements, not copy-paste code.
- Prefer a better/current implementation only with an explanation
  (ADR or plan amendment) before changing design.
- **Git ownership (§0.0):** agent never commits, pushes, or stages unless
  explicitly told to `git add`; owner alone owns history.
- **Authorship (§0.0):** no Co-authored-by / Generated-by / Cursor /
  Claude / AI / tool attribution in commits, metadata, headers, docs,
  patches, or generated files; owner is sole author and committer.
- **Zero-cost DoD is binding (§0.1).** No required paid cloud usage.
- Do not invent benchmark, security, or AWS results.
- Do not claim AWS deployment from Terraform alone (§0.2).
- Do not hardcode outputs to pass acceptance checks.
- Do not claim an integration works until exercised.
- Mocks are for unit tests; real integration criteria need real wiring
  (local Compose counts; unpaid cloud does not unlock extra claims).
- Keep scope tight; no Kubernetes/ECS/mesh/WAF/extra proxies without a
  measured reason.
- Distinguish **data traffic** from **control traffic** in docs, metrics,
  and benchmarks.
- Optimize for depth, correctness, reproducibility, operational safety,
  clarity—**without** weakening tests because apply is optional.
- Significant decisions get reasons (ADRs).
- After each phase: format, lint, test, update docs; **suggest** commits
  for the owner—do not create them.

---

## 11. Stop Points by Milestone

- After plan approval: Milestone 0 complete (§0).
- After skeleton and architecture docs: **stop at Milestone 1** until
  reviewed; do not start Milestone 2 without go-ahead.
- Later milestones: implement → validate → **stop with commit suggestions**
  → wait for owner confirmation that commits landed → only then next
  milestone when requested.
- Never treat “finish / proceed / continue” as commit permission (§0.0).

---

## Appendix A — Definition of Done Traceability

Spec items that assumed live AWS are satisfied on the **zero-cost** path
as shown. Optional cloud apply never gates “done.”

| Spec / project DoD item | Milestone(s) | Zero-cost satisfaction |
| --- | --- | --- |
| Local TLS | 4 | Compose + local certs |
| Host routing | 5 | Envoy + local hosts / resolve |
| Path routing | 5 | Envoy |
| Redis distributed RL | 7–8 | Compose Redis + tests |
| 429 tested | 8, 13 | Local integration + k6 |
| Health-based removal | 6 | Local multi-upstream |
| Failure recovery | 6, 14 | Local failure suite |
| Prometheus metrics | 9 | Local Prom |
| Grafana auto-provisioned | 10 | Local Grafana |
| k6 from clean checkout | 12–14 | Local k6 |
| Baseline + edge + edge-added latency | 12 | Local paired runs |
| Failure injection | 14 | Local scripts/tests |
| Terraform validated | 15, 17 | fmt/validate/lint/policy/plan fixtures |
| AWS deploy/destroy | 16 | **Not required**; optional only |
| CI validates repo | 17 | GHA without apply |
| README with real evidence | 18, 20 | Local artifacts + honest IaC language |
| No invented performance / AWS claims | 12–20 | Continuous |
| Completable without spending money | 0.1 | Hard requirement |

## Appendix B — Decision Log (resolved)

| # | Question | Decision |
| --- | --- | --- |
| 1 | Fail-open when Redis/RL down? | Yes for **standard**; **sensitive** fails closed; configurable; both tested + metered |
| 2 | EC2 + Compose behind NLB TCP? | Yes as **Terraform design**; apply optional / outside DoD; no ECS/ElastiCache by default |
| 3 | Second host? | `api.breakwater.local` + `status.breakwater.local` |
| 4 | `x-client-id`? | Yes, demo-only; abstract extraction; document spoofability |
| 5 | License? | Apache 2.0 |
| 6 | Resume hypotheses as targets? | Do not optimize toward them; replace with measured results only |
| 7 | Must spend on AWS to finish? | **No.** Zero-cost completeness is mandatory (§0.1) |
| 8 | Who commits / pushes? | **Owner only.** Agent never commits or pushes (§0.0) |
| 9 | Commit / file attribution? | **Owner sole author.** No Co-authored-by, Generated-by, Cursor, Claude, AI, or tool credit (§0.0) |
