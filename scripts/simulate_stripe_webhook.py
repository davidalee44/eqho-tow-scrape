#!/usr/bin/env python3
"""Simulate Stripe webhook to create organization in Eqho"""
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

# Webhook endpoint
webhook_url = "https://api.eqho.ai/v1/billing/webhook"

# Stripe webhook secret (from Stripe Dashboard)
webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
if not webhook_secret:
    print("Error: STRIPE_WEBHOOK_SECRET environment variable not set")
    print("\nTo get the webhook secret:")
    print("1. Go to Stripe Dashboard → Webhooks")
    print("2. Click on the webhook endpoint: https://api.eqho.ai/v1/billing/webhook")
    print("3. Copy the 'Signing secret' (starts with whsec_)")
    print("4. Set it: export STRIPE_WEBHOOK_SECRET='whsec_...'")
    sys.exit(1)

# Subscription data from Stripe - matching exact Stripe format
subscription_data = {
    "id": "sub_1STDAUCyexzwFObxg19JwADY",
    "object": "subscription",
    "application": None,
    "application_fee_percent": None,
    "automatic_tax": {
        "disabled_reason": None,
        "enabled": False,
        "liability": None
    },
    "billing_cycle_anchor": 1763088922,
    "billing_cycle_anchor_config": None,
    "billing_mode": {
        "flexible": None,
        "type": "classic"
    },
    "billing_thresholds": None,
    "cancel_at": None,
    "cancel_at_period_end": False,
    "canceled_at": None,
    "cancellation_details": {
        "comment": None,
        "feedback": None,
        "reason": None
    },
    "collection_method": "charge_automatically",
    "created": 1763088922,
    "currency": "usd",
    "current_period_end": 1765680922,
    "current_period_start": 1763088922,
    "customer": "cus_TQ2nf9y5uQfW20",
    "days_until_due": None,
    "default_payment_method": None,
    "default_source": None,
    "default_tax_rates": [],
    "description": None,
    "discount": None,
    "discounts": [],
    "ended_at": None,
    "invoice_settings": {
        "account_tax_ids": None,
        "issuer": {
            "type": "self"
        }
    },
    "items": {
        "object": "list",
        "data": [
            {
                "id": "si_TQ3H59i5hh6q9q",
                "object": "subscription_item",
                "billing_thresholds": None,
                "created": 1763088922,
                "current_period_end": 1765680922,
                "current_period_start": 1763088922,
                "discounts": [],
                "metadata": {},
                "plan": {
                    "id": "price_1PLp1XCyexzwFObxkRFlxkM8",
                    "object": "plan",
                    "active": True,
                    "aggregate_usage": None,
                    "amount": 0,
                    "amount_decimal": "0",
                    "billing_scheme": "per_unit",
                    "created": 1716998807,
                    "currency": "usd",
                    "interval": "month",
                    "interval_count": 1,
                    "livemode": True,
                    "metadata": {},
                    "meter": None,
                    "nickname": None,
                    "product": "prod_QCDSbbKqd7MIXF",
                    "tiers_mode": None,
                    "transform_usage": None,
                    "trial_period_days": None,
                    "usage_type": "licensed"
                },
                "price": {
                    "id": "price_1PLp1XCyexzwFObxkRFlxkM8",
                    "object": "price",
                    "active": True,
                    "billing_scheme": "per_unit",
                    "created": 1716998807,
                    "currency": "usd",
                    "custom_unit_amount": None,
                    "livemode": True,
                    "lookup_key": None,
                    "metadata": {},
                    "nickname": None,
                    "product": "prod_QCDSbbKqd7MIXF",
                    "recurring": {
                        "aggregate_usage": None,
                        "interval": "month",
                        "interval_count": 1,
                        "meter": None,
                        "trial_period_days": None,
                        "usage_type": "licensed"
                    },
                    "tax_behavior": "unspecified",
                    "tiers_mode": None,
                    "transform_quantity": None,
                    "type": "recurring",
                    "unit_amount": 0,
                    "unit_amount_decimal": "0"
                },
                "quantity": 1,
                "subscription": "sub_1STDAUCyexzwFObxg19JwADY",
                "tax_rates": []
            }
        ],
        "has_more": False,
        "total_count": 1,
        "url": "/v1/subscription_items?subscription=sub_1STDAUCyexzwFObxg19JwADY"
    },
    "latest_invoice": "in_1STDAUCyexzwFObxNX31MEpE",
    "livemode": True,
    "metadata": {
        "initialize_org": "true",
        "org_name": "TowPilot Marketing",
        "tag": "tow"
    },
    "next_pending_invoice_item_invoice": None,
    "on_behalf_of": None,
    "pause_collection": None,
    "payment_settings": {
        "payment_method_options": None,
        "payment_method_types": None,
        "save_default_payment_method": "off"
    },
    "pending_invoice_item_interval": None,
    "pending_setup_intent": "seti_1STDAUCyexzwFObxKvILcC5z",
    "pending_update": None,
    "plan": {
        "id": "price_1PLp1XCyexzwFObxkRFlxkM8",
        "object": "plan",
        "active": True,
        "aggregate_usage": None,
        "amount": 0,
        "amount_decimal": "0",
        "billing_scheme": "per_unit",
        "created": 1716998807,
        "currency": "usd",
        "interval": "month",
        "interval_count": 1,
        "livemode": True,
        "metadata": {},
        "meter": None,
        "nickname": None,
        "product": "prod_QCDSbbKqd7MIXF",
        "tiers_mode": None,
        "transform_usage": None,
        "trial_period_days": None,
        "usage_type": "licensed"
    },
    "quantity": 1,
    "schedule": None,
    "start_date": 1763088922,
    "status": "active",
    "test_clock": None,
    "transfer_data": None,
    "trial_end": None,
    "trial_settings": {
        "end_behavior": {
            "missing_payment_method": "create_invoice"
        }
    },
    "trial_start": None
}

# Create Stripe webhook event payload - matching exact Stripe format
event_payload = {
    "id": f"evt_simulated_{int(time.time())}",
    "object": "event",
    "api_version": "2023-10-16",
    "created": int(time.time()),
    "data": {
        "object": subscription_data,
        "previous_attributes": None
    },
    "livemode": True,
    "pending_webhooks": 1,
    "request": {
        "id": f"req_simulated_{int(time.time())}",
        "idempotency_key": None
    },
    "type": "customer.subscription.created"
}

# Create Stripe signature (Stripe expects the raw payload bytes, not JSON string)
# Stripe signs the raw request body, so we need to send it as bytes
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

print(f"Sending webhook to: {webhook_url}")
print(f"Event type: {event_payload['type']}")
print(f"Subscription: {subscription_data['id']}")
print(f"Organization: {subscription_data['metadata']['org_name']}")
print()

try:
    # Send raw JSON bytes to match Stripe's signature format
    response = requests.post(
        webhook_url,
        headers=headers,
        data=payload_bytes,  # Send as raw bytes, not JSON
        timeout=30
    )
    
    print(f"Response Status: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text[:500]}")
    
    if response.status_code == 200:
        print("\n✓ Webhook delivered successfully!")
        print("Organization should be created in Eqho.")
    else:
        print(f"\n✗ Webhook failed with status {response.status_code}")
        print("Check the response above for error details.")
        
except requests.exceptions.RequestException as e:
    print(f"✗ Error sending webhook: {e}")

