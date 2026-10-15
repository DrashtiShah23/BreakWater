# Breakwater — common developer entry points (zero-cost local path).

UPSTREAM_DIR := services/upstream
# Prefer the upstream local venv when present (created via pip install -e ".[dev]").
UPSTREAM_PYTHON := $(wildcard $(UPSTREAM_DIR)/.venv/bin/python)
PYTHON ?= $(if $(UPSTREAM_PYTHON),$(abspath $(UPSTREAM_PYTHON)),python3)
COMPOSE ?= docker compose
ENVOY_IMAGE ?= envoyproxy/envoy:v1.31.5
ENVOY_HTTP_PORT ?= 8080
ENVOY_ADMIN_PORT ?= 9901

.PHONY: help bootstrap certs up up-upstream down smoke test test-upstream \
	test-integration bench fail inject-failure fmt lint validate-envoy \
	validate-terraform plan apply destroy clean

help:
	@echo "Breakwater targets"
	@echo ""
	@echo "  make bootstrap            Local setup checks"
	@echo "  make up                   Start Envoy + upstreams (Compose)"
	@echo "  make up-upstream          Start upstream services only"
	@echo "  make down                 Stop Compose stack"
	@echo "  make validate-envoy       Envoy --mode validate (CI-friendly)"
	@echo "  make smoke                Functional smoke via Envoy (not a benchmark)"
	@echo "  make test                 Upstream unit tests"
	@echo "  make test-integration     Compose edge integration tests"
	@echo "  make fmt lint             Format and lint upstream Python"
	@echo "  make certs                Generate development TLS material (M4)"
	@echo "  make bench                k6 benchmark workflow (M12+)"
	@echo "  make fail                 Failure injection helper notes"
	@echo "  make validate-terraform   Terraform fmt/validate (M15+)"
	@echo "  make plan apply destroy   Optional AWS only (not DoD)"
	@echo "  make clean                Remove local generated artifacts"
	@echo ""
	@echo "Data traffic  = client requests through Envoy :$(ENVOY_HTTP_PORT)"
	@echo "Control       = Envoy admin :$(ENVOY_ADMIN_PORT), /__test__/*, health probes"

bootstrap:
	@test -f .env.example
	@test -f docs/architecture.md
	@test -f LICENSE
	@test -f $(UPSTREAM_DIR)/pyproject.toml
	@test -f envoy/envoy.yaml
	@echo "bootstrap checks: ok"
	@echo "Copy .env.example to .env if needed. Stack: make up"

certs:
	@echo "TODO(M4): scripts/generate_local_certs.sh"

up:
	$(COMPOSE) build upstream-api
	$(COMPOSE) up -d upstream-api upstream-status envoy

up-upstream:
	$(COMPOSE) build upstream-api
	$(COMPOSE) up -d upstream-api upstream-status

down:
	$(COMPOSE) down

validate-envoy:
	@echo "Validating envoy/envoy.yaml with $(ENVOY_IMAGE) --mode validate"
	docker run --rm \
		-v "$(CURDIR)/envoy/envoy.yaml:/etc/envoy/envoy.yaml:ro" \
		$(ENVOY_IMAGE) \
		--mode validate \
		-c /etc/envoy/envoy.yaml

smoke:
	@echo "Functional smoke (not a benchmark): data path via Envoy"
	@curl -sf "http://127.0.0.1:$(ENVOY_ADMIN_PORT)/ready" >/dev/null
	@curl -sf "http://127.0.0.1:$(ENVOY_HTTP_PORT)/health" | $(PYTHON) -m json.tool
	@curl -sf "http://127.0.0.1:$(ENVOY_HTTP_PORT)/api/v1/items" | $(PYTHON) -m json.tool
	@curl -sf "http://127.0.0.1:$(ENVOY_HTTP_PORT)/api/v2/items" | $(PYTHON) -m json.tool
	@echo "unknown path (expect 404 from edge):"
	@curl -s -o /dev/null -w "HTTP %{http_code}\n" "http://127.0.0.1:$(ENVOY_HTTP_PORT)/nope"
	@echo "direct upstream baseline still available on :$${UPSTREAM_API_PORT:-9001}"

test test-upstream:
	cd $(UPSTREAM_DIR) && $(PYTHON) -m pytest -q

test-integration:
	@echo "Requires: make up (Envoy + upstreams). Skipping is not a pass."
	$(PYTHON) -m pytest -q tests/integration -m "not slow"
	@echo "Optional upstream-down path: $(PYTHON) -m pytest -q tests/integration -m slow"

bench:
	@echo "TODO(M12): baseline → Envoy (no RL) → Envoy (RL); calculate edge overhead"

fail inject-failure:
	@echo "Upstream controls (local, ENABLE_TEST_CONTROLS=true):"
	@echo "  curl -X POST http://127.0.0.1:9001/__test__/latency -H 'content-type: application/json' -d '{\"delay_ms\":200}'"
	@echo "  curl -X POST http://127.0.0.1:9001/__test__/errors -H 'content-type: application/json' -d '{\"mode\":\"http_500\",\"count\":5}'"
	@echo "  curl -X POST http://127.0.0.1:9001/__test__/health -H 'content-type: application/json' -d '{\"healthy\":false}'"
	@echo "  curl -X POST http://127.0.0.1:9001/__test__/reset"
	@echo "Then observe data-plane effect via Envoy: curl http://127.0.0.1:$(ENVOY_HTTP_PORT)/api/v1/items"

fmt:
	cd $(UPSTREAM_DIR) && $(PYTHON) -m ruff format app tests
	cd $(UPSTREAM_DIR) && $(PYTHON) -m ruff check --select I --fix app tests
	$(PYTHON) -m ruff format tests/integration
	$(PYTHON) -m ruff check --select I --fix tests/integration

lint:
	cd $(UPSTREAM_DIR) && $(PYTHON) -m ruff check app tests
	$(PYTHON) -m ruff check tests/integration

validate-terraform:
	@echo "TODO(M15): terraform fmt -check && terraform validate"

plan:
	@echo "TODO(M15): terraform plan against fixtures/static validation (zero-cost)."
	@echo "Real AWS plan/apply is OPTIONAL and outside Definition of Done."

apply:
	@echo "OPTIONAL ONLY — not required for project completion."
	@echo "TODO(M16): refuse unless BREAKWATER_ALLOW_AWS_SPEND=1; warn about billable resources."
	@echo "Do not treat Free Tier as free. Prefer: make test / local Compose."

destroy:
	@echo "OPTIONAL ONLY — for voluntary AWS apply cleanup (M16 runbook)."
	@echo "Required path never creates cloud resources to destroy."

clean:
	@echo "Removing common local artifacts (safe defaults)..."
	@rm -rf $(UPSTREAM_DIR)/.pytest_cache $(UPSTREAM_DIR)/.ruff_cache $(UPSTREAM_DIR)/.venv
	@rm -rf $(UPSTREAM_DIR)/app.egg-info $(UPSTREAM_DIR)/*.egg-info
	@rm -rf .pytest_cache
	@find $(UPSTREAM_DIR) tests -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "clean: done"
