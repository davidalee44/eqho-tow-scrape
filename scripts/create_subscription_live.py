#!/usr/bin/env python3
"""Create a subscription in Stripe live mode - requires live API key"""
import os
import sys
import json

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Get API key from environment variable or prompt
api_key = os.environ.get('STRIPE_LIVE_API_KEY')
if not api_key:
    print("Error: STRIPE_LIVE_API_KEY environment variable not set")
    print("\nUsage:")
    print("  export STRIPE_LIVE_API_KEY='rk_live_...'")
    print("  python3 scripts/create_subscription_live.py")
    print("\nOr provide it as an argument:")
    print("  python3 scripts/create_subscription_live.py rk_live_...")
    sys.exit(1)

if len(sys.argv) > 1:
    api_key = sys.argv[1]

customer_id = "cus_TQ2nf9y5uQfW20"
price_id = "price_1PLp1XCyexzwFObxkRFlxkM8"  # Live mode legacy $0 price

url = "https://api.stripe.com/v1/subscriptions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "customer": customer_id,
    "items[0][price]": price_id,
    "metadata[initialize_org]": "true",
    "metadata[org_name]": "TowPilot Marketing",
    "metadata[tag]": "tow"
}

print(f"Creating subscription for customer {customer_id}...")
print(f"Using price: {price_id}")
print("Metadata: initialize_org=true, org_name='TowPilot Marketing', tag='tow'")
print()

response = requests.post(url, headers=headers, data=data)

if response.status_code == 200:
    subscription = response.json()
    print("✓ Subscription created successfully!")
    print(json.dumps(subscription, indent=2))
    print(f"\nSubscription ID: {subscription.get('id')}")
    print(f"Status: {subscription.get('status')}")
    print(f"Metadata: {subscription.get('metadata')}")
else:
    print(f"✗ Error: {response.status_code}")
    print(response.text)
    sys.exit(1)

