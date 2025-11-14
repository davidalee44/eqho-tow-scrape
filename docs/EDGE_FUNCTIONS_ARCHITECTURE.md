# Edge Functions Architecture

## Overview

Moving data processing to Supabase Edge Functions will eliminate the need to download, process, and upload data through local machines. This architecture will be more efficient, scalable, and reduce latency.

## Current Flow (Inefficient)

```
Apify API → Local Machine → Process → Supabase Database
   ↓            ↓              ↓            ↓
Download    Transform      Validate    Upload
```

**Issues:**
- Data moves through multiple systems
- Requires local machine to be running
- Network latency for large datasets
- Manual orchestration required

## Proposed Flow (Edge Functions)

```
Apify API → Supabase Edge Function → Supabase Database
   ↓              ↓                        ↓
Webhook      Process & Transform      Store Directly
```

**Benefits:**
- No data movement through local machines
- Automatic processing on Apify completion
- Lower latency (edge functions run close to database)
- Scalable (handles multiple concurrent crawls)
- Cost-effective (pay per execution)

## Architecture Design

### 1. Apify Webhook Integration

**Edge Function: `apify-webhook-handler`**

```typescript
// supabase/functions/apify-webhook-handler/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  // Verify webhook signature
  const webhook = await req.json()
  
  // Only process SUCCEEDED runs
  if (webhook.data.status !== 'SUCCEEDED') {
    return new Response(JSON.stringify({ message: 'Run not completed' }), {
      headers: { 'Content-Type': 'application/json' },
    })
  }
  
  const runId = webhook.data.id
  const datasetId = webhook.data.defaultDatasetId
  
  // Trigger data processing function
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  )
  
  // Invoke processing function
  await supabase.functions.invoke('process-apify-data', {
    body: { runId, datasetId }
  })
  
  return new Response(JSON.stringify({ success: true }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

### 2. Data Processing Function

**Edge Function: `process-apify-data`**

```typescript
// supabase/functions/process-apify-data/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const { runId, datasetId } = await req.json()
  
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL') ?? '',
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
  )
  
  // Fetch data from Apify
  const apifyToken = Deno.env.get('APIFY_TOKEN') ?? ''
  const apifyResponse = await fetch(
    `https://api.apify.com/v2/datasets/${datasetId}/items?token=${apifyToken}`
  )
  const items = await apifyResponse.json()
  
  // Process and map data
  const companies = items
    .map(mapApifyResult)
    .filter(company => company !== null)
  
  // Batch insert into database
  const { data, error } = await supabase
    .from('companies')
    .upsert(companies, {
      onConflict: 'google_business_url',
      ignoreDuplicates: false
    })
  
  return new Response(JSON.stringify({ 
    processed: companies.length,
    inserted: data?.length || 0
  }), {
    headers: { 'Content-Type': 'application/json' },
  })
})

function mapApifyResult(item: any) {
  // Same mapping logic as current Python service
  // Returns company object or null
}
```

### 3. Crawl Orchestration Function

**Edge Function: `start-apify-crawl`**

```typescript
// supabase/functions/start-apify-crawl/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { location, searchQueries, maxResults, zoneId } = await req.json()
  
  const apifyToken = Deno.env.get('APIFY_TOKEN') ?? ''
  const actorId = 'compass/crawler-google-places'
  
  const runs = []
  
  for (const query of searchQueries) {
    const input = {
      searchStringsArray: [`${query} ${location}`],
      maxCrawledPlacesPerSearch: maxResults,
      maxReviewsPerPlace: 10,
      includeImages: true,
      includeOpeningHours: true,
    }
    
    // Start crawl
    const response = await fetch(
      `https://api.apify.com/v2/acts/${encodeURIComponent(actorId)}/runs?token=${apifyToken}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input)
      }
    )
    
    const runData = await response.json()
    
    // Store run metadata in database
    await supabase.from('apify_runs').insert({
      run_id: runData.data.id,
      zone_id: zoneId,
      location,
      query,
      status: 'RUNNING',
      webhook_url: `${SUPABASE_URL}/functions/v1/apify-webhook-handler`
    })
    
    // Set up webhook for completion
    await fetch(
      `https://api.apify.com/v2/actor-runs/${runData.data.id}/webhook?token=${apifyToken}`,
      {
        method: 'POST',
        body: JSON.stringify({
          eventTypes: ['ACTOR.RUN.SUCCEEDED'],
          requestUrl: `${SUPABASE_URL}/functions/v1/apify-webhook-handler`
        })
      }
    )
    
    runs.push(runData.data.id)
  }
  
  return new Response(JSON.stringify({ runs }), {
    headers: { 'Content-Type': 'application/json' },
  })
})
```

## Database Schema Additions

```sql
-- Track Apify runs
CREATE TABLE apify_runs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_id TEXT UNIQUE NOT NULL,
  zone_id UUID REFERENCES zones(id),
  location TEXT NOT NULL,
  query TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'RUNNING',
  items_count INTEGER,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  webhook_url TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for quick lookups
