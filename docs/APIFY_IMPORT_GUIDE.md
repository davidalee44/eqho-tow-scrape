# Apify Data Import Guide

This guide explains how to download Apify datasets and import them into Supabase.

## Prerequisites

1. **Apify Token**: Set `APIFY_TOKEN` in your `.env` file
   - Get your token from: https://console.apify.com/account/integrations

2. **Database Connection**: Set `DATABASE_URL` in your `.env` file
   - Format: `postgresql+asyncpg://user:password@host:port/database`

3. **Zone Created**: You need at least one zone in the database
   - Use `make list-zones` to see existing zones
   - Create zones via API: `POST /api/v1/zones`

## Quick Start

### Step 1: List Available Apify Runs

```bash
make apify-list
```

This shows all previous towing company runs from Apify.

### Step 2: List Zones

```bash
make list-zones
```

Copy the UUID of the zone you want to import data into.

### Step 3: Import Data to Supabase

```bash
make apify-import-to-supabase ZONE_ID=<your-zone-uuid>
```

Options:
- `LIMIT_RUNS=N` - Limit number of runs to process (default: 10)
- `LIMIT_ITEMS=N` - Limit items per run (default: all)

Example:
```bash
make apify-import-to-supabase ZONE_ID=123e4567-e89b-12d3-a456-426614174000 LIMIT_RUNS=5
```

### Step 4: Query and Analyze Data

```bash
# Query all companies
make query-companies

# Query by zone
make query-companies ZONE_ID=<uuid>

# Query by state
make query-companies STATE=UT

# Query companies with impound service
make query-companies HAS_IMPOUND=true

# Combine filters
make query-companies ZONE_ID=<uuid> STATE=UT HAS_IMPOUND=true LIMIT=50
```

## What Gets Imported

The import script:
1. Downloads company data from Apify runs
2. Maps Apify data to our company schema
3. Creates new companies or updates existing ones (based on Google Business URL)
4. Sets scraping stage to `google_maps`
5. Links companies to the specified zone

## Data Mapping

Apify fields → Company fields:
- `title` → `name`
- `phone` → `phone_primary`
- `address` → `address_street`, `address_city`, `address_state`, `address_zip`
- `website` → `website`
- `url` → `google_business_url`
- `rating` → `rating`
- `reviewsCount` → `review_count`
- `openingHours` → `hours`

## Troubleshooting

### No zones found
Create a zone first:
```bash
# Via API (with authentication)
curl -X POST http://localhost:8000/api/v1/zones \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Utah", "state": "UT", "zone_type": "state"}'
```

### No Apify runs found
- Check that `APIFY_TOKEN` is set correctly
- Verify you have completed runs in your Apify account
- Runs must contain "towing" in the search query or use Google Maps scraper

### Import errors
- Check database connection (`DATABASE_URL`)
- Verify zone UUID is correct
- Check logs for specific error messages

## Example Workflow

```bash
# 1. List available Apify runs
make apify-list

# 2. List zones (or create one if needed)
make list-zones

# 3. Import data (replace with actual zone UUID)
make apify-import-to-supabase ZONE_ID=your-zone-uuid LIMIT_RUNS=3

# 4. Query imported data
make query-companies ZONE_ID=your-zone-uuid

# 5. Analyze by state
make query-companies STATE=UT

# 6. Find companies with impound service
make query-companies HAS_IMPOUND=true
```

## Next Steps

After importing:
1. **Website Scraping**: Use the scraping orchestrator to scrape company websites
2. **Enrichment**: Enrich company profiles with Facebook/Google Business data
3. **Outreach**: Set up outreach sequences for imported companies

