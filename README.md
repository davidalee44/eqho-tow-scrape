# TowPilot Lead Scraper Backend

FastAPI backend for scraping and enriching towing company leads from Google Maps, with website scraping, lead enrichment, and multi-channel outreach automation.

## Features

- **Google Maps Scraping**: Uses Apify to crawl Google Maps for towing companies
- **Website Scraping**: Playwright-based scraping for hours of operation and impound service detection
- **Lead Enrichment**: Enriches company data from multiple sources (Google, Facebook, websites)
- **Zone-Based Targeting**: Organize companies by geographic zones (city/metro areas)
- **Multi-Channel Outreach**: Automated email/SMS/phone outreach with sequence management
- **Terminal Dashboard**: Real-time Textual-based dashboard with time period filtering
- **Scheduled Jobs**: Automated daily crawls, enrichment refreshes, and outreach processing

## Tech Stack

- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **ORM**: SQLAlchemy (async)
- **Migrations**: Alembic
- **Web Scraping**: Playwright
- **Background Jobs**: APScheduler
- **Terminal UI**: Textual
- **Deployment**: Google Cloud Run

## Setup

### Prerequisites

- Python 3.11+
- Supabase account and project
- Apify account and API token
- Google Cloud account (for Cloud Run deployment)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd eqho-tow-scrape
```

2. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
make install
# Or manually:
pip install -r requirements.txt
playwright install chromium
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables

Required environment variables (see `.env.example`):

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key (optional)
- `DATABASE_URL`: PostgreSQL connection string (from Supabase)
- `APIFY_TOKEN`: Your Apify API token

Optional:
- `EMAIL_PROVIDER_API_KEY`: For email sending
- `SMS_PROVIDER_API_KEY`: For SMS sending
- `PHONE_PROVIDER_API_KEY`: For phone calls
- `OUTREACH_WEBHOOK_URL`: Webhook URL for outreach system
- `PLAYWRIGHT_HEADLESS`: Run Playwright in headless mode (default: true)
- `PLAYWRIGHT_TIMEOUT`: Page load timeout in ms (default: 30000)
- `WEBSITE_SCRAPE_CONCURRENT`: Max concurrent scrapes (default: 5)
- `LOG_LEVEL`: Logging level (default: INFO)

### Database Setup

1. Create a Supabase project at https://supabase.com
2. Get your database connection string from Supabase dashboard
3. Update `DATABASE_URL` in `.env`
4. Run migrations:
```bash
make migrate
# Or manually:
alembic upgrade head
```

### Apify Setup

1. Sign up at https://apify.com
2. Get your API token from the Apify dashboard
3. Add `APIFY_TOKEN` to your `.env` file

## Usage

### Running the API Server

```bash
make run
# Or manually:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at http://localhost:8000

API documentation: http://localhost:8000/docs

### Running the Terminal Dashboard

```bash
make dashboard
# Or manually:
python -m app.dashboard.dashboard
```

Dashboard keyboard shortcuts:
- `t` - Today
- `y` - Yesterday
- `w` - This Week
- `l` - Last Week
- `m` - This Month
- `n` - Last Month
- `7` - Last 7 Days
- `1` - Last 14 Days
- `3` - Last 30 Days
- `r` - Refresh
- `q` - Quit

### Makefile Commands

```bash
make help          # Show all available commands
make install       # Install dependencies
make run           # Run the API server
make migrate       # Run database migrations
make dashboard     # Run terminal dashboard
make test          # Run tests
make lint          # Run linter
make format        # Format code
```

## API Endpoints

### Zones
- `POST /api/v1/zones` - Create zone
- `GET /api/v1/zones` - List zones
- `GET /api/v1/zones/{zone_id}` - Get zone details
- `PUT /api/v1/zones/{zone_id}` - Update zone
- `DELETE /api/v1/zones/{zone_id}` - Deactivate zone

### Companies
- `GET /api/v1/companies` - List/search companies (filters: zone_id, services, fleet_size, has_impound_service)
- `GET /api/v1/companies/{company_id}` - Get company details
- `PUT /api/v1/companies/{company_id}` - Update company
- `POST /api/v1/companies/bulk-import` - Bulk import companies

### Crawling
- `POST /api/v1/crawl/zone/{zone_id}` - Crawl a zone for companies
- `POST /api/v1/crawl/company/{company_id}` - Re-crawl a company