CREATE INDEX idx_apify_runs_status ON apify_runs(status);
CREATE INDEX idx_apify_runs_zone ON apify_runs(zone_id);
```

## Implementation Plan

### Phase 1: Basic Webhook Handler
- [ ] Create `apify-webhook-handler` edge function
- [ ] Set up webhook in Apify console
- [ ] Test with single completed run
- [ ] Store run metadata in database

### Phase 2: Data Processing
- [ ] Create `process-apify-data` edge function
- [ ] Implement data mapping logic (TypeScript version)
- [ ] Batch insert into companies table
- [ ] Handle duplicates and updates

### Phase 3: Crawl Orchestration
- [ ] Create `start-apify-crawl` edge function
- [ ] Accept zone_id, location, queries as input
- [ ] Start multiple crawls
- [ ] Set up webhooks automatically

### Phase 4: Error Handling & Monitoring
- [ ] Add retry logic for failed processing
- [ ] Error logging and alerting
- [ ] Status tracking dashboard
- [ ] Rate limit handling

### Phase 5: Advanced Features
- [ ] Parallel processing for large datasets
- [ ] Incremental updates (only new companies)
- [ ] Data validation and quality checks
- [ ] Integration with scraping orchestrator

## Benefits Summary

1. **No Local Processing**: All processing happens in Supabase
2. **Automatic**: Webhooks trigger processing on completion
3. **Scalable**: Edge functions scale automatically
4. **Cost-Effective**: Pay only for execution time
5. **Lower Latency**: Functions run close to database
6. **Simpler Architecture**: Fewer moving parts

## Migration Path

1. **Keep Current System**: Continue using local scripts for now
2. **Build Edge Functions**: Develop functions alongside current system
3. **Test in Parallel**: Run both systems, compare results
4. **Gradual Migration**: Move one location at a time
5. **Deprecate Local Scripts**: Once edge functions are proven

## Environment Variables Needed

```bash
# Supabase Edge Functions
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Apify
APIFY_TOKEN=your-apify-token

# Webhook URL (set in Apify console)
WEBHOOK_URL=https://your-project.supabase.co/functions/v1/apify-webhook-handler
```

## API Endpoints

### Start Crawl
```bash
POST /functions/v1/start-apify-crawl
{
  "zone_id": "uuid",
  "location": "Baltimore, MD",
  "search_queries": ["impound lot", "towing impound"],
  "max_results": 3000
}
```

### Webhook Handler (called by Apify)
```bash
POST /functions/v1/apify-webhook-handler
# Called automatically by Apify when run completes
```

### Process Data (internal)
```bash
POST /functions/v1/process-apify-data
{
  "runId": "apify-run-id",
  "datasetId": "apify-dataset-id"
}
```

## Future Enhancements

1. **Real-time Updates**: Use Supabase Realtime to notify frontend
2. **Queue System**: Use Supabase Queue for large batches
3. **Data Validation**: Add schema validation before insert
4. **Deduplication**: Smart matching across multiple sources
5. **Analytics**: Track processing times and success rates

