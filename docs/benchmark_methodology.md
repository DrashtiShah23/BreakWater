# Benchmark methodology

Draft placeholder — filled in Milestone 12+.

Required order of measurement:

1. Direct upstream (no Envoy)
2. Envoy with rate limiting disabled
3. Envoy with rate limiting enabled

Edge-added latency is calculated from (1) vs (2). Rate-limit overhead from
(2) vs (3). Measure data traffic only; do not treat control/scrape traffic
as offered load.

Do not invent results in this document.
