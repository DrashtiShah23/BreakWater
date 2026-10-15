# Breakwater — common developer entry points.
# Prefer: make <target> over memorizing docker/compose invocations.

UPSTREAM_DIR := services/upstream
# Prefer the upstream local venv when present (created via pip install -e ".[dev]").
UPSTREAM_PYTHON := $(wildcard $(UPSTREAM_DIR)/.venv/bin/python)
PYTHON ?= $(if $(UPSTREAM_PYTHON),$(abspath $(UPSTREAM_PYTHON)),python3)
COMPOSE ?= docker compose

.PHONY: help bootstrap certs up up-upstream down smoke test test-upstream \
	bench fail inject-failure fmt lint validate-envoy validate-terraform \
	plan apply destroy clean

help:
	@echo "Breakwater targets"
	@echo ""
	@echo "  make bootstrap          Local setup checks"
	@echo "  make up / up-upstream   Start upstream services (Compose)"
	@echo "  make down               Stop Compose stack"
	@echo "  make test / test-upstream  Upstream unit+integration tests"
	@echo "  make fmt lint           Format and lint upstream Python"
	@echo "  make certs              Generate development TLS material (M4)"
	@echo "  make smoke              Smoke through Envoy (M3+)"
	@echo "  make bench              k6 benchmark workflow (M12+)"
	@echo "  make fail               Failure injection helper (M6/M14)"
	@echo "  make validate-envoy     Envoy config validation (M3+)"
	@echo "  make validate-terraform Terraform fmt/validate (M15+)"
	@echo "  make plan apply destroy AWS validation lifecycle (M16)"
	@echo "  make clean              Remove local generated artifacts"
	@echo ""
	@echo "Data traffic = client requests through Envoy (later) / upstreams (now)."
	@echo "Control traffic = health, /__test__ controls, metrics (later)."

bootstrap:
	@test -f .env.example
	@test -f docs/architecture.md
	@test -f LICENSE
	@test -f $(UPSTREAM_DIR)/pyproject.toml
	@echo "bootstrap checks: ok"
	@echo "Copy .env.example to .env if needed. Upstream: make up-upstream"

certs:
	@echo "TODO(M4): scripts/generate_local_certs.sh"

up up-upstream:
	$(COMPOSE) up --build -d upstream-api upstream-status

down:
	$(COMPOSE) down

smoke:
	@echo "TODO(M3+): smoke tests against local Envoy"
	@echo "Upstream-only smoke (no Envoy):"
	@curl -sf "http://127.0.0.1:$${UPSTREAM_API_PORT:-9001}/health" | $(PYTHON) -m json.tool
	@curl -sf "http://127.0.0.1:$${UPSTREAM_API_PORT:-9001}/api/v1/items" | $(PYTHON) -m json.tool
	@curl -sf "http://127.0.0.1:$${UPSTREAM_STATUS_PORT:-9002}/api/v1/status" | $(PYTHON) -m json.tool

test test-upstream:
	cd $(UPSTREAM_DIR) && $(PYTHON) -m pytest -q

bench:
	@echo "TODO(M12): baseline → Envoy (no RL) → Envoy (RL); calculate edge overhead"

fail inject-failure:
	@echo "TODO(M6/M14): scripts/inject_failure.sh"
	@echo "Upstream controls (local, ENABLE_TEST_CONTROLS=true):"
	@echo "  curl -X POST http://127.0.0.1:9001/__test__/latency -H 'content-type: application/json' -d '{\"delay_ms\":200}'"
	@echo "  curl -X POST http://127.0.0.1:9001/__test__/errors -H 'content-type: application/json' -d '{\"mode\":\"http_500\",\"count\":5}'"
	@echo "  curl -X POST http://127.0.0.1:9001/__test__/health -H 'content-type: application/json' -d '{\"healthy\":false}'"
	@echo "  curl -X POST http://127.0.0.1:9001/__test__/reset"

fmt:
	cd $(UPSTREAM_DIR) && $(PYTHON) -m ruff format app tests
	cd $(UPSTREAM_DIR) && $(PYTHON) -m ruff check --select I --fix app tests

lint:
	cd $(UPSTREAM_DIR) && $(PYTHON) -m ruff check app tests

validate-envoy:
	@echo "TODO(M3): envoy config validate"

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
	@find $(UPSTREAM_DIR) -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "clean: done"
