# Scraping & Crawling Flow Documentation

## Overview

The TowPilot scraping system uses a multi-stage pipeline to collect comprehensive data about towing companies from multiple sources. This document outlines the complete flow, methods, and best practices.

## Architecture

```
┌─────────────────┐
│  Zone Crawl     │  → Google Maps (Apify)
│  (Discovery)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Company Store  │  → Create/Update in Database
│  (Deduplication)│
└────────┬────────┘
         │
         ├─────────────────┬─────────────────┐
         ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Website     │  │  Facebook    │  │  Google      │
│  Scraping    │  │  Profile     │  │  Business   │
│  (Playwright)│  │  (Future)    │  │  (Future)    │
└────────┬─────┘  └────────┬─────┘  └────────┬─────┘
         │                 │                 │
         └─────────────────┴─────────────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Data Enrichment│
                  │  & Validation   │
                  └─────────────────┘
```

## Scraping Stages

Companies progress through these stages:

1. **INITIAL** - Just discovered, no scraping done
2. **GOOGLE_MAPS** - Google Maps data collected via Apify
3. **WEBSITE_SCRAPED** - Website scraped for hours, services, impound info
4. **FACEBOOK_SCRAPED** - Facebook profile scraped (future)
5. **FULLY_ENRICHED** - All available sources scraped
6. **FAILED** - Scraping failed (retryable)

## Flow Methods

### 1. Zone Crawl (`crawl_and_enrich_zone`)

**Purpose**: Discover companies in a geographic zone and enrich them

**Steps**:
1. Query Google Maps via Apify for towing companies in zone
2. Deduplicate by `google_business_url`
3. Create or update company records
4. Queue companies with websites for scraping
5. Scrape websites in parallel (with concurrency limit)
6. Optionally scrape social profiles
7. Update scraping stage and status

**API Endpoint**: `POST /api/v1/crawl/zone/{zone_id}`

**Parameters**:
- `zone_id`: UUID of zone to crawl
- `search_query`: Search term (default: "towing company")
- `scrape_websites`: Boolean (default: true)
- `scrape_profiles`: Boolean (default: false)
- `max_results`: Maximum companies to discover (default: 100)

**Returns**:
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

### 2. Website Scraping (`scrape_company_website`)

**Purpose**: Extract data from company website

**Data Extracted**:
- Hours of operation (structured format)
- Impound service detection (with confidence score)
- Service offerings
- Contact information updates

**Method**: Playwright-based browser automation

**Concurrency**: Controlled by `WEBSITE_SCRAPE_CONCURRENT` (default: 5)

**Status Tracking**:
- `website_scrape_status`: 'pending', 'success', 'failed', 'no_website'
- `website_scraped_at`: Timestamp of last scrape
- `scraping_stage`: Current stage in pipeline

**API Endpoint**: `POST /api/v1/enrichment/scrape-website/{company_id}`

### 3. Batch Website Scraping (`scrape_websites_for_zone`)

**Purpose**: Scrape all company websites in a zone

