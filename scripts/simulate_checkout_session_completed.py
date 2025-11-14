#!/usr/bin/env python3
"""Simulate checkout.session.completed webhook to create organization"""
import os
import sys
import json
import hmac
import hashlib
import time

try:
    import requests
except ImportError:
    print("Error: requests library not found. Install with: pip install requests")
    sys.exit(1)

webhook_url = "https://api.eqho.ai/v1/billing/webhook"
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
if not webhook_secret:
    print("Error: STRIPE_WEBHOOK_SECRET environment variable not set")
    sys.exit(1)

# Get API key for fetching customer
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

customer_id = "cus_TQ2nf9y5uQfW20"
subscription_id = "sub_1STEhHCyexzwFObx3SQwTbmB"

# Fetch customer to get email
print(f"Fetching customer {customer_id}...")
customer_response = requests.get(
    f"https://api.stripe.com/v1/customers/{customer_id}",
    headers={"Authorization": f"Bearer {api_key}"}
)
if customer_response.status_code != 200:
    print(f"Error fetching customer: {customer_response.status_code}")
    sys.exit(1)
customer = customer_response.json()

# Fetch subscription to get price details
print(f"Fetching subscription {subscription_id}...")
sub_response = requests.get(
    f"https://api.stripe.com/v1/subscriptions/{subscription_id}",
    headers={"Authorization": f"Bearer {api_key}"}
)
if sub_response.status_code != 200:
    print(f"Error fetching subscription: {sub_response.status_code}")
    sys.exit(1)
subscription = sub_response.json()

# Build checkout.session.completed event
# This is what Stripe sends when a checkout session completes
checkout_session_data = {
    "id": f"cs_test_{int(time.time())}",
    "object": "checkout.session",
    "after_expiration": None,
    "allow_promotion_codes": None,
    "amount_subtotal": 0,
    "amount_total": 0,
    "automatic_tax": {
        "enabled": False,
        "status": None
    },
    "billing_address_collection": None,
    "cancel_url": None,
    "client_reference_id": None,
    "client_secret": None,
    "consent": None,
    "consent_collection": None,
    "created": int(time.time()),
    "currency": "usd",
    "currency_conversion": None,
    "custom_fields": [],
    "custom_text": {
        "shipping_address": None,
        "submit": None,
        "terms_of_service_acceptance": None
    },
    "customer": customer_id,
    "customer_creation": "always",
    "customer_details": {
        "address": None,
        "email": customer.get("email", "dave@eqho.ai"),
        "name": customer.get("name", "Dave Leee"),
        "phone": None,
        "tax_exempt": "none",
        "tax_ids": []
    },
    "customer_email": customer.get("email", "dave@eqho.ai"),
    "expires_at": None,
    "invoice": subscription.get("latest_invoice"),
    "invoice_creation": {
        "enabled": True,
        "invoice_data": {
            "metadata": {
                "initialize_org": "true",
                "org_name": "TowPilot Marketing",
                "tag": "tow"
            }
        }
    },
    "livemode": True,
    "locale": None,
    "metadata": {
        "initialize_org": "true",
        "org_name": "TowPilot Marketing",
        "tag": "tow"
    },
    "mode": "subscription",
    "payment_intent": None,
    "payment_link": None,
    "payment_method_collection": "if_required",
    "payment_method_options": {},
    "payment_method_types": ["card"],
    "payment_status": "paid",
    "phone_number_collection": {
        "enabled": False
    },
    "recovered_from": None,
    "saved_payment_method_options": None,
    "setup_intent": subscription.get("pending_setup_intent"),
    "shipping_address_collection": None,
    "shipping_cost": None,
    "shipping_details": None,
    "shipping_options": [],
    "status": "complete",
    "submit_type": None,
    "subscription": subscription_id,
    "success_url": None,
    "total_details": {
        "amount_discount": 0,
        "amount_shipping": 0,
        "amount_tax": 0
    },
    "ui_mode": None,
    "url": None
}

event_payload = {
    "id": f"evt_checkout_{int(time.time())}",
    "object": "event",
    "api_version": "2023-10-16",
    "created": int(time.time()),
    "data": {
        "object": checkout_session_data,
        "previous_attributes": None
    },
    "livemode": True,
    "pending_webhooks": 1,
    "request": {
        "id": f"req_checkout_{int(time.time())}",
        "idempotency_key": None
    },
    "type": "checkout.session.completed"
}

# Generate signature
payload_bytes = json.dumps(event_payload, separators=(',', ':')).encode('utf-8')
timestamp = int(time.time())
signed_payload = f"{timestamp}.{payload_bytes.decode('utf-8')}".encode('utf-8')
signature = hmac.new(
    webhook_secret.encode('utf-8'),
    signed_payload,
    hashlib.sha256
).hexdigest()

headers = {
    "Stripe-Signature": f"t={timestamp},v1={signature}",
    "Content-Type": "application/json"
}

print(f"\nSending checkout.session.completed webhook to: {webhook_url}")
print(f"Customer: {customer_id}")
print(f"Subscription: {subscription_id}")
print(f"Metadata: {checkout_session_data['metadata']}")
print()

try:
    response = requests.post(
        webhook_url,
        headers=headers,
        data=payload_bytes,
        timeout=30
    )

    print(f"Response Status: {response.status_code}")
    print(f"Response Body: {response.text[:500]}")

    if response.status_code == 200:
        print("\n✓ checkout.session.completed webhook delivered!")
        print("Organization should be created in Eqho.")
        print("\nNow invoice.created should find the existing org.")
    else:
        print(f"\n✗ Webhook failed with status {response.status_code}")
        print("Check the response above for error details.")

except requests.exceptions.RequestException as e:
    print(f"✗ Error sending webhook: {e}")

