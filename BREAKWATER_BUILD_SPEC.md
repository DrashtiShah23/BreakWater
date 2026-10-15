# Breakwater

## Build Specification for Cursor

### Mission

Build Breakwater as a production style edge traffic tier in front of a
sample application.

The project should demonstrate how an ingress layer can terminate TLS,
route requests, enforce distributed rate limits, isolate unhealthy
upstreams, expose meaningful telemetry, and remain predictable under
load and partial failure.

The repository should emphasize traffic engineering, failure behavior,
measurement, and operational clarity.

The goal is not to create a toy reverse proxy configuration.

The goal is to create a small but credible edge platform that a senior
network or platform engineer can inspect, run, stress, break, and
understand.

### Resume Claims This Repository Must Prove

The finished implementation must provide reproducible evidence for these
capabilities.

1.  Envoy terminates TLS for incoming traffic.

2.  Requests route by host and path to versioned upstream services.

3.  Per client token bucket limits are enforced through a Redis backed
    rate limit service.

4.  The system can be deployed on AWS behind a Network Load Balancer
    using Terraform.

5.  The deployment uses controlled CI promotion.

6.  k6 produces a reproducible load test result.

7.  Abusive clients are throttled quickly without materially degrading
    compliant clients.

8.  The project measures edge added latency rather than merely reporting
    total application latency.

9.  Prometheus and Grafana expose request volume, 429 responses, 5xx
    responses, upstream latency, and relevant edge health metrics.

Any throughput or latency number placed on a resume must come from the
actual benchmark artifacts produced by this repository.

Do not force the implementation to achieve a predetermined number.

### Product Boundary

Breakwater is an ingress and traffic management demonstration.

It is not a full API gateway.

It should not implement application business authentication, billing,
service discovery for arbitrary clusters, or a general service mesh.

Focus on:

TLS

Routing

Rate limiting

Upstream health

Failure isolation

Traffic observability

Load testing

Infrastructure deployment

## Architecture

### Request Path

Client

AWS NLB for cloud validation

Envoy

TLS termination

Route selection

External rate limit decision

Healthy upstream cluster

Sample API service

Metrics and logs emitted throughout

### Components

#### Envoy Edge Tier

Envoy owns:

TLS termination

Host based routing

Path based routing

Versioned upstream selection

Health checks

Request timeout policy

Retry policy where safe

Rate limit filter integration

Access logs

Prometheus metrics

Do not hide the Envoy configuration behind excessive templating at the
beginning.

The configuration should remain inspectable.

#### Sample Upstreams

Create at least two versions of a small FastAPI service.

Example routes:

`GET /api/v1/items`

`GET /api/v2/items`

`GET /health`

Provide controllable behavior for testing:

Normal response

Artificial latency

5xx response

Process termination

Recovery

The upstream exists to make edge behavior measurable.

#### Rate Limit Service

Build a small Python service compatible with the selected Envoy rate
limit integration approach.

Use Redis for shared state.

Implement token bucket semantics.

Support at least:

Per client limit

Per route limit

Burst allowance

Configurable refill rate

Clear response metadata where appropriate

Do not implement a fake in memory limiter and describe it as
distributed.

If a local fallback is included, label it clearly as a development mode.

#### Redis

Redis stores distributed rate limit state.

Document key structure and expiration behavior.

Define what happens if Redis becomes unavailable.

Choose fail open or fail closed deliberately for each relevant class of
traffic and document the tradeoff.

Do not leave this behavior accidental.

#### Prometheus

Collect:

Envoy downstream request count

Response code classes

429 count

5xx count

Upstream request latency

Downstream request latency

Rate limit decisions

Rate limit service latency

Healthy upstream count

Connection counts where useful

#### Grafana

Provision dashboards as code.

Do not require manual dashboard construction.

Create panels for:

Traffic rate

p50 latency

p95 latency

p99 latency

429 rate

5xx rate

Upstream health

Rate limit decisions

Rate limit service latency

Optional connection metrics

Add useful thresholds only when they have a reason.

### Terraform Deployment

Use Terraform for a minimal AWS validation deployment.

The cloud deployment should include only what is necessary to prove the
architecture.

Potential components:

VPC

Public subnets

Security groups

NLB

Compute for Envoy and supporting services

CloudWatch integration where useful

Avoid expensive infrastructure that does not strengthen the
demonstration.

If ECS is used, justify it.

If EC2 is simpler and cheaper for the validation path, it is acceptable.

Prefer architectural clarity and cost control over maximizing AWS
service count.

## Suggested Repository Structure

``` text
breakwater/
  README.md
  LICENSE
  Makefile
  docker-compose.yml
  .env.example
  .gitignore
  .github/
    workflows/
      ci.yml
      deploy.yml
  envoy/
    envoy.yaml
    tls/
      README.md
  services/
    upstream/
      app/
      tests/
    rate_limit/
      app/
      tests/
  load/
    k6/
      baseline.js
      mixed_traffic.js
      abusive_client.js
      upstream_failure.js
      saturation.js
    results/
      README.md
  observability/
    prometheus/
      prometheus.yml
    grafana/
      provisioning/
      dashboards/
  terraform/
    modules/
      network/
      nlb/
      compute/
      observability/
    environments/
      dev/
      staging/
  tests/
    integration/
    failure/
  scripts/
    generate_local_certs.sh
    benchmark.sh
    compare_latency.py
    inject_failure.sh
  docs/
    architecture.md
    benchmark_methodology.md
    failure_model.md
    threat_model.md
    operations.md
    adr/
```

