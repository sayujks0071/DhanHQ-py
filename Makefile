.PHONY: help install dev-install clean lint test test-cov format check-format ingest research run-paper run-live report

help: ## Show this help message
	@echo "Liquid F&O Trading System - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -e .

dev-install: ## Install development dependencies
	pip install -e ".[dev]"
	pre-commit install

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint: ## Run linting checks
	black --check src/ tests/
	isort --check-only src/ tests/
	mypy src/

format: ## Format code
	black src/ tests/
	isort src/ tests/

check-format: ## Check code formatting
	black --check src/ tests/
	isort --check-only src/ tests/

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

ingest: ## Build F&O universe and cache historical data
	python -m src.cli ingest

research: ## Run walk-forward optimization and strategy ranking
	python -m src.cli research

run-paper: ## Start paper trading engine with dashboard
	python -m src.cli run-paper

run-live: ## Start live trading engine (requires ENABLE_LIVE=true)
	python -m src.cli run-live

report: ## Generate EOD report
	python -m src.cli report

setup-env: ## Create .env file from template
	cp .env.example .env
	@echo "Please edit .env with your credentials"

docker-build: ## Build Docker image
	docker build -t liquid-fo-trading .

docker-run: ## Run in Docker container
	docker run -d --name liquid-fo-trading --env-file .env -p 8787:8787 liquid-fo-trading

docker-stop: ## Stop Docker container
	docker stop liquid-fo-trading
	docker rm liquid-fo-trading

# Development helpers
dev-setup: dev-install setup-env ## Complete development setup
	@echo "Development environment ready!"
	@echo "1. Edit .env with your credentials"
	@echo "2. Run 'make ingest' to build universe"
	@echo "3. Run 'make research' to backtest strategies"
	@echo "4. Run 'make run-paper' to start paper trading"

# Production deployment
prod-deploy: clean install ## Production deployment
	@echo "Production deployment ready!"
	@echo "Ensure ENABLE_LIVE=true in .env for live trading"
