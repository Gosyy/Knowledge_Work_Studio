PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
UVICORN ?= $(PYTHON) -m uvicorn

.PHONY: install run test lint create-dirs deploy-preflight operator-smoke

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
