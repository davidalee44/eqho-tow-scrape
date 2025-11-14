#!/usr/bin/env python3
"""Create a subscription in Stripe live mode"""
import subprocess
import json
import re
import sys

def get_live_api_key():
    """Get live mode API key from Stripe CLI config"""
    result = subprocess.run(
        ['stripe', 'config', '--list'],
        capture_output=True,
        text=True
    )
    
    for line in result.stdout.split('\n'):
        if 'live_mode_api_key' in line:
            # Extract the key value - format: live_mode_api_key = 'rk_live_...'
            # The key might be masked with asterisks, so try to get it from config --get
            if 'rk_live_' in line:
                match = re.search(r"rk_live_[A-Za-z0-9]+", line)
                if match:
                    return match.group(0)
    
    # Try using config --get instead
    result = subprocess.run(
        ['stripe', 'config', '--get', 'live_mode_api_key'],
        capture_output=True,
        text=True
    )
    
    # The output might be in format: live_mode_api_key = 'rk_live_...'
    for line in result.stdout.split('\n'):
        if 'rk_live_' in line:
            match = re.search(r"rk_live_[A-Za-z0-9]+", line)
            if match:
                return match.group(0)
    
    print("Error: Could not find live mode API key")
    print("Output:", result.stdout[:200])
    print("Make sure you're logged into Stripe CLI with: stripe login")
    sys.exit(1)

def create_subscription(api_key, customer_id, price_id):
    """Create subscription using Stripe API"""
    import requests
    
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
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

if __name__ == "__main__":
    customer_id = "cus_TQ2nf9y5uQfW20"
    price_id = "price_1PLp1XCyexzwFObxkRFlxkM8"  # Live mode legacy $0 price
    
    print("Getting live mode API key...")
    api_key = get_live_api_key()
    print(f"✓ Found API key: {api_key[:20]}...")
    
    print(f"\nCreating subscription for customer {customer_id}...")
    print(f"Using price: {price_id}")
    print("Metadata: initialize_org=true, org_name='TowPilot Marketing', tag='tow'")
    
    subscription = create_subscription(api_key, customer_id, price_id)
    
    print("\n✓ Subscription created successfully!")
    print(json.dumps(subscription, indent=2))

