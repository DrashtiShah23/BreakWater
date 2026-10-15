# Failure model

Draft placeholder — filled as Milestones 6 and 14 land.

Will document intentional, repeatable failure scenarios for upstreams,
Redis, rate-limit service, Envoy restart, and traffic spikes, including
standard (fail-open) vs sensitive (fail-closed) rate-limit outage behavior.

Distinguish impact on **data traffic** from loss of **control/observability**
visibility.