### Enrichment
- `POST /api/v1/enrichment/company/{company_id}` - Enrich a company
- `POST /api/v1/enrichment/bulk` - Bulk enrichment for a zone
- `GET /api/v1/enrichment/snapshots/{company_id}` - Get enrichment history
- `POST /api/v1/enrichment/scrape-website/{company_id}` - Scrape company website
- `POST /api/v1/enrichment/scrape-websites/zone/{zone_id}` - Batch website scraping

### Outreach
- `POST /api/v1/outreach/sequences` - Create outreach sequence
- `GET /api/v1/outreach/sequences` - List sequences
- `POST /api/v1/outreach/assign` - Assign company to sequence
- `POST /api/v1/outreach/send` - Send immediate outreach
- `GET /api/v1/outreach/history/{company_id}` - Get outreach history
- `PUT /api/v1/outreach/assignments/{assignment_id}/pause` - Pause assignment
- `PUT /api/v1/outreach/assignments/{assignment_id}/resume` - Resume assignment

## Deployment to Cloud Run

### Prerequisites

- Google Cloud SDK installed
- Project ID set: `gcloud config set project YOUR_PROJECT_ID`

### Build and Deploy

```bash
# Build and deploy using Cloud Build
make cloud-build
make cloud-deploy

# Or manually:
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/towpilot-scraper
gcloud run deploy towpilot-scraper \
  --image gcr.io/YOUR_PROJECT_ID/towpilot-scraper \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "DATABASE_URL=...,APIFY_TOKEN=..."
```

### Environment Variables in Cloud Run

Set environment variables in Cloud Run:
```bash
gcloud run services update towpilot-scraper \
  --update-env-vars DATABASE_URL=...,APIFY_TOKEN=...
```

## Scheduled Jobs

The application includes scheduled background jobs:

- **Daily Zone Crawl**: Runs at 2 AM daily to crawl all active zones
- **Weekly Enrichment Refresh**: Runs Sundays at 3 AM to refresh stale enrichments
- **Daily Website Scraping**: Runs at 4 AM daily for new/stale companies
- **Outreach Queue Processing**: Runs every 15 minutes to process pending outreach

To start the scheduler:
```python
from app.jobs.scheduled_jobs import start_scheduler
start_scheduler()
```

## Project Structure

```
eqho-tow-scrape/
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Configuration
│   ├── database.py          # Database setup
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── services/            # Business logic
│   ├── api/                 # API routes
│   ├── dashboard/           # Terminal dashboard
│   ├── jobs/                # Background jobs
│   └── utils/               # Utilities
├── alembic/                 # Database migrations
├── tests/                   # Tests
├── Makefile                 # Common commands
├── Dockerfile               # Docker image
└── requirements.txt         # Dependencies
```

## Development

### Testing (TDD Approach)

This project follows **Test-Driven Development (TDD)** principles. Tests are written before implementing features to ensure clean, accurate code.

#### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run tests in watch mode (requires pytest-watch)
make test-watch
```

#### Test Structure

Tests are organized to mirror the application structure:

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_services/           # Service layer tests
│   ├── test_zone_service.py
│   ├── test_company_service.py
│   ├── test_apify_service.py
│   └── test_website_scraper_service.py
├── test_api/                # API endpoint tests
│   └── test_zones.py
└── test_utils/              # Utility function tests
    └── test_time_periods.py
```

#### Writing Tests

Follow these patterns:

1. **Write tests first** (TDD)
2. **Use descriptive test names**: `test_<functionality>_<scenario>`
3. **Use fixtures** for common setup (database, test data)
4. **Mock external services** (Apify, webhooks)
5. **Test both success and failure cases**
6. **Keep tests isolated** (each test should be independent)

Example test:
```python
@pytest.mark.asyncio
async def test_create_zone_success(db_session):
    """Test successful zone creation"""
    zone_data = ZoneCreate(name="Test Zone", zone_type="city")
    zone = await ZoneService.create_zone(db_session, zone_data)
    assert zone.name == "Test Zone"
    assert zone.id is not None
```

#### Test Coverage Goals

- **Services**: 90%+ coverage (core business logic)
- **API Endpoints**: 80%+ coverage (happy paths + error cases)
- **Models**: 70%+ coverage (relationships, validations)
- **Utils**: 90%+ coverage (pure functions)

### Code Formatting

```bash
make format
```

### Linting

```bash
make lint
```

## License

[Your License Here]

