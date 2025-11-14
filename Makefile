.PHONY: help install dev test lint format run migrate dashboard apify-list apify-download apify-download-run venv-check venv

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

venv: ## Create virtual environment using uv
	@which uv > /dev/null || (echo "ERROR: uv not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
	uv venv .venv
	@echo "Virtual environment created at .venv/. Activate with: source .venv/bin/activate"

venv-check: ## Check if virtual environment is activated or exists
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -c "import sys; sys.exit(0)" 2>/dev/null || (echo "ERROR: .venv exists but python not found. Run: source .venv/bin/activate" && exit 1); \
	else \
		python -c "import sys; sys.exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)" 2>/dev/null || (echo "ERROR: Virtual environment not activated. Run: source .venv/bin/activate or make venv" && exit 1); \
	fi

install: ## Install dependencies using uv
	@which uv > /dev/null || (echo "ERROR: uv not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
	@if [ ! -d ".venv" ]; then uv venv .venv; fi
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && uv pip install -r requirements.txt && playwright install chromium; \
	else \
		echo "ERROR: Failed to create .venv"; \
		exit 1; \
	fi

dev: ## Install development dependencies using uv
	@which uv > /dev/null || (echo "ERROR: uv not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
	@if [ ! -d ".venv" ]; then uv venv .venv; fi
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && uv pip install -r requirements.txt && \
		uv pip install pytest pytest-asyncio black ruff mypy && \
		playwright install chromium; \
	else \
		echo "ERROR: Failed to create .venv"; \
		exit 1; \
	fi

test: venv-check ## Run tests
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pytest tests/ -v; \
	else \
		pytest tests/ -v; \
	fi

test-cov: venv-check ## Run tests with coverage
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pytest tests/ --cov=app --cov-report=html --cov-report=term; \
	else \
		pytest tests/ --cov=app --cov-report=html --cov-report=term; \
	fi

test-watch: venv-check ## Run tests in watch mode
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && pytest-watch tests/; \
	else \
		pytest-watch tests/; \
	fi

lint: venv-check ## Run linter
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && ruff check app/; \
	else \
		ruff check app/; \
	fi

format: venv-check ## Format code
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && black app/ tests/; \
	else \
		black app/ tests/; \
	fi

run: venv-check ## Run the FastAPI server
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000; \
	else \
		uvicorn app.main:app --reload --host 0.0.0.0 --port 8000; \
	fi

migrate: venv-check ## Run database migrations
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && alembic upgrade head; \
	else \
		alembic upgrade head; \
	fi

migrate-create: venv-check ## Create a new migration (use MESSAGE="description")
	@if [ -z "$(MESSAGE)" ]; then \
		read -p "Migration message: " msg; \
		if [ -d ".venv" ]; then \
			. .venv/bin/activate && alembic revision --autogenerate -m "$$msg"; \
		else \
			alembic revision --autogenerate -m "$$msg"; \
		fi; \
	else \
		if [ -d ".venv" ]; then \
			. .venv/bin/activate && alembic revision --autogenerate -m "$(MESSAGE)"; \
		else \
			alembic revision --autogenerate -m "$(MESSAGE)"; \
		fi; \
	fi

dashboard: venv-check ## Run the terminal dashboard
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python -m app.dashboard.dashboard; \
	else \
		python -m app.dashboard.dashboard; \
	fi

setup-db: venv-check ## Set up database (create tables)
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && alembic upgrade head; \
	else \
		alembic upgrade head; \
	fi

init: ## Initial setup (create venv + install + setup database)
	@which uv > /dev/null || (echo "ERROR: uv not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh" && exit 1)
	@if [ ! -d ".venv" ]; then uv venv .venv; fi
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && uv pip install -r requirements.txt && \
		playwright install chromium && \
		echo ""; \
		echo "✓ Dependencies installed successfully!"; \
		echo "Attempting database migrations..."; \
		set +e; \
		timeout 5 bash -c '. .venv/bin/activate && alembic upgrade head' 2>&1 | head -3 || true; \
		MIGRATE_EXIT=$$?; \
		set -e; \
		if [ $$MIGRATE_EXIT -eq 0 ] || [ $$MIGRATE_EXIT -eq 124 ]; then \
			if [ $$MIGRATE_EXIT -eq 124 ]; then \
				echo "⚠ Database connection timeout (this is OK if DATABASE_URL is not configured)"; \
			else \
				echo "✓ Database migrations completed successfully"; \
			fi; \
		else \
			echo "⚠ WARNING: Database migrations failed (this is OK if DATABASE_URL is not configured)"; \
		fi; \
		echo "  Run 'make migrate' later after setting DATABASE_URL in .env"; \
		echo ""; \
		echo "Setup complete! Activate virtual environment with: source .venv/bin/activate"; \
	else \
		echo "ERROR: Failed to create .venv"; \
		exit 1; \
	fi

# Apify commands
apify-list: venv-check ## List previous Apify towing runs
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/download_apify_runs.py --list-only; \
	else \
		python scripts/download_apify_runs.py --list-only; \
	fi

apify-download: venv-check ## Download all previous Apify towing data (use LIMIT_RUNS=N to set limit, default: 10)
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/download_apify_runs.py --limit-runs $(or $(LIMIT_RUNS),10) --output towing_data.json; \
	else \
		python scripts/download_apify_runs.py --limit-runs $(or $(LIMIT_RUNS),10) --output towing_data.json; \
	fi

    apify-download-run: venv-check ## Download specific Apify run (use RUN_ID=id to specify)
	@if [ -z "$(RUN_ID)" ]; then \
		echo "ERROR: RUN_ID not set. Usage: make apify-download-run RUN_ID=your_run_id"; \
		exit 1; \
	fi
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/download_apify_runs.py --run-id $(RUN_ID) --output run_$(RUN_ID).json; \
	else \
		python scripts/download_apify_runs.py --run-id $(RUN_ID) --output run_$(RUN_ID).json; \
	fi

apify-import-to-supabase: venv-check ## Import Apify data to Supabase (use ZONE_ID=uuid LIMIT_RUNS=N LIMIT_ITEMS=N)
	@if [ -z "$(ZONE_ID)" ]; then \
		echo "ERROR: ZONE_ID not set. Usage: make apify-import-to-supabase ZONE_ID=your_zone_uuid"; \
		echo "First, list zones or create one, then use its UUID"; \
		exit 1; \
	fi
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/import_apify_to_supabase.py --zone-id $(ZONE_ID) --limit-runs $(or $(LIMIT_RUNS),10) --limit-items $(or $(LIMIT_ITEMS),); \
	else \
		python scripts/import_apify_to_supabase.py --zone-id $(ZONE_ID) --limit-runs $(or $(LIMIT_RUNS),10) --limit-items $(or $(LIMIT_ITEMS),); \
	fi

list-zones: venv-check ## List all zones in the database
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/list_zones.py; \
	else \
		python scripts/list_zones.py; \
	fi

query-companies: venv-check ## Query and analyze company data (use ZONE_ID=uuid STATE=XX HAS_IMPOUND=true)
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/query_companies.py \
			$(if $(ZONE_ID),--zone-id $(ZONE_ID)) \
			$(if $(STATE),--state $(STATE)) \
			$(if $(HAS_IMPOUND),--has-impound) \
			--limit $(or $(LIMIT),100); \
	else \
		python scripts/query_companies.py \
			$(if $(ZONE_ID),--zone-id $(ZONE_ID)) \
			$(if $(STATE),--state $(STATE)) \
			$(if $(HAS_IMPOUND),--has-impound) \
			--limit $(or $(LIMIT),100); \
	fi

analyze-data: venv-check ## Analyze imported company data (use STATE=XX HAS_IMPOUND=true)
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/analyze_imported_data.py \
			$(if $(STATE),--state $(STATE)) \
			$(if $(HAS_IMPOUND),--has-impound); \
	else \
		python scripts/analyze_imported_data.py \
			$(if $(STATE),--state $(STATE)) \
			$(if $(HAS_IMPOUND),--has-impound); \
	fi

import-from-json: venv-check ## Import companies from all_towing_leads.json (use JSON_FILE=path/to/file.json)
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/import_from_json.py \
			$(if $(JSON_FILE),--json-file $(JSON_FILE)); \
	else \
		python scripts/import_from_json.py \
			$(if $(JSON_FILE),--json-file $(JSON_FILE)); \
	fi

monitor-import: venv-check ## Monitor import progress in real-time (use INTERVAL=N for update interval)
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/monitor_import.py \
			$(if $(INTERVAL),--interval $(INTERVAL)); \
	else \
		python scripts/monitor_import.py \
			$(if $(INTERVAL),--interval $(INTERVAL)); \
	fi

import-contact-enrichment: venv-check ## Import contact enrichment data (use RUN_ID=apify_run_id DRY_RUN=true for preview)
	@if [ -z "$(RUN_ID)" ]; then \
		echo "ERROR: RUN_ID not set. Usage: make import-contact-enrichment RUN_ID=your_run_id"; \
		exit 1; \
	fi
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/import_contact_enrichment.py --run-id $(RUN_ID) $(if $(DRY_RUN),--dry-run); \
	else \
		python scripts/import_contact_enrichment.py --run-id $(RUN_ID) $(if $(DRY_RUN),--dry-run); \
	fi

run-impound-crawls: venv-check ## Run impound-focused crawls for Baltimore MD, Jacksonville NC, and Florida (use MAX_RESULTS=N to override)
	@if [ -d ".venv" ]; then \
		. .venv/bin/activate && python scripts/run_impound_crawls.py $(if $(MAX_RESULTS),--max-results $(MAX_RESULTS)); \
	else \
		python scripts/run_impound_crawls.py $(if $(MAX_RESULTS),--max-results $(MAX_RESULTS)); \
	fi

# Docker commands
docker-build: ## Build Docker image
	docker build -t towpilot-scraper .

docker-run: ## Run Docker container
	docker run -p 8000:8000 --env-file .env towpilot-scraper

# Cloud Run commands
cloud-build: ## Build for Cloud Run (use PROJECT_ID=id)
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set. Usage: make cloud-build PROJECT_ID=your_project_id"; \
		exit 1; \
	fi
	gcloud builds submit --tag gcr.io/$(PROJECT_ID)/towpilot-scraper

cloud-deploy: ## Deploy to Cloud Run (use PROJECT_ID=id)
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "ERROR: PROJECT_ID not set. Usage: make cloud-deploy PROJECT_ID=your_project_id"; \
		exit 1; \
	fi
	gcloud run deploy towpilot-scraper \
		--image gcr.io/$(PROJECT_ID)/towpilot-scraper \
		--platform managed \
		--region us-central1 \
		--allow-unauthenticated
