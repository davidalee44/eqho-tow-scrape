# Import Status & Progress

## Current Import Status

The import script (`scripts/import_from_json.py`) is currently running in the background, importing companies from `all_towing_leads.json` into the Supabase database.

### How to Monitor Progress

**Option 1: Check the log file**
```bash
tail -f /tmp/import_log.txt
```

**Option 2: Use the monitor script**
```bash
make monitor-import
# or
python scripts/monitor_import.py
```

**Option 3: Quick database check**
```bash
make analyze-data
```

### Expected Data

- **Total companies in JSON**: ~1,440 companies
  - Maryland (MD): ~822 companies
  - Utah (UT): ~618 companies

### Import Process

1. **Load JSON file** → Parse `all_towing_leads.json`
2. **Group by state** → Create/use zones for each state
3. **Import companies** → Create or update companies in database
4. **Set scraping stage** → Mark as `google_maps` stage

### What Happens During Import

- Companies are checked for duplicates using `google_business_url`
- Existing companies are updated with new data
- New companies are created
- Progress is committed every 100 companies
- Errors are logged but don't stop the import

### After Import Completes

Once the import finishes, you can:

1. **Analyze the data**:
   ```bash
   make analyze-data
   make analyze-data STATE=MD
   make analyze-data HAS_IMPOUND=true
   ```

2. **Query companies**:
   ```bash
   make query-companies STATE=MD
   make query-companies HAS_IMPOUND=true
   ```

3. **Check import stats**:
   ```bash
   make list-zones
   ```

### Troubleshooting

**Import seems stuck:**
- Check if the process is still running: `ps aux | grep import_from_json`
- Check the log file: `tail -f /tmp/import_log.txt`
- Verify database connection: `make list-zones`

**Import failed:**
- Check error messages in `/tmp/import_log.txt`
- Verify database connection and credentials
- Ensure zones exist: `make list-zones`

**Want to restart import:**
- The script handles duplicates, so it's safe to run again
- It will update existing companies and create new ones
- Run: `make import-from-json`

## Next Steps After Import

1. ✅ **Verify data quality** - Run analysis scripts
2. ✅ **Check for impound services** - Filter companies with impound
3. ✅ **Start website scraping** - Begin next stage of enrichment
4. ✅ **Run new crawls** - Target Baltimore MD, Jacksonville NC, Florida

