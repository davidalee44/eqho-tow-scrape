#!/usr/bin/env python3
"""Script to check Stripe product metadata for 'tow' and client creation flags"""
import os
import sys
import json
from typing import Dict, Any, List

try:
    import stripe
except ImportError:
    print("Error: stripe package not installed. Install with: pip install stripe")
    sys.exit(1)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_API_KEY")

if not stripe.api_key:
    print("Error: STRIPE_SECRET_KEY or STRIPE_API_KEY environment variable not set")
    sys.exit(1)


def check_product_metadata(product: Dict[str, Any]) -> Dict[str, Any]:
    """Check if product has relevant metadata"""
    metadata = product.get("metadata", {})
    result = {
        "product_id": product.get("id"),
        "name": product.get("name"),
        "has_tow_flag": metadata.get("tow") == "true" or metadata.get("tow") == True,
        "tow_value": metadata.get("tow"),
        "has_create_client_flag": False,
        "create_client_value": None,
        "all_metadata": metadata
    }
    
    # Check for various possible flags for creating clients
    create_client_keys = [
        "create_client", "create_new_client", "build_client", 
        "new_client", "setup_client", "onboard_client",
        "trigger_client_creation", "should_create_client"
    ]
    
    for key in create_client_keys:
        if key in metadata:
            result["has_create_client_flag"] = True
            result["create_client_key"] = key
            result["create_client_value"] = metadata.get(key)
            break
    
    return result


def main():
    """Main function to check all products"""
    print("Fetching Stripe products...")
    
    # Get all products
    products = []
    has_more = True
    starting_after = None
    
    while has_more:
        params = {"limit": 100}
        if starting_after:
            params["starting_after"] = starting_after
        
        response = stripe.Product.list(**params)
        products.extend(response.data)
        has_more = response.has_more
        if response.data:
            starting_after = response.data[-1].id
    
    print(f"Found {len(products)} products\n")
    
    # Check products with relevant metadata
    relevant_products = []
    
    for product in products:
        result = check_product_metadata(product)
        if result["has_tow_flag"] or result["has_create_client_flag"] or result["all_metadata"]:
            relevant_products.append(result)
    
    # Print results
    if relevant_products:
        print("=" * 80)
        print("PRODUCTS WITH RELEVANT METADATA:")
        print("=" * 80)
        
        for product in relevant_products:
            print(f"\nProduct: {product['name']}")
            print(f"  ID: {product['product_id']}")
            print(f"  Has 'tow' flag: {product['has_tow_flag']} (value: {product['tow_value']})")
            print(f"  Has create client flag: {product['has_create_client_flag']}")
            if product['has_create_client_flag']:
                print(f"    Key: {product.get('create_client_key')}")
                print(f"    Value: {product['create_client_value']}")
            print(f"  All metadata: {json.dumps(product['all_metadata'], indent=4)}")
            print("-" * 80)
    else:
        print("No products found with 'tow' or client creation metadata flags")
        print("\nChecking setup/onboarding products for metadata...")
        
        # Check setup products specifically
        setup_keywords = ["setup", "get started", "onboarding", "implementation", "commitment"]
        setup_products = [
            p for p in products 
            if any(keyword in p.name.lower() for keyword in setup_keywords)
        ]
        
        print(f"\nFound {len(setup_products)} setup/onboarding products:")
        for product in setup_products[:10]:  # Show first 10
            result = check_product_metadata(product)
            print(f"\n  {product.name} ({product.id})")
            print(f"    Metadata: {json.dumps(result['all_metadata'], indent=6)}")


if __name__ == "__main__":
    main()

