#!/usr/bin/env python3
"""Create subscription for a customer (clean start)"""
import os
import sys
import json
import requests

def get_live_api_key():
    api_key = os.environ.get('STRIPE_SECRET_KEY')
    if not api_key:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('STRIPE_SECRET_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
    if not api_key:
        print("Error: Stripe API key not found")
        sys.exit(1)
    return api_key

if __name__ == "__main__":
    # Default to the new customer from Eqho frontend
    customer_id = sys.argv[1] if len(sys.argv) > 1 else "cus_TQ53r3o8gkLorT"
    price_id = sys.argv[2] if len(sys.argv) > 2 else "price_1PLp1XCyexzwFObxkRFlxkM8"
    
    api_key = get_live_api_key()
    
    print("=" * 60)
    print("CREATING SUBSCRIPTION")
    print("=" * 60)
    print(f"Customer: {customer_id}")
    print(f"Price: {price_id}")
    print()
    
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
    
    print("Creating subscription...")
    response = requests.post(url, headers=headers, data=data, timeout=30)
    
    if response.status_code == 200:
        subscription = response.json()
        print("\n✓ Subscription created successfully!")
        print(f"\nSubscription ID: {subscription['id']}")
        print(f"Status: {subscription['status']}")
        print(f"Latest Invoice: {subscription.get('latest_invoice')}")
        print()
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print("The invoice.created webhook should fire automatically")
        print("and find the organization by account_id!")
        print("=" * 60)
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

