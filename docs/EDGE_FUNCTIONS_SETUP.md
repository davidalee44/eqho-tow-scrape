# Edge Functions Setup Guide

This guide walks you through setting up automatic Apify crawl processing using Supabase Edge Functions.

## Overview

Edge Functions automatically process Apify crawls when they complete, eliminating the need for local machine processing. The system uses webhooks to trigger processing immediately when crawls finish.

## Architecture

```
Apify Crawl Completes
    ↓
Webhook → apify-webhook-handler (Edge Function)
    ↓
process-apify-data (Edge Function)
    ↓
Download & Process Data
    ↓
Import to Supabase Database
```

## Prerequisites

1. Supabase project with database access
2. Supabase CLI installed: `npm install -g supabase`
3. Apify account with API token
4. Database migrations applied (includes `apify_runs` table)

## Step 1: Apply Database Migration

First, ensure the `apify_runs` table exists:

```bash
make migrate
```

This creates the table needed to track crawl processing status.

## Step 2: Deploy Edge Functions

Deploy all Edge Functions to Supabase:

```bash
make deploy-edge-functions
```

Or manually:

```bash
supabase functions deploy apify-webhook-handler --project-ref YOUR_PROJECT_REF
supabase functions deploy process-apify-data --project-ref YOUR_PROJECT_REF
supabase functions deploy start-apify-crawl --project-ref YOUR_PROJECT_REF
```

## Step 3: Set Environment Variables

In the Supabase Dashboard:

1. Go to **Project Settings** → **Edge Functions**
2. Set the following secrets:

   - `APIFY_TOKEN` - Your Apify API token
   - `SUPABASE_SERVICE_ROLE_KEY` - Should be auto-set, but verify it exists

To set secrets via CLI:

```bash
supabase secrets set APIFY_TOKEN=your_token_here --project-ref YOUR_PROJECT_REF
```

## Step 4: Configure Apify Webhook

### Get Your Webhook URL

Your webhook URL format:
```
https://[your-project-ref].supabase.co/functions/v1/apify-webhook-handler
```

Replace `[your-project-ref]` with your Supabase project reference (found in your `.env` file as part of `SUPABASE_URL`).

### Set Up Webhook in Apify

1. Go to [Apify Console](https://console.apify.com)
2. Navigate to **Settings** → **Webhooks**
3. Click **Add Webhook**
4. Configure:
   - **Event**: `ACTOR.RUN.SUCCEEDED`
   - **URL**: Your webhook URL from above
   - **Method**: `POST`
   - **Payload Template** (optional, but recommended):
     ```json
     {
       "data": {
         "id": "{{runId}}",
         "status": "{{status}}",
         "defaultDatasetId": "{{defaultDatasetId}}",
         "finishedAt": "{{finishedAt}}",
         "stats": {
           "itemsCount": "{{stats.itemsCount}}"
         }
       }
     }
     ```
5. Click **Save**

## Step 5: Test the System

### Test 1: Manual Crawl Start

Start a small crawl manually and verify webhook is received:

```bash
# Start a crawl (this will also set up webhook automatically if using start-apify-crawl)
curl -X POST https://[your-project].supabase.co/functions/v1/start-apify-crawl \
  -H "Authorization: Bearer YOUR_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "your-zone-uuid",
    "location": "Baltimore, MD",
    "search_queries": ["towing company"],
    "max_results": 10
  }'
```

### Test 2: Check Processing Status

Query the `apify_runs` table to see processing status:

```sql
SELECT 
  run_id,
  status,
  processing_status,
  items_count,
  error_message,
  completed_at,
  processed_at
FROM apify_runs
ORDER BY created_at DESC
LIMIT 10;
```

### Test 3: Verify Data Import

Check that companies were imported:

```bash
make analyze-data STATE=MD
```

## Usage

### Starting Crawls Manually

You can still start crawls manually using the existing scripts:

```bash
make run-impound-crawls
```

The webhook will automatically process them when they complete.

### Starting Crawls via Edge Function

Use the `start-apify-crawl` Edge Function:

```bash
curl -X POST https://[your-project].supabase.co/functions/v1/start-apify-crawl \
  -H "Authorization: Bearer YOUR_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "zone-uuid",
    "location": "Baltimore, MD",
    "search_queries": ["impound lot", "towing impound"],
    "max_results": 3000,
    "actor_id": "compass/crawler-google-places"
  }'
```

This will:
1. Start the crawls in Apify
2. Set up webhooks automatically
3. Store run metadata in database
4. Process automatically when crawls complete

### Monitoring

#### Check Processing Status

```sql
-- All runs
SELECT * FROM apify_runs ORDER BY created_at DESC;

-- Failed runs
SELECT * FROM apify_runs WHERE processing_status = 'failed';

-- Pending processing
SELECT * FROM apify_runs WHERE processing_status = 'pending' AND status = 'SUCCEEDED';
```

#### View Edge Function Logs

In Supabase Dashboard:
1. Go to **Edge Functions**
2. Select a function
3. Click **Logs** tab

Or via CLI:

```bash
supabase functions logs apify-webhook-handler --project-ref YOUR_PROJECT_REF
supabase functions logs process-apify-data --project-ref YOUR_PROJECT_REF
```

## Troubleshooting

### Webhook Not Received

1. Check Apify webhook configuration
2. Verify webhook URL is correct
3. Check Edge Function logs for errors
4. Test webhook manually:
   ```bash
   curl -X POST https://[your-project].supabase.co/functions/v1/apify-webhook-handler \
     -H "Content-Type: application/json" \
     -d '{"data": {"id": "test-run-id", "status": "SUCCEEDED"}}'
   ```

### Processing Fails

1. Check `apify_runs` table for error messages
2. Verify `APIFY_TOKEN` is set correctly
3. Check Edge Function logs
4. Verify zone_id exists for the run

### Data Not Imported

1. Check `processing_status` in `apify_runs` table
2. Verify zone_id is set correctly
3. Check for validation errors in logs
4. Verify companies table structure matches expected schema

### Rate Limits

If you hit Apify rate limits:
1. Reduce `max_results` per crawl
2. Space out crawl starts
3. Use different Apify actors if available

## Manual Retry

If a run fails processing, you can manually retry:

```bash
curl -X POST https://[your-project].supabase.co/functions/v1/process-apify-data \
  -H "Authorization: Bearer YOUR_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "failed-run-id",
    "dataset_id": "dataset-id"
  }'
```

## Security Considerations

1. **Webhook Verification**: Consider adding webhook signature verification
2. **Rate Limiting**: Edge Functions have built-in rate limiting
3. **Error Handling**: Failed runs are logged but don't expose sensitive data
4. **API Keys**: Store `APIFY_TOKEN` as Supabase secret, never commit to repo

## Next Steps

- Set up monitoring/alerting for failed runs
- Add retry logic with exponential backoff
- Create dashboard for run status
- Add support for multiple zones automatically

## Support

For issues:
1. Check Edge Function logs
2. Review `apify_runs` table
3. Check Apify console for crawl status
4. Review this documentation