**Features**:
- Concurrent processing with semaphore control
- Error handling per company (doesn't stop batch)
- Status updates for each company
- Progress tracking

**API Endpoint**: `POST /api/v1/enrichment/scrape-websites/zone/{zone_id}`

### 4. Refresh Stale Companies (`refresh_stale_companies`)

**Purpose**: Re-scrape companies that haven't been updated recently

**Criteria**:
- No website scrape in last N days (default: 30)
- Has website URL
- Not marked as 'no_website'

**Use Case**: Scheduled job to keep data fresh

**API Endpoint**: `POST /api/v1/enrichment/bulk` (with zone_id)

### 5. Status Tracking (`get_scraping_status`)

**Purpose**: Get overview of scraping progress for a zone

**Returns**:
- Total companies
- Breakdown by scraping stage
- Website scraping statistics
- Success/failure rates

**API Endpoint**: `GET /api/v1/crawl/status/{zone_id}` (to be implemented)

## Data Sources

### Google Maps (Apify)
- **Source**: Apify Google Maps Scraper actor
- **Data Collected**:
  - Business name, address, phone
  - Website URL, Google Business URL
  - Ratings, review count
  - Hours (if available)
  - Services listed
  - Photos

### Company Websites (Playwright)
- **Source**: Direct website scraping
- **Data Collected**:
  - Hours of operation (structured)
  - Impound service indicators
  - Service descriptions
  - Contact information
  - Fleet information

### Facebook Profiles (Future)
- **Source**: Facebook Business Pages
- **Data Collected**:
  - Hours of operation
  - Services offered
  - Reviews and ratings
  - Contact information

### Google Business Profiles (Future)
- **Source**: Google Business API
- **Data Collected**:
  - Verified hours
  - Services
  - Reviews
  - Q&A responses

## Concurrency Control

### Website Scraping
- **Semaphore-based**: Limits concurrent browser instances
- **Configurable**: `WEBSITE_SCRAPE_CONCURRENT` env var
- **Default**: 5 concurrent scrapes
- **Rationale**: Balance speed vs. resource usage

### Apify Crawls
- **Sequential**: One zone at a time (Apify handles internal concurrency)
- **Rate Limiting**: Apify API handles rate limits
- **Timeout**: 300 seconds per crawl

## Error Handling

### Retry Logic
- **Website Scrapes**: Mark as 'failed', can retry via refresh endpoint
- **Apify Crawls**: Fail fast, return partial results if any
- **Network Errors**: Retry with exponential backoff (future enhancement)

### Status Tracking
- **Failed Scrapes**: Marked with `website_scrape_status = 'failed'`
- **No Website**: Marked with `website_scrape_status = 'no_website'`
- **Success**: `website_scrape_status = 'success'` + timestamp

## Best Practices

### 1. Zone Crawling
- Start with smaller zones (city-level) before metro areas
- Use specific search queries ("towing company", "24 hour towing")
- Set reasonable `max_results` to avoid API limits

### 2. Website Scraping
- Scrape immediately after discovery for fresh data
- Use batch scraping for efficiency
- Refresh stale data regularly (30-day window)

### 3. Data Quality
- Validate extracted hours format
- Cross-reference impound detection with multiple signals
- Store confidence scores for uncertain data

### 4. Performance
- Use concurrent scraping for websites
- Process zones sequentially to avoid overwhelming Apify
- Cache browser instances when possible

## Scheduled Jobs

### Daily Zone Crawl
- **Time**: 2 AM
- **Action**: Crawl all active zones
- **Purpose**: Discover new companies

### Daily Website Scraping
- **Time**: 4 AM
- **Action**: Scrape stale websites (last 30 days)
- **Purpose**: Keep website data fresh

### Weekly Enrichment Refresh
- **Time**: Sunday 3 AM
- **Action**: Full enrichment refresh for stale companies
- **Purpose**: Comprehensive data update

## API Usage Examples

### Complete Zone Crawl
```bash
curl -X POST http://localhost:8000/api/v1/crawl/zone/{zone_id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "towing company",
    "scrape_websites": true,
    "max_results": 100
  }'
```

### Scrape Single Company Website
```bash
curl -X POST http://localhost:8000/api/v1/enrichment/scrape-website/{company_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Batch Scrape Zone Websites
```bash
curl -X POST http://localhost:8000/api/v1/enrichment/scrape-websites/zone/{zone_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Refresh Stale Companies
```bash
curl -X POST http://localhost:8000/api/v1/enrichment/bulk \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "{zone_id}",
    "days_stale": 30
  }'
```

## Monitoring & Metrics

### Key Metrics
- Companies discovered per zone
- Website scrape success rate
- Average scrape time per website
- Data freshness (days since last scrape)
- Stage distribution (how many companies in each stage)

### Status Dashboard
- Total companies by stage
- Scraping success rates
- Recent crawl activity
- Failed scrape retry queue

## Future Enhancements

1. **Facebook Scraping**: Implement Facebook Business Page scraping
2. **Google Business API**: Direct integration for verified data
3. **Retry Queue**: Automatic retry for failed scrapes
4. **Rate Limiting**: Smart rate limiting based on source
5. **Data Validation**: Cross-source validation for accuracy
6. **Change Detection**: Detect and alert on data changes
7. **Webhook Notifications**: Notify on scraping completion

