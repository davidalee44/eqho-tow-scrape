#!/usr/bin/env python3
"""Update customer metadata with initialize_org flags"""
import os
import sys
import json

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Get API key from environment, .env file, or argument
api_key = os.environ.get('STRIPE_LIVE_API_KEY') or os.environ.get('STRIPE_SECRET_KEY')

# Try to load from .env file if not in environment
if not api_key:
    try:
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if line.startswith('STRIPE_SECRET_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break
    except:
        pass

if len(sys.argv) > 1:
    api_key = sys.argv[1]

if not api_key:
    print("Error: Stripe API key not found")
    print("\nUsage:")
    print("  export STRIPE_SECRET_KEY='sk_live_...'")
    print("  python3 scripts/update_customer_metadata.py")
    print("\nOr provide it as an argument:")
    print("  python3 scripts/update_customer_metadata.py sk_live_...")
    sys.exit(1)

customer_id = "cus_TQ2nf9y5uQfW20"

# Metadata to set on customer
metadata = {
    "initialize_org": "true",
    "org_name": "TowPilot Marketing",
    "tag": "tow"
}

print(f"Updating customer {customer_id} metadata...")
print(f"Metadata: {json.dumps(metadata, indent=2)}")
print()

url = f"https://api.stripe.com/v1/customers/{customer_id}"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/x-www-form-urlencoded"
}

# Stripe API expects metadata as metadata[key]=value
data = {}
for key, value in metadata.items():
    data[f"metadata[{key}]"] = value

try:
    response = requests.post(url, headers=headers, data=data, timeout=30)
    
    if response.status_code == 200:
        customer = response.json()
        print("✓ Customer metadata updated successfully!")
        print(f"\nCustomer: {customer.get('id')}")
        print(f"Email: {customer.get('email')}")
        print(f"Metadata: {json.dumps(customer.get('metadata', {}), indent=2)}")
        print("\n" + "="*60)
        print("Next step: Resend the invoice.created webhook event")
        print("from Stripe Dashboard. The webhook handler should now")
        print("see initialize_org in customer.metadata and create the org.")
        print("="*60)
    else:
        print(f"✗ Error updating customer: {response.status_code}")
        print(response.text)
        sys.exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

