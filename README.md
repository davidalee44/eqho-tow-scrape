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
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service role key (required for auth)
- `DATABASE_URL`: PostgreSQL connection string (from Supabase)
- `APIFY_TOKEN`: Your Apify API token
- `EQHO_API_TOKEN`: Your Eqho.ai API token (for AI voice outreach)

Authentication (Required):
- `SUPABASE_AUTH_ENABLED`: Enable Supabase Auth (default: true)
- `SUPABASE_JWT_SECRET`: JWT secret from Supabase dashboard
- `SUPABASE_AUTH_URL`: Auth URL (default: {SUPABASE_URL}/auth/v1)

Optional:
- `USE_SUPABASE_ENV_VARS`: Fetch env vars from Supabase (default: false)
- `ENV_CACHE_TTL`: Cache TTL for env vars in seconds (default: 300)
- `EQHO_API_URL`: Eqho API URL (default: https://api.eqho.ai/v1)
- `EQHO_DEFAULT_CAMPAIGN_ID`: Default campaign ID for TowPilot outreach
- `EMAIL_PROVIDER_API_KEY`: For email sending (legacy)
- `SMS_PROVIDER_API_KEY`: For SMS sending (legacy)
- `PHONE_PROVIDER_API_KEY`: For phone calls (legacy - prefer Eqho.ai)
- `OUTREACH_WEBHOOK_URL`: Webhook URL for outreach system
- `PLAYWRIGHT_HEADLESS`: Run Playwright in headless mode (default: true)
- `PLAYWRIGHT_TIMEOUT`: Page load timeout in ms (default: 30000)
- `WEBSITE_SCRAPE_CONCURRENT`: Max concurrent scrapes (default: 5)
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (development/production)

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

### Supabase Auth Setup

This application uses Supabase Auth for authentication, OAuth 2.0, and OpenID Connect integration.

#### 1. Configure Supabase Auth

1. Go to your Supabase project dashboard: https://supabase.com/dashboard
2. Navigate to **Authentication** > **Settings**
3. Enable email/password authentication
4. Configure JWT settings:
   - Set JWT expiry (default: 3600 seconds)
   - Enable refresh token rotation
5. Get your JWT secret from **Settings** > **API** > **JWT Secret**
6. Add to `.env`:
   ```
   SUPABASE_JWT_SECRET=your-jwt-secret
   SUPABASE_AUTH_URL=https://your-project.supabase.co/auth/v1
   ```

#### 2. Configure OAuth Providers (Optional)

To enable OAuth login (Google, GitHub, etc.):

1. Go to **Authentication** > **Providers** in Supabase dashboard
2. Enable desired providers (Google, GitHub, GitLab, etc.)
3. Configure OAuth credentials for each provider
4. Set redirect URLs in provider settings

#### 3. Configure OpenID Connect

For third-party integrations (like Pipe dream):

1. Supabase Auth automatically provides OIDC endpoints
2. Use the discovery endpoint: `GET /.well-known/openid-configuration`
3. Configure OIDC clients in your third-party service using:
   - Issuer: `https://your-project.supabase.co/auth/v1`
   - Authorization endpoint: `https://your-project.supabase.co/auth/v1/authorize`
   - Token endpoint: `https://your-project.supabase.co/auth/v1/token`
   - UserInfo endpoint: `https://your-project.supabase.co/auth/v1/userinfo`

#### 4. Run Database Migrations

After configuring Supabase Auth, run migrations to create user tables:

```bash
make migrate
# Or manually:
alembic upgrade head
```

This creates:
- `users` table for user profiles
- `environment_config` table for managing environment variables

#### 5. Create First Admin User

After running migrations, create your first admin user:

1. Sign up via API: `POST /api/v1/auth/signup`
2. Update user role to admin in Supabase dashboard or via API:
   ```bash
   PUT /api/v1/users/{user_id}
   {
     "role": "admin"
   }
```

### Apify Setup

1. Sign up at https://apify.com
2. Get your API token from the Apify dashboard: https://console.apify.com/account/integrations
3. Add `APIFY_TOKEN` to your `.env` file

#### Download Previous Runs

Download data from previous Apify runs:

```bash
# Activate virtual environment first
source venv/bin/activate

# List all previous towing runs
make apify-list

# Download all previous runs (default: 10 runs)
make apify-download

# Download with custom limit
make apify-download LIMIT_RUNS=20

# Download specific run
make apify-download-run RUN_ID=your_run_id
```

Or use the script directly:
```bash
python scripts/download_apify_runs.py --list-only
python scripts/download_apify_runs.py --limit-runs 10
python scripts/download_apify_runs.py --run-id YOUR_RUN_ID
```

See `docs/APIFY_DOWNLOAD.md` for detailed documentation.

### Eqho.ai Setup (Recommended for Voice AI Outreach)

Eqho.ai is the primary platform for AI-powered voice outreach. It provides:
- **Voice AI Agents**: Conversational AI agents for outbound calls
- **Campaign Management**: Organize and manage outreach campaigns
- **Lead Management**: Upload and manage leads with custom fields
- **Call Analytics**: Track call outcomes, dispositions, and quality
- **Knowledge Bases**: Store TowPilot information for agents to reference

**Setup Steps:**

1. Get your Eqho.ai API token from your Eqho dashboard
2. Create or identify your TowPilot campaign ID
3. Add to `.env`:
   ```
   EQHO_API_TOKEN=your-eqho-api-token
   EQHO_DEFAULT_CAMPAIGN_ID=your-campaign-id
   ```

**Using Eqho.ai Integration:**

- Phone outreach automatically uses Eqho.ai when `EQHO_API_TOKEN` is configured
- Upload leads to campaigns via `/api/v1/eqho/upload-leads`
- Trigger immediate calls via `/api/v1/eqho/trigger-call`
- View campaign calls via `/api/v1/eqho/campaign/{campaign_id}/calls`

**Note:** The current implementation uses the Eqho MCP tools pattern. For production, you'll need to implement the actual HTTP API integration based on Eqho's API documentation.

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
make help              # Show all available commands
make venv              # Create virtual environment
make install           # Install dependencies (requires venv)
make init              # Complete initial setup (venv + install + db)
make run               # Run the FastAPI server
make migrate           # Run database migrations
make test              # Run tests
make lint              # Run linter
make format            # Format code
make dashboard         # Run terminal dashboard

# Apify commands
make apify-list        # List previous Apify towing runs
make apify-download    # Download all previous runs (default: 10)
make apify-download LIMIT_RUNS=20  # Download with custom limit
make apify-download-run RUN_ID=abc123  # Download specific run

# Docker & Deployment
make docker-build      # Build Docker image
make docker-run        # Run Docker container
make cloud-build PROJECT_ID=your_id  # Build for Cloud Run
make cloud-deploy PROJECT_ID=your_id # Deploy to Cloud Run
```

**Note**: Most commands require the virtual environment to be activated. The Makefile will check and warn you if it's not activated.

## API Endpoints

### Authentication (Public)
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login (email/password)
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Get current user profile
- `POST /api/v1/auth/oauth/{provider}` - OAuth provider login
- `GET /api/v1/auth/oauth/{provider}/callback` - OAuth callback handler

### OpenID Connect (Public)
- `GET /.well-known/openid-configuration` - OIDC discovery endpoint
- `GET /api/v1/oidc/userinfo` - User info endpoint (requires auth)
- `POST /api/v1/oidc/token` - Token endpoint info
- `GET /api/v1/oidc/authorize` - Authorization endpoint info

### Users (Protected)
- `GET /api/v1/users` - List users (admin only)
- `GET /api/v1/users/{user_id}` - Get user details (admin only)
- `PUT /api/v1/users/{user_id}` - Update user (admin only)
- `DELETE /api/v1/users/{user_id}` - Deactivate user (admin only)
- `GET /api/v1/users/me/profile` - Get current user's profile
- `PUT /api/v1/users/me/profile` - Update current user's profile

### Configuration (Admin Only)
- `GET /api/v1/config/env` - List environment variables
- `POST /api/v1/config/env` - Set environment variable
- `DELETE /api/v1/config/env/{key}` - Delete environment variable

### Zones (Protected)
- `POST /api/v1/zones` - Create zone
- `GET /api/v1/zones` - List zones
- `GET /api/v1/zones/{zone_id}` - Get zone details
- `PUT /api/v1/zones/{zone_id}` - Update zone
- `DELETE /api/v1/zones/{zone_id}` - Deactivate zone

### Companies (Protected)
- `GET /api/v1/companies` - List/search companies (filters: zone_id, services, fleet_size, has_impound_service)
- `GET /api/v1/companies/{company_id}` - Get company details
- `PUT /api/v1/companies/{company_id}` - Update company
- `POST /api/v1/companies/bulk-import` - Bulk import companies

### Crawling (Protected)
- `POST /api/v1/crawl/zone/{zone_id}` - Comprehensive zone crawl with website scraping
  - Query params: `search_query`, `scrape_websites`, `scrape_profiles`, `max_results`
- `POST /api/v1/crawl/company/{company_id}` - Re-crawl a specific company website
- `GET /api/v1/crawl/status/{zone_id}` - Get scraping status breakdown for a zone
- `POST /api/v1/crawl/refresh-stale` - Refresh stale companies (query params: `zone_id`, `days_stale`, `limit`)

### Apify (Protected)
- `GET /api/v1/apify/runs` - List all Apify actor runs
- `GET /api/v1/apify/runs/towing` - List towing-related runs only
- `GET /api/v1/apify/runs/{run_id}` - Get run details
- `GET /api/v1/apify/runs/{run_id}/data` - Download data from a run
- `POST /api/v1/apify/runs/download-all` - Download data from all towing runs

### Enrichment (Protected)
- `POST /api/v1/enrichment/company/{company_id}` - Enrich a company
- `POST /api/v1/enrichment/bulk` - Bulk enrichment for a zone
- `GET /api/v1/enrichment/snapshots/{company_id}` - Get enrichment history
- `POST /api/v1/enrichment/scrape-website/{company_id}` - Scrape company website
- `POST /api/v1/enrichment/scrape-websites/zone/{zone_id}` - Batch website scraping

### Outreach (Protected)
- `POST /api/v1/outreach/sequences` - Create outreach sequence
- `GET /api/v1/outreach/sequences` - List sequences
- `POST /api/v1/outreach/assign` - Assign company to sequence
- `POST /api/v1/outreach/send` - Send immediate outreach (uses Eqho.ai for phone)
- `GET /api/v1/outreach/history/{company_id}` - Get outreach history
- `PUT /api/v1/outreach/assignments/{assignment_id}/pause` - Pause assignment
- `PUT /api/v1/outreach/assignments/{assignment_id}/resume` - Resume assignment

### Eqho.ai Integration (Protected)
- `POST /api/v1/eqho/upload-leads` - Upload companies as leads to Eqho campaign
- `POST /api/v1/eqho/trigger-call` - Trigger immediate call via Eqho
- `GET /api/v1/eqho/campaign/{campaign_id}/calls` - Get campaign call history

## Authentication & Authorization

### Using the API

All protected endpoints require authentication via JWT Bearer token:

```bash
# Login to get access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in subsequent requests
curl http://localhost:8000/api/v1/zones \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### User Roles

- **admin**: Full access to all endpoints, including user management and configuration
- **user**: Standard access to zones, companies, crawl, enrichment, outreach endpoints
- **readonly**: Read-only access (future implementation)

### OAuth Integration

To login with OAuth provider:

```bash
# Get OAuth URL
curl -X POST http://localhost:8000/api/v1/auth/oauth/google

# Redirect user to returned URL
# After callback, exchange code for tokens via Supabase Auth
```

### OpenID Connect Integration

For third-party integrations (e.g., Pipe dream):

1. **Discovery**: Get OIDC configuration
   ```bash
   curl http://localhost:8000/.well-known/openid-configuration
   ```

2. **Authorization**: Redirect user to authorization endpoint
   ```
   GET https://your-project.supabase.co/auth/v1/authorize?client_id=...&redirect_uri=...&response_type=code&scope=openid profile email
   ```

3. **Token Exchange**: Exchange authorization code for tokens
   ```
   POST https://your-project.supabase.co/auth/v1/token
   ```

4. **User Info**: Get user information
   ```bash
   curl http://localhost:8000/api/v1/oidc/userinfo \
     -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
   ```

### Environment Variable Management

Admin users can manage environment variables via API:

```bash
# List environment variables
curl http://localhost:8000/api/v1/config/env \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Set environment variable
curl -X POST http://localhost:8000/api/v1/config/env \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "API_KEY",
    "value": "secret-value",
    "is_encrypted": true,
    "environment": "production"
  }'
```

To enable fetching env vars from Supabase on startup, set `USE_SUPABASE_ENV_VARS=true` in `.env`.

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

## Scraping & Crawling Flow

The system uses a comprehensive multi-stage scraping pipeline:

### Pipeline Stages

1. **INITIAL** - Company just discovered
2. **GOOGLE_MAPS** - Google Maps data collected via Apify
3. **WEBSITE_SCRAPED** - Website scraped for hours, services, impound info
4. **FACEBOOK_SCRAPED** - Facebook profile scraped (future)
5. **FULLY_ENRICHED** - All available sources scraped
6. **FAILED** - Scraping failed (retryable)

### Complete Zone Crawl Flow

```bash
# Comprehensive crawl with website scraping
curl -X POST "http://localhost:8000/api/v1/crawl/zone/{zone_id}?scrape_websites=true&max_results=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Flow**:
1. Discover companies via Google Maps (Apify)
2. Deduplicate by `google_business_url`
3. Create/update company records
4. Scrape websites in parallel (concurrency controlled)
5. Extract hours, services, impound detection
6. Update scraping stage and status

**Response**:
```json
{
  "companies_found": 45,
  "companies_new": 30,
  "companies_updated": 15,
  "websites_scraped": 28,
  "websites_failed": 2,
  "profiles_scraped": 0,
  "stage_breakdown": {
    "initial": 30,
    "google_maps": 45,
    "website_scraped": 28,
    "fully_enriched": 0
  }
}
```

### Website Scraping

- **Concurrency**: Controlled by `WEBSITE_SCRAPE_CONCURRENT` (default: 5)
- **Data Extracted**: Hours of operation, impound service, services offered
- **Status Tracking**: `website_scrape_status` ('pending', 'success', 'failed', 'no_website')
- **Retry**: Use refresh endpoint for failed scrapes

See `docs/SCRAPING_FLOW.md` for detailed documentation.

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

