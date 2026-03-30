.PHONY: up down logs install dev-ingestion dev-reasoning dev-persona dev-dashboard test lint typecheck

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

install:
	cd shared && pip install -e ".[dev]"
	cd services/ingestion && pip install -e ".[dev]"
	cd services/reasoning && pip install -e ".[dev]"
	cd services/persona && pip install -e ".[dev]"
	cd services/dashboard && pip install -e ".[dev]"
	cd frontend && npm install
	cd infra && npm install

dev-ingestion:
	cd services/ingestion && uvicorn app.main:app --reload --port 8000

dev-reasoning:
	cd services/reasoning && uvicorn app.main:app --reload --port 8001

dev-persona:
	cd services/persona && uvicorn app.main:app --reload --port 8002

dev-dashboard:
	cd services/dashboard && uvicorn app.main:app --reload --port 8003

test:
	cd shared && python -m pytest tests/ -v
	cd services/ingestion && python -m pytest tests/ -v
	cd services/reasoning && python -m pytest tests/ -v
	cd services/persona && python -m pytest tests/ -v
	cd services/dashboard && python -m pytest tests/ -v
	cd frontend && npm test

lint:
	cd shared && ruff check .
	cd services/ingestion && ruff check .
	cd services/reasoning && ruff check .
	cd services/persona && ruff check .
	cd services/dashboard && ruff check .
	cd frontend && npx eslint src/

typecheck:
	cd shared && mypy crip_shared/
	cd services/ingestion && mypy app/
	cd services/reasoning && mypy app/
	cd services/persona && mypy app/
	cd services/dashboard && mypy app/
	cd frontend && npx tsc --noEmit
