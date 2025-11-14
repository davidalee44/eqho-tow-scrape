#!/usr/bin/env python3
"""Check webhook delivery status for a Stripe subscription"""
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
    print("  python3 scripts/check_webhook_delivery.py [subscription_id]")
    sys.exit(1)

subscription_id = sys.argv[2] if len(sys.argv) > 2 else "sub_1STDAUCyexzwFObxg19JwADY"

print(f"Checking webhook delivery for subscription: {subscription_id}\n")

# Get events for this subscription
url = "https://api.stripe.com/v1/events"
headers = {
    "Authorization": f"Bearer {api_key}",
}

params = {
    "type": "customer.subscription.created",
    "limit": 100
}

response = requests.get(url, headers=headers, params=params)

if response.status_code != 200:
    print(f"Error fetching events: {response.status_code}")
    print(response.text)
    sys.exit(1)

events = response.json().get('data', [])
found_event = None

for event in events:
    sub = event.get('data', {}).get('object', {})
    if sub.get('id') == subscription_id:
        found_event = event
        break

if not found_event:
    print(f"✗ No webhook event found for subscription {subscription_id}")
    print("This means the webhook was never sent.")
    print("\nPossible reasons:")
    print("1. No LIVE MODE webhook endpoint configured")
    print("2. Webhook endpoint doesn't have 'customer.subscription.created' enabled")
    print("3. Webhook endpoint is disabled")
    sys.exit(1)

print(f"✓ Found webhook event: {found_event['id']}")
print(f"  Created: {found_event['created']}")
print(f"  Type: {found_event['type']}")

# Check webhook delivery attempts
request_id = found_event.get('request')
if request_id:
    print(f"\nWebhook Request ID: {request_id}")
    
    # Get webhook delivery details
    delivery_url = f"https://api.stripe.com/v1/events/{found_event['id']}"
    delivery_response = requests.get(delivery_url, headers=headers)
    
    if delivery_response.status_code == 200:
        event_details = delivery_response.json()
        # Check if there are delivery attempts
        print(f"\nWebhook Delivery Status:")
        # Note: Full delivery logs might need to be checked in Dashboard
        print(f"  Event ID: {event_details['id']}")
        print(f"  Livemode: {event_details['livemode']}")
        
        # The request object contains webhook delivery info
        if isinstance(request_id, str):
            print(f"\nTo see full webhook delivery details:")
            print(f"  Visit: https://dashboard.stripe.com/events/{found_event['id']}")
    else:
        print(f"Could not fetch event details: {delivery_response.status_code}")
else:
    print("\n⚠️  No webhook request ID found")
    print("This might mean the webhook was never attempted")

print("\n" + "="*60)
print("To resend the webhook:")
print(f"1. Go to: https://dashboard.stripe.com/events/{found_event['id']}")
print("2. Click 'Resend' or 'Send test webhook'")
print("3. Or use: stripe events resend {found_event['id']}")
print("="*60)

