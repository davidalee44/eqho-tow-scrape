#!/usr/bin/env python3
"""Create a new subscription with updated price metadata"""
import os
import sys
import json
import requests

def get_live_api_key():
    api_key = os.environ.get('STRIPE_LIVE_API_KEY') or os.environ.get('STRIPE_SECRET_KEY')
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
    api_key = get_live_api_key()
    
    customer_id = "cus_TQ2nf9y5uQfW20"
    price_id = "price_1PLp1XCyexzwFObxkRFlxkM8"  # Updated price with metadata
    
    print("=" * 60)
    print("Creating NEW subscription with updated price metadata")
    print("=" * 60)
    print(f"Customer: {customer_id}")
    print(f"Price: {price_id} (now has metadata)")
    print()
    
    url = "https://api.stripe.com/v1/subscriptions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Create subscription with metadata
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
        print("\n✓ New subscription created!")
        print(f"Subscription ID: {subscription['id']}")
        print(f"Status: {subscription['status']}")
        print(f"Latest Invoice: {subscription.get('latest_invoice')}")
        print()
        print("This will trigger:")
        print("  1. invoice.created webhook")
        print("  2. Invoice will have updated price.metadata in the payload")
        print("  3. Handler should be able to check price.metadata to create org")
        print()
        print("=" * 60)
        print("Next: Wait for invoice.created webhook to fire")
        print("The invoice should now have price.metadata populated!")
        print("=" * 60)
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

