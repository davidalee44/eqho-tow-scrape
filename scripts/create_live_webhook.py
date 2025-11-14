#!/usr/bin/env python3
"""Create or update LIVE MODE webhook endpoint for Eqho production"""
import os
import sys
import json

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Get API key from environment variable
api_key = os.environ.get('STRIPE_LIVE_API_KEY')
if len(sys.argv) > 1:
    api_key = sys.argv[1]

if not api_key:
    print("Error: STRIPE_LIVE_API_KEY environment variable not set")
    print("\nUsage:")
    print("  export STRIPE_LIVE_API_KEY='rk_live_...'")
    print("  python3 scripts/create_live_webhook.py")
    print("\nOr provide it as an argument:")
    print("  python3 scripts/create_live_webhook.py rk_live_...")
    sys.exit(1)

webhook_url = "https://api.eqho.ai/v1/billing/webhook"
enabled_events = [
    "customer.subscription.created",
    "invoice.created",
    "charge.dispute.created",
    "customer.subscription.deleted",
    "invoice.payment_succeeded",
    "invoice.payment_failed",
    "setup_intent.succeeded"
]

# First, list existing webhook endpoints to see if one exists
print("Checking existing LIVE MODE webhook endpoints...")
url = "https://api.stripe.com/v1/webhook_endpoints"
headers = {
    "Authorization": f"Bearer {api_key}",
}

# List endpoints (live mode by default when using live API key)
response = requests.get(url, headers=headers, params={"limit": 100})

if response.status_code != 200:
    print(f"Error listing webhooks: {response.status_code}")
    print(response.text)
    sys.exit(1)

existing_endpoints = response.json().get('data', [])
existing_endpoint = None

for endpoint in existing_endpoints:
    if endpoint.get('url') == webhook_url:
        existing_endpoint = endpoint
        break

if existing_endpoint:
    print(f"\n✓ Found existing webhook endpoint: {existing_endpoint['id']}")
    print(f"  URL: {existing_endpoint['url']}")
    print(f"  Status: {existing_endpoint['status']}")
    
    # Check if it has the right events
    current_events = set(existing_endpoint.get('enabled_events', []))
    required_events = set(enabled_events)
    
    if required_events.issubset(current_events):
        print(f"  ✓ All required events are enabled")
        if existing_endpoint['status'] == 'enabled':
            print(f"\n✓ Webhook endpoint is already configured correctly!")
            sys.exit(0)
        else:
            print(f"  ⚠️  Webhook is disabled, enabling...")
            # Enable the endpoint
            update_url = f"https://api.stripe.com/v1/webhook_endpoints/{existing_endpoint['id']}"
            update_data = {
                "enabled_events[]": enabled_events
            }
            update_response = requests.post(update_url, headers=headers, data=update_data)
            if update_response.status_code == 200:
                print(f"✓ Webhook endpoint enabled!")
                print(json.dumps(update_response.json(), indent=2))
            else:
                print(f"✗ Error enabling webhook: {update_response.status_code}")
                print(update_response.text)
    else:
        missing = required_events - current_events
        print(f"  ⚠️  Missing events: {missing}")
        print(f"  Updating webhook endpoint...")
        # Update the endpoint
        update_url = f"https://api.stripe.com/v1/webhook_endpoints/{existing_endpoint['id']}"
        update_data = {
            "enabled_events[]": enabled_events
        }
        update_response = requests.post(update_url, headers=headers, data=update_data)
        if update_response.status_code == 200:
            print(f"✓ Webhook endpoint updated!")
            print(json.dumps(update_response.json(), indent=2))
        else:
            print(f"✗ Error updating webhook: {update_response.status_code}")
            print(update_response.text)
else:
    print(f"\n✗ No existing webhook endpoint found for {webhook_url}")
    print(f"Creating new LIVE MODE webhook endpoint...")
    
    # Create new endpoint
    create_data = {
        "url": webhook_url,
    }
    for event in enabled_events:
        create_data[f"enabled_events[]"] = event
    
    create_response = requests.post(url, headers=headers, data=create_data)
    
    if create_response.status_code == 200:
        endpoint = create_response.json()
        print(f"✓ Webhook endpoint created successfully!")
        print(json.dumps(endpoint, indent=2))
        print(f"\nWebhook ID: {endpoint['id']}")
        print(f"URL: {endpoint['url']}")
        print(f"Status: {endpoint['status']}")
    else:
        print(f"✗ Error creating webhook: {create_response.status_code}")
        print(create_response.text)
        sys.exit(1)

print("\n✓ LIVE MODE webhook endpoint is now configured!")
print("  The next subscription creation in LIVE MODE should trigger the webhook.")