## Routing Requirements

Support at minimum:

Host based routing between two logical applications

Path based routing between API versions

Default route behavior

Explicit unknown host behavior

Explicit unknown path behavior

Health check endpoint behavior

The README should include a routing table.

## TLS Requirements

Use TLS locally with generated development certificates.

Document clearly that local certificates are development only.

For cloud validation, use an appropriate certificate strategy.

Measure TLS behavior separately from application behavior where useful.

Be prepared to explain:

Where TLS terminates

Why it terminates there

What traffic exists between Envoy and upstreams

How internal encryption would be added

Certificate rotation strategy

Failure behavior for invalid or expired certificates

## Rate Limiting Requirements

Implement a real distributed limiter using Redis.

Use token bucket semantics.

A client identity for the demonstration may be derived from a controlled
request header or another explicit identifier.

Do not claim the demonstration header is production identity.

Test:

Normal client under limit

Client at limit

Client exceeding limit

Burst behavior

Multiple Envoy instances sharing Redis state if practical

Redis unavailable

Rate limit service slow

Rate limit service unavailable

The system should make the chosen failure policy visible.

## Failure Model

Breakwater must be intentionally breakable.

Create repeatable failure scenarios.

### Upstream Failure

Terminate one upstream.

Observe health checks.

Verify traffic no longer routes to the unhealthy instance.

Record recovery behavior when it returns.

### Slow Upstream

Inject latency.

Measure how edge latency and upstream latency differ.

Verify timeout behavior.

### Upstream 5xx

Return controlled 5xx responses.

Verify metrics and dashboard visibility.

### Redis Failure

Stop Redis.

Verify the documented limiter failure policy.

### Rate Limit Service Failure

Stop or delay the service.

Verify Envoy behavior.

### Envoy Restart

Restart the edge tier during traffic.

Measure connection and request impact.

### Traffic Spike

Increase load rapidly.

Observe saturation behavior.

Do not claim graceful shedding unless the benchmark demonstrates it.

## Benchmark Methodology

This section is critical.

Do not optimize for a resume number.

Optimize for a benchmark another engineer can reproduce.

### Baseline

Measure the upstream directly without Envoy.

Record:

Throughput

p50

p95

p99

Error rate

CPU and memory if practical

### Edge Test

Run the same workload through Envoy with rate limiting disabled.

Calculate edge added latency.

### Rate Limit Test

Enable the rate limit service.

Run compliant traffic.

Measure additional latency.

### Mixed Traffic Test

Generate:

Compliant clients

Bursting clients

Abusive clients

Verify that abusive traffic receives 429 responses while compliant
traffic remains healthy.

### Failure Test

Inject upstream failures during load.

Measure:

5xx behavior

Recovery time

Healthy upstream count

Latency impact

### Saturation Test

Increase request rate gradually.

Identify the point where latency or errors rise materially.

Do not report the last request rate the tool happened to send.

Report a sustained operating point with an explicit success criterion.

### Benchmark Environment

Every published result must record:

Date

Git commit

Machine or cloud instance type

CPU

Memory

Operating system

Envoy version

Redis version

Python version

k6 version

Number of Envoy instances

Number of upstream instances

Test duration

Virtual users or arrival rate

TLS enabled or disabled

Rate limiting enabled or disabled

Keep raw benchmark outputs.

## Resume Metric Rule

The draft resume previously referenced a target such as twenty thousand
requests per second and less than four milliseconds of added p99
latency.

Treat those as hypotheses until measured.

After implementation, replace them with actual results.

If the measured result is lower, use the lower result.

Never manipulate the benchmark solely to preserve a resume claim.

## Observability Requirements

Metrics alone are not enough.

Create a dashboard that lets an operator answer:

Is traffic arriving?

Are clients being throttled?

Are upstreams healthy?

Are errors originating at the edge or upstream?

Is latency coming from Envoy, the rate limit service, or the
application?

Did a deployment change behavior?

Use structured Envoy access logs.

Include correlation identifiers where practical.

## Security Requirements

No private keys committed to Git.

Development certificates must be generated locally.

Restrict exposed ports.

Use explicit security groups in AWS.

Do not expose Redis publicly.

Do not expose Prometheus or Grafana publicly in the AWS demonstration
unless access is deliberately protected.

Document trust boundaries.

Document client identity limitations in the demo.

Document rate limiting bypass considerations.

Create `docs/threat_model.md`.

## Testing Strategy

### Unit Tests

Rate limiter token accounting

Configuration parsing

Client identity extraction

Failure policy behavior

Upstream control endpoints

### Integration Tests

TLS handshake

Host routing

Path routing

429 behavior

Shared Redis state

