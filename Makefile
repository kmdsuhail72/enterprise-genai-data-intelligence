.PHONY: help install install-dev test lint format run migrate docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       Install production dependencies"
	@echo "  make install-dev   Install development dependencies"
	@echo "  make test          Run pytest suite"
	@echo "  make lint          Run ruff code linter"
	@echo "  make format        Format code with ruff"
	@echo "  make run           Run FastAPI development server"
	@echo "  make migrate       Run database migrations"
	@echo "  make docker-up     Start Docker Compose services"
	@echo "  make docker-down   Stop Docker Compose services"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

test:
	python -m pytest tests/unit -v

lint:
	ruff check src tests

format:
	ruff format src tests

run:
	uvicorn enterprise_ai.main:app --app-dir src --host 0.0.0.0 --port 8000 --reload

migrate:
	alembic upgrade head

docker-up:
	docker compose up -d

docker-down:
	docker compose down
