# Real-Time Console Dashboard Guide

The Textual-based terminal dashboard provides real-time monitoring of Apify crawls, company imports, and system statistics.

## Features

### Real-Time Updates
- **Auto-refresh**: Updates every 5 seconds automatically
- **Manual refresh**: Press `r` to refresh immediately
- **Live status**: See Apify runs and import progress as they happen

### Multiple Views (Tabs)

1. **Overview Tab** - Key metrics and summary
   - Company statistics
   - Zone statistics
   - Quick overview of all systems

2. **Apify Runs Tab** - Monitor crawl operations
   - Recent runs with status indicators
   - Active runs count
   - Pending processing
   - Failed runs
   - Total items processed

3. **Import Progress Tab** - Track company imports
   - Total companies imported
   - Companies by scraping stage
   - Companies by state
   - Impound service statistics
   - Recent imports (24h)

4. **Companies Tab** - Detailed company view
   - Company listings with details
   - Filtering and sorting (future)

5. **Zones Tab** - Zone management view
   - Zone statistics
   - Company counts per zone

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit dashboard |
| `r` | Refresh data |
| `t` | Set period to Today |
| `y` | Set period to Yesterday |
| `w` | Set period to This Week |
| `l` | Set period to Last Week |
| `m` | Set period to This Month |
| `n` | Set period to Last Month |
| `7` | Set period to Last 7 Days |
| `1` | Set period to Last 14 Days |
| `3` | Set period to Last 30 Days |
| `Tab` | Next tab |
| `Shift+Tab` | Previous tab |

## Running the Dashboard

### Using Makefile
```bash
make dashboard
```

### Direct Python
```bash
python -m app.dashboard.dashboard
```

### With Virtual Environment
```bash
source .venv/bin/activate
python -m app.dashboard.dashboard
```

## Dashboard Components

### Stats Cards (Top Bar)
Displays key metrics at a glance:
- **Companies**: Total and new companies
- **Zones**: Active zones and company counts
- **Apify**: Active runs and pending processing
- **Imports**: Total and recent imports

### Apify Runs Monitor
Shows:
- Run ID (truncated for display)
- Location and query
- Status (🟢 RUNNING, ✅ SUCCEEDED, ❌ FAILED)
- Processing status (⏳ pending, 🔄 processing, ✅ completed)
- Items count
- Start time

### Import Progress Widget
Displays:
- Total companies
- Companies with impound service
- Websites scraped count
- Recent imports (24h)
- Breakdown by scraping stage
- Breakdown by state

## Status Indicators

### Apify Run Status
- 🟢 **RUNNING**: Crawl is actively running
- ✅ **SUCCEEDED**: Crawl completed successfully
- ❌ **FAILED**: Crawl failed
- ⏹️ **ABORTED**: Crawl was aborted

### Processing Status
- ⏳ **pending**: Waiting to be processed
- 🔄 **processing**: Currently being processed
- ✅ **completed**: Successfully processed
- ❌ **failed**: Processing failed

## Monitoring Scenarios

### Scenario 1: Monitor Active Crawls
1. Open dashboard: `make dashboard`
2. Navigate to "Apify Runs" tab (click or Tab key)
3. Watch for 🟢 RUNNING status
4. See items count increase as crawl progresses

### Scenario 2: Check Import Progress
1. Navigate to "Import Progress" tab
2. Check "Recent (24h)" count
3. Review "By Stage" breakdown
4. Monitor "By State" distribution

### Scenario 3: Track Failed Operations
1. Check Stats Cards for failed counts
2. Navigate to "Apify Runs" tab
3. Look for ❌ FAILED status
4. Check error messages in run details

### Scenario 4: Monitor Processing Queue
1. Check Stats Cards "Pending" count
2. Navigate to "Apify Runs" tab
3. Look for ⏳ pending processing status
4. Watch as runs move from pending → processing → completed

## Troubleshooting

### Dashboard Won't Start
- Check database connection: `make list-zones`
- Verify virtual environment: `source .venv/bin/activate`
- Check Textual installation: `pip show textual`

### No Data Showing
- Verify database has data: `make query-companies`
- Check time period filter (try "Last 30 Days")
- Refresh manually: Press `r`

### Slow Updates
- Reduce refresh interval in code (default: 5 seconds)
- Check database query performance
- Verify network connection to Supabase

### Widgets Not Updating
- Press `r` to force refresh
- Check for errors in terminal
- Verify database connection is active

## Performance Tips

1. **Large Datasets**: Dashboard shows last 15-20 items by default
2. **Refresh Rate**: 5 seconds is optimal for real-time monitoring
3. **Database Load**: Dashboard queries are optimized but may impact DB during heavy imports
4. **Memory**: Dashboard uses minimal memory, suitable for long-running sessions

## Future Enhancements

- [ ] Pagination for large datasets
- [ ] Filtering and search
- [ ] Export functionality
- [ ] Alert notifications
- [ ] Historical trend charts
- [ ] Custom time range selection
- [ ] Real-time Supabase Realtime integration

## Integration with Edge Functions

The dashboard works seamlessly with Supabase Edge Functions:
- Shows runs started via Edge Functions
- Displays processing status from Edge Functions
- Tracks imports processed by Edge Functions
- Monitors webhook-triggered operations

## Example Workflow

1. **Start crawls** via Edge Functions or scripts
2. **Open dashboard**: `make dashboard`
3. **Monitor progress** in "Apify Runs" tab
4. **Watch imports** in "Import Progress" tab
5. **Review results** in "Companies" tab
6. **Analyze zones** in "Zones" tab

The dashboard provides a comprehensive real-time view of your entire scraping and import pipeline!