Health based upstream removal

Recovery after upstream return

Timeout behavior

Metrics availability

### Failure Tests

Redis unavailable

Rate limit service unavailable

Rate limit service latency

Upstream unavailable

Upstream slow

Envoy restart

Malformed request

Invalid host

### Configuration Validation

Run Envoy configuration validation in CI.

Validate Prometheus configuration.

Validate Grafana provisioning files where practical.

Validate Terraform.

## CI Pipeline

Every pull request should run:

Python formatting and linting

Python tests

Envoy configuration validation

Docker image builds

Integration tests through Docker Compose

Terraform format

Terraform validate

tflint if used

Security scanning where lightweight and useful

The deployment workflow should require explicit approval for AWS.

## Local Developer Experience

A reviewer should be able to clone the repository and run a documented
command to start:

Envoy

Redis

Rate limit service

Two upstream versions

Prometheus

Grafana

Then another command should run smoke tests.

Then another command should run a short benchmark.

Keep the local demonstration reliable.

## AWS Cost Discipline

The project should be cheap to validate.

Avoid NAT Gateway.

Avoid unnecessary managed databases.

Redis does not need to be ElastiCache merely to prove distributed rate
limiting.

A small compute deployment is sufficient.

Destroy resources after validation.

Tag resources.

Provide `make destroy` or an equivalent documented command.

Document likely billable resources before deployment.

## Git History Plan

Suggested progression:

1.  Repository skeleton and architecture

2.  Sample upstream service

3.  Basic Envoy reverse proxy

4.  TLS termination

5.  Host and path routing

6.  Health checks and upstream failure handling

7.  Redis backed rate limit service

8.  Envoy rate limit integration

9.  Prometheus metrics

10. Grafana provisioning

11. Structured access logging

12. Baseline k6 benchmark

13. Mixed traffic benchmark

14. Failure injection suite

15. Terraform network module

16. AWS NLB deployment

17. CI validation

18. Benchmark documentation

19. Threat model and operations guide

20. Final README and demo assets

Do not squash the entire development story into one artificial commit.

## Public README Requirements

The public README should open with the engineering problem, not a
technology list.

It should contain:

Architecture diagram

Request flow

Supported routing behavior

Rate limit model

Failure policy table

Local quick start

Benchmark methodology

Actual benchmark results

Grafana screenshot

Failure injection example

AWS deployment overview

Testing commands

Security considerations

Tradeoffs

Known limitations

Future work

Do not say the project was created to match a job description.

Do not present unmeasured targets as achieved results.

## Architecture Diagram

Use Mermaid.

Show:

Client

NLB for cloud path

Envoy

Rate limit service

Redis

Upstream version A

Upstream version B

Prometheus

Grafana

Make the traffic path visually distinct from the metrics path using
labels rather than decorative complexity.

## Senior Engineer Review Bar

A strong reviewer should be able to see:

A clear separation between edge responsibilities and application
responsibilities

An explicit rate limiting algorithm

A documented failure policy

Reproducible performance measurement

Meaningful failure injection

Useful observability

Infrastructure that can be recreated

No unexplained cloud complexity

No magical benchmark numbers

A credible security model

Clear operational tradeoffs

## Interview Defense

Be prepared to explain:

Why Envoy rather than NGINX or HAProxy

L4 versus L7 load balancing

What the NLB does versus what Envoy does

Where TLS terminates and why

How Envoy selects upstreams

How health checking differs from passive failure detection

How token bucket rate limiting works

Why Redis is needed

What happens if Redis is unavailable

Fail open versus fail closed tradeoffs

How retries can amplify failures

Why some requests should not be retried

How timeouts are selected

How connection reuse affects latency

How p99 differs from p50 and why it matters

How you isolated edge added latency

How k6 generated traffic

Where the benchmark bottleneck actually was

How you would scale Envoy horizontally

How shared rate limits behave across replicas

How you would defend against abusive clients at larger scale

How observability distinguishes edge errors from upstream errors

How configuration rollout could be made safer

How certificate rotation would work

## Definition of Done

Breakwater is complete only when:

Local TLS works

Host routing works

Path routing works

Redis backed distributed rate limiting works

429 behavior is tested

Health based upstream removal works

Failure recovery works

Prometheus metrics are exposed

Grafana dashboards are provisioned automatically

k6 benchmark scenarios run from a clean checkout

Baseline and edge measurements are recorded

Edge added latency is calculated

Failure injection tests run

Terraform deployment is validated

AWS resources can be destroyed cleanly

CI validates the repository

The public README contains actual evidence

No performance claim is invented

## Cursor Working Rules

Build in small coherent phases.

Keep configuration readable.

Prefer explicit behavior over hidden magic.

Do not add technologies merely to make the stack look impressive.

Do not fabricate benchmark output.

Do not call a mocked path production complete.

Do not commit credentials, certificates, or private keys.

Keep local development cheap and deterministic.

After each phase:

Format

Lint

Test

Update relevant documentation

Commit coherently

Before declaring completion, clone the repository into a clean
environment and run the documented setup, smoke tests, failure tests,
and benchmark workflow.
