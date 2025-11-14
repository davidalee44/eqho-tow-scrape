#!/usr/bin/env python3
"""Set customer.metadata.account_id to link Stripe customer to Eqho org"""
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
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/set_customer_account_id.py <eqho_org_id>")
        print()
        print("Example:")
        print("  python3 scripts/set_customer_account_id.py 65b96d473a1934b055687945")
        sys.exit(1)
    
    eqho_org_id = sys.argv[1]
    api_key = get_live_api_key()
    customer_id = "cus_TQ2nf9y5uQfW20"
    
    print("=" * 60)
    print("Linking Stripe Customer to Eqho Organization")
    print("=" * 60)
    print(f"Customer: {customer_id}")
    print(f"Eqho Org ID: {eqho_org_id}")
    print()
    
    url = f"https://api.stripe.com/v1/customers/{customer_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Update customer metadata with account_id
    data = {
        "metadata[account_id]": eqho_org_id,
        "metadata[initialize_org]": "true",
        "metadata[org_name]": "TowPilot Marketing",
        "metadata[tag]": "tow"
    }
    
    print("Updating customer metadata...")
    response = requests.post(url, headers=headers, data=data, timeout=30)
    
    if response.status_code == 200:
        customer = response.json()
        print("\n✓ Customer metadata updated successfully!")
        print(f"\nCustomer: {customer.get('id')}")
        print(f"Email: {customer.get('email')}")
        print(f"\nMetadata:")
        metadata = customer.get('metadata', {})
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        print()
        print("=" * 60)
        print("Next: Resend invoice.created webhook")
        print("It should now find the organization by account_id!")
        print("=" * 60)
    else:
        print(f"✗ Error: {response.status_code}")
        print(response.text)
        sys.exit(1)

