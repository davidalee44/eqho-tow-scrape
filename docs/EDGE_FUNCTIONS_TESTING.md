# Edge Functions Testing Guide

This guide covers testing the Edge Functions locally and in production.

## Local Testing

### Prerequisites

1. Supabase CLI installed: `npm install -g supabase`
2. Deno installed (for local Edge Function testing)
3. Supabase project linked

### Test Webhook Handler

```bash
# Start local Supabase (if using local development)
supabase start

# Serve Edge Functions locally
supabase functions serve apify-webhook-handler

# Test webhook with mock payload
curl -X POST http://localhost:54321/functions/v1/apify-webhook-handler \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "id": "test-run-id",
      "status": "SUCCEEDED",
      "defaultDatasetId": "test-dataset-id",
      "finishedAt": "2025-11-14T01:00:00Z",
      "stats": {
        "itemsCount": 100
      }
    }
  }'
```

### Test Process Function

```bash
# Serve process function
supabase functions serve process-apify-data

# Test with mock data
curl -X POST http://localhost:54321/functions/v1/process-apify-data \
  -H "Authorization: Bearer YOUR_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "run_id": "test-run-id",
    "dataset_id": "test-dataset-id"
  }'
```

### Test Start Crawl Function

```bash
# Serve start crawl function
supabase functions serve start-apify-crawl

# Test starting a crawl
curl -X POST http://localhost:54321/functions/v1/start-apify-crawl \
  -H "Authorization: Bearer YOUR_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "zone_id": "your-zone-uuid",
    "location": "Baltimore, MD",
    "search_queries": ["towing company"],
    "max_results": 10
  }'
```

## Production Testing

### 1. Test Webhook Endpoint

After deploying, test the webhook endpoint:

```bash
curl -X POST https://[your-project].supabase.co/functions/v1/apify-webhook-handler \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "id": "test-run-id",
      "status": "SUCCEEDED",
      "defaultDatasetId": "test-dataset-id"
    }
  }'
```

Expected response: `{"success": true, "run_id": "test-run-id", ...}`

### 2. Test with Real Apify Run

1. Start a small crawl manually in Apify console
2. Wait for it to complete
3. Check `apify_runs` table:
   ```sql
   SELECT * FROM apify_runs WHERE run_id = 'your-run-id';
   ```
4. Verify processing status updates
5. Check that companies were imported:
   ```sql
   SELECT COUNT(*) FROM companies WHERE source = 'apify_google_maps';
   ```

### 3. Monitor Edge Function Logs

In Supabase Dashboard:
1. Go to **Edge Functions**
2. Select a function
3. Click **Logs** tab
4. Filter by time range or search for errors

Or via CLI:
```bash
supabase functions logs apify-webhook-handler --project-ref YOUR_PROJECT_REF
```

## Common Test Scenarios

### Scenario 1: Successful Webhook Processing

1. Start crawl via Apify console
2. Wait for completion
3. Verify webhook received (check logs)
4. Verify `apify_runs` table updated
5. Verify companies imported

### Scenario 2: Duplicate Webhook

1. Send same webhook twice
2. Verify idempotency (no duplicate processing)
3. Check `processing_status` remains 'completed'

### Scenario 3: Failed Processing

1. Use invalid `dataset_id`
2. Verify error logged in `apify_runs.error_message`
3. Verify `processing_status` set to 'failed'
4. Verify can retry manually

### Scenario 4: Missing Zone ID

1. Create run without `zone_id`
2. Verify error message logged
3. Verify processing fails gracefully

### Scenario 5: Large Dataset

1. Start crawl with 5000+ results
2. Verify batch processing works
3. Verify all companies imported
4. Check processing time

## Debugging Tips

### Check Function Logs

```bash
# All functions
supabase functions logs --project-ref YOUR_PROJECT_REF

# Specific function
supabase functions logs apify-webhook-handler --project-ref YOUR_PROJECT_REF

# With filters
supabase functions logs apify-webhook-handler --project-ref YOUR_PROJECT_REF --since 1h
```

### Check Database State

```sql
-- Check recent runs
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

-- Check processing failures
SELECT * FROM apify_runs 
WHERE processing_status = 'failed'
ORDER BY created_at DESC;

-- Check pending processing
SELECT * FROM apify_runs 
WHERE processing_status = 'pending' 
  AND status = 'SUCCEEDED'
ORDER BY completed_at DESC;
```

### Test Data Mapping

Create a test script to verify mapping logic:

```typescript
import { mapApifyResult } from "./shared/map-apify-result.ts";

const testItem = {
  title: "Test Towing Company",
  url: "https://www.google.com/maps/place/test",
  phone: "555-1234",
  address: "123 Main St, Baltimore, MD 21201",
  rating: 4.5,
  reviewsCount: 100
};

const mapped = mapApifyResult(testItem);
console.log("Mapped result:", mapped);
```

## Performance Testing

### Load Test Webhook Handler

```bash
# Send multiple webhooks concurrently
for i in {1..10}; do
  curl -X POST https://[your-project].supabase.co/functions/v1/apify-webhook-handler \
    -H "Content-Type: application/json" \
    -d "{\"data\": {\"id\": \"test-$i\", \"status\": \"SUCCEEDED\"}}" &
done
wait
```

### Monitor Processing Time

```sql
SELECT 
  run_id,
  items_count,
  completed_at,
  processed_at,
  EXTRACT(EPOCH FROM (processed_at - completed_at)) as processing_seconds
FROM apify_runs
WHERE processing_status = 'completed'
ORDER BY processed_at DESC
LIMIT 10;
```

## Troubleshooting

### Webhook Not Received

1. Check Apify webhook configuration
2. Verify webhook URL is correct
3. Check Edge Function logs for errors
4. Test webhook endpoint manually

### Processing Fails

1. Check `apify_runs.error_message`
2. Verify `APIFY_TOKEN` is set correctly
3. Check Edge Function logs
4. Verify zone_id exists

### Data Not Imported

1. Check `processing_status` in `apify_runs`
2. Verify zone_id is set correctly
3. Check for validation errors in logs
4. Verify companies table structure

### Rate Limits

1. Check Apify API rate limits
2. Reduce batch size if needed
3. Add delays between requests
4. Monitor Apify dashboard for limits

