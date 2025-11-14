#!/bin/bash
# Deploy Supabase Edge Functions

set -e

echo "=========================================="
echo "Deploying Supabase Edge Functions"
echo "=========================================="

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "ERROR: Supabase CLI not found"
    echo "Install with: npm install -g supabase"
    exit 1
fi

# Check if logged in
if ! supabase projects list &> /dev/null; then
    echo "ERROR: Not logged in to Supabase"
    echo "Login with: supabase login"
    exit 1
fi

# Get project reference from .env or prompt
PROJECT_REF=$(grep SUPABASE_URL .env | cut -d'/' -f3 | cut -d'.' -f1 || echo "")

if [ -z "$PROJECT_REF" ]; then
    echo "ERROR: Could not determine Supabase project reference"
    echo "Please set SUPABASE_URL in .env file"
    exit 1
fi

echo "Project: $PROJECT_REF"
echo ""

# Deploy functions
echo "Deploying apify-webhook-handler..."
supabase functions deploy apify-webhook-handler --project-ref "$PROJECT_REF"

echo ""
echo "Deploying process-apify-data..."
supabase functions deploy process-apify-data --project-ref "$PROJECT_REF"

echo ""
echo "Deploying start-apify-crawl..."
supabase functions deploy start-apify-crawl --project-ref "$PROJECT_REF"

echo ""
echo "=========================================="
echo "Deployment complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Set environment variables in Supabase dashboard:"
echo "   - APIFY_TOKEN"
echo "   - SUPABASE_SERVICE_ROLE_KEY (should be auto-set)"
echo ""
echo "2. Configure Apify webhook:"
echo "   URL: https://$PROJECT_REF.supabase.co/functions/v1/apify-webhook-handler"
echo "   Event: ACTOR.RUN.SUCCEEDED"
echo ""
echo "3. See docs/EDGE_FUNCTIONS_SETUP.md for detailed instructions"

