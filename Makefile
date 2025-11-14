.PHONY: help install dev test lint format run migrate dashboard

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	playwright install chromium

dev: ## Install development dependencies
	pip install -r requirements.txt
	playwright install chromium
	pip install pytest pytest-asyncio black ruff mypy

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=app --cov-report=html --cov-report=term

test-watch: ## Run tests in watch mode
	pytest-watch tests/

lint: ## Run linter
	ruff check app/

format: ## Format code
	black app/ tests/

run: ## Run the FastAPI server
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate: ## Run database migrations
	alembic upgrade head

migrate-create: ## Create a new migration
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

dashboard: ## Run the terminal dashboard
	python -m app.dashboard.dashboard

setup-db: ## Set up database (create tables)
	alembic upgrade head

init: install setup-db ## Initial setup (install + setup database)

docker-build: ## Build Docker image
	docker build -t towpilot-scraper .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env towpilot-scraper

cloud-build: ## Build for Cloud Run
	gcloud builds submit --tag gcr.io/$(PROJECT_ID)/towpilot-scraper

cloud-deploy: ## Deploy to Cloud Run
	gcloud run deploy towpilot-scraper \
		--image gcr.io/$(PROJECT_ID)/towpilot-scraper \
		--platform managed \
		--region us-central1 \
		--allow-unauthenticated

