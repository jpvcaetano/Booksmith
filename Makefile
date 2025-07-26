.PHONY: help install dev-install run test format lint format-check clean notebook build export-requirements

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install project dependencies
	poetry install --no-dev

dev-install: ## Install with development dependencies
	poetry install

run-api: ## Start the API server (development mode)
	poetry run python run_api.py

test: ## Run all tests
	poetry run pytest tests/ -v

format: ## Format code with black and isort
	poetry run black booksmith/ tests/ run_api.py
	poetry run isort booksmith/ tests/ run_api.py

lint: ## Run type checking with mypy
	poetry run mypy booksmith/

export-requirements: ## Export requirements.txt from Poetry
	poetry export --without-hashes --format=requirements.txt > requirements.txt
	poetry export --with dev --without-hashes --format=requirements.txt > requirements-dev.txt

clean: ## Remove build artifacts and cache files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ .coverage htmlcov/ 