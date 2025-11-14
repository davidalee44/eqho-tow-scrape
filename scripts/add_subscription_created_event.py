#!/usr/bin/env python3
"""Add customer.subscription.created event to Stripe webhook endpoint"""
import os
import sys
import json

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Get API key from environment or argument
api_key = os.environ.get('STRIPE_LIVE_API_KEY')
if len(sys.argv) > 1:
    api_key = sys.argv[1]

if not api_key:
    print("Error: STRIPE_LIVE_API_KEY environment variable not set")
    print("\nUsage:")
    print("  export STRIPE_LIVE_API_KEY='rk_live_...'")
    print("  python3 scripts/add_subscription_created_event.py")
    print("\nOr provide it as an argument:")
    print("  python3 scripts/add_subscription_created_event.py rk_live_...")
    sys.exit(1)

webhook_endpoint_id = "we_1PLoXuCyexzwFObxY3d4TOcz"

# Current events (from the webhook endpoint)
current_events = [
    "charge.dispute.created",
    "checkout.session.completed",
    "customer.subscription.deleted",
    "invoice.created",
    "invoice.payment_failed",
    "invoice.payment_succeeded",
    "setup_intent.succeeded"
]

# Add the missing event
new_events = current_events + ["customer.subscription.created"]

print(f"Updating webhook endpoint: {webhook_endpoint_id}")
print(f"Current events: {len(current_events)}")
print(f"New events: {len(new_events)}")
print(f"Adding: customer.subscription.created")
print()

url = f"https://api.stripe.com/v1/webhook_endpoints/{webhook_endpoint_id}"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Stripe API expects events as array parameters
data = {}
for i, event in enumerate(new_events):
    data[f"enabled_events[{i}]"] = event

try:
    response = requests.post(url, headers=headers, data=data, timeout=30)
    
    if response.status_code == 200:
        endpoint = response.json()
        print("✓ Webhook endpoint updated successfully!")
        print(f"\nEnabled events ({len(endpoint.get('enabled_events', []))}):")
        for event in endpoint.get('enabled_events', []):
            marker = "✓" if event == "customer.subscription.created" else " "
            print(f"  {marker} {event}")
        print(f"\nWebhook URL: {endpoint.get('url')}")
        print(f"Status: {endpoint.get('status')}")
    else:
        print(f"✗ Error updating webhook: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("Next step: Resend the customer.subscription.created event")
print("from Stripe Dashboard to trigger organization creation.")
print("="*60)

