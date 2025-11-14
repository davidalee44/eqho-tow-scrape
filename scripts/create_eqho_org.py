#!/usr/bin/env python3
"""Create organization in Eqho directly via API"""
import os
import sys
import json

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

# Get API key from environment or argument
api_key = os.environ.get('EQHO_API_TOKEN') or os.environ.get('EQHO_API_KEY')
if len(sys.argv) > 1:
    api_key = sys.argv[1]

if not api_key:
    print("Error: EQHO_API_TOKEN environment variable not set")
    print("\nUsage:")
    print("  export EQHO_API_TOKEN='your-eqho-api-token'")
    print("  python3 scripts/create_eqho_org.py")
    print("\nOr provide it as an argument:")
    print("  python3 scripts/create_eqho_org.py your-api-token")
    sys.exit(1)

# Organization details from Stripe subscription metadata
org_name = "TowPilot Marketing"
org_tag = "tow"
customer_id = "cus_TQ2nf9y5uQfW20"
subscription_id = "sub_1STDAUCyexzwFObxg19JwADY"

print(f"Creating organization in Eqho:")
print(f"  Name: {org_name}")
print(f"  Tag: {org_tag}")
print(f"  Stripe Customer: {customer_id}")
print(f"  Stripe Subscription: {subscription_id}")
print()

# Try to create organization via Eqho API
# The webhook endpoint is: https://api.eqho.ai/v1/billing/webhook
# But we need to find the organization creation endpoint
# Let's try the admin/organization endpoint

base_url = "https://api.eqho.ai"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

# Try different possible endpoints
endpoints_to_try = [
    "/v1/organizations",
    "/v1/admin/organizations",
    "/v1/orgs",
    "/api/v1/organizations",
]

print("Attempting to create organization...")

for endpoint in endpoints_to_try:
    url = f"{base_url}{endpoint}"
    print(f"\nTrying: {url}")
    
    payload = {
        "name": org_name,
        "tag": org_tag,
        "stripe_customer_id": customer_id,
        "stripe_subscription_id": subscription_id,
        "metadata": {
            "initialize_org": "true",
            "org_name": org_name,
            "tag": org_tag
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            print(f"✓ Organization created successfully!")
            print(json.dumps(result, indent=2))
            sys.exit(0)
        elif response.status_code == 404:
            print(f"  Endpoint not found, trying next...")
            continue
        else:
            print(f"  Response: {response.text[:200]}")
    except requests.exceptions.RequestException as e:
        print(f"  Error: {e}")
        continue

print("\n✗ Could not create organization via API endpoints")
print("\nPossible reasons:")
print("1. Organization creation requires admin/superadmin permissions")
print("2. Organization creation is only available via Stripe webhook")
print("3. Different API endpoint structure")
print("\nAlternative solutions:")
print("1. Check Eqho admin dashboard to create organization manually")
print("2. Resend the Stripe webhook event from Stripe Dashboard")
print("3. Contact Eqho support to create the organization")
print("4. Check Eqho API documentation for organization creation endpoint")

