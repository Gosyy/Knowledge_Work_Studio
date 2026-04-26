PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
UVICORN ?= $(PYTHON) -m uvicorn

.PHONY: install run test lint create-dirs deploy-preflight operator-smoke postgres-integration deploy-package-validate docker-build docker-up docker-down production-readiness

install:
	$(PIP) install -r requirements.txt

run:
	$(UVICORN) backend.app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	pytest -q

lint:
	$(PYTHON) -m compileall backend

create-dirs:
	mkdir -p storage/uploads storage/artifacts storage/temp storage/logs

deploy-preflight:
	$(PYTHON) scripts/kw_deployment_preflight.py --skip-tests --skip-frontend

operator-smoke:
	$(PYTHON) scripts/kw_operator_smoke.py --base-url http://localhost:8000

postgres-integration:
	$(PYTHON) scripts/kw_postgres_integration_gate.py --require-dsn

deploy-package-validate:
	$(PYTHON) scripts/kw_validate_deployment_package.py --repo-root .

docker-build:
	docker compose -f docker-compose.deploy.yml build

docker-up:
	docker compose -f docker-compose.deploy.yml up -d

docker-down:
	docker compose -f docker-compose.deploy.yml down

production-readiness:
	$(PYTHON) scripts/kw_production_readiness_gate.py --repo-root .
