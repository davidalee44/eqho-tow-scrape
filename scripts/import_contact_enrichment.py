#!/usr/bin/env python3
"""
Script to import contact enrichment data from Apify Contact Details Scraper runs

This matches enrichment data to existing companies by domain/website URL and updates
them with emails, phones, and social media links.

Usage:
    make import-contact-enrichment RUN_ID=<apify_run_id>
    Or: python scripts/import_contact_enrichment.py --run-id <run_id>
"""
import asyncio
import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.apify_service import ApifyService
from app.services.company_service import CompanyService
from app.database import get_db
from app.config import settings
from sqlalchemy import select
from app.models.company import Company


def extract_domain(url: str) -> Optional[str]:
    """Extract domain from URL"""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path
        # Remove www. prefix
        domain = domain.replace('www.', '')
        # Remove protocol if still present
        domain = domain.replace('http://', '').replace('https://', '')
        # Remove trailing slash
        domain = domain.rstrip('/')
        return domain.lower()
    except Exception:
        return None


def normalize_phone(phone: str) -> str:
    """Normalize phone number for matching"""
    if not phone:
        return ""
    # Remove common formatting
    phone = phone.replace('(', '').replace(')', '').replace('-', '').replace(' ', '')
    # Remove +1 prefix
    if phone.startswith('+1'):
        phone = phone[2:]
    elif phone.startswith('1') and len(phone) == 11:
        phone = phone[1:]
    return phone


async def match_and_enrich_companies(
    enrichment_data: list,
    dry_run: bool = False
):
    """Match enrichment data to companies and update them"""
    
    async for db in get_db():
        # Build domain -> enrichment mapping
        domain_map: Dict[str, Dict[str, Any]] = {}
        for item in enrichment_data:
            domain = extract_domain(item.get('url', ''))
            if domain:
                domain_map[domain] = item
        
        print(f"✓ Mapped {len(domain_map)} domains from enrichment data")
        
        # Get all companies with websites
        result = await db.execute(
            select(Company).where(Company.website.isnot(None))
        )
        companies = result.scalars().all()
        
        print(f"✓ Found {len(companies)} companies with websites")
        
        matched_count = 0
        updated_count = 0
        enrichment_stats = {
            'emails_added': 0,
            'phones_added': 0,
            'facebook_added': 0,
            'other_social_added': 0
        }
        
        for company in companies:
            company_domain = extract_domain(company.website)
            if not company_domain:
                continue
            
            # Try exact domain match
            enrichment = domain_map.get(company_domain)
            
            # Try variations (with/without www)
            if not enrichment:
                for domain_key in domain_map.keys():
                    if domain_key.replace('www.', '') == company_domain.replace('www.', ''):
                        enrichment = domain_map[domain_key]
                        break
            
            if not enrichment:
                continue
            
            matched_count += 1
            updates = {}
            
            # Add email if not present
            if enrichment.get('emails') and not company.email:
                emails = enrichment['emails']
                if emails:
                    # Use first valid email
                    email = emails[0]
                    if '@' in email and not email.endswith('@legit.com'):  # Filter out test emails
                        updates['email'] = email
                        enrichment_stats['emails_added'] += 1
            
            # Add phone if better/new
            if enrichment.get('phones'):
                phones = enrichment['phones']
                if phones:
                    # Check if we should update phone
                    current_phone = normalize_phone(company.phone_primary or '')
                    for phone in phones:
                        normalized = normalize_phone(phone)
                        if normalized and normalized != current_phone:
                            # Use first phone that's different
                            if not company.phone_dispatch:
                                updates['phone_dispatch'] = phone
                            break
            
            # Add Facebook page
            if enrichment.get('facebooks') and not company.facebook_page:
                facebooks = enrichment['facebooks']
                if facebooks:
                    updates['facebook_page'] = facebooks[0]
                    enrichment_stats['facebook_added'] += 1
            
            # Store other social media in services JSON
            social_links = {}
            if enrichment.get('linkedIns'):
                social_links['linkedin'] = enrichment['linkedIns'][0]
                enrichment_stats['other_social_added'] += 1
            if enrichment.get('instagrams'):
                social_links['instagram'] = enrichment['instagrams'][0]
                enrichment_stats['other_social_added'] += 1
            if enrichment.get('twitters'):
                social_links['twitter'] = enrichment['twitters'][0]
                enrichment_stats['other_social_added'] += 1
            if enrichment.get('youtubes'):
                social_links['youtube'] = enrichment['youtubes'][0]
                enrichment_stats['other_social_added'] += 1
            
            if social_links:
                # Merge with existing services
                current_services = company.services or {}
                if not isinstance(current_services, dict):
                    current_services = {}
                current_services.update(social_links)
                updates['services'] = current_services
            
            # Apply updates
            if updates:
                if dry_run:
                    print(f"\n  Would update: {company.name}")
                    for key, value in updates.items():
                        print(f"    {key}: {value}")
                else:
                    for key, value in updates.items():
                        setattr(company, key, value)
                    updated_count += 1
        
        if not dry_run:
            await db.commit()
        
        print(f"\n{'='*60}")
        print(f"Enrichment Complete!")
        print(f"{'='*60}")
        print(f"  ✓ Companies matched: {matched_count}")
        print(f"  ✓ Companies updated: {updated_count}")
        print(f"\n  Enrichment Details:")
        print(f"    📧 Emails added: {enrichment_stats['emails_added']}")
        print(f"    📞 Phones added: {enrichment_stats['phones_added']}")
        print(f"    📘 Facebook pages added: {enrichment_stats['facebook_added']}")
        print(f"    🔗 Other social links added: {enrichment_stats['other_social_added']}")
        
        break  # Exit the async generator


async def import_contact_enrichment(
    run_id: str,
    dry_run: bool = False
):
    """Import contact enrichment data from Apify run"""
    
    if not settings.apify_token:
        print("ERROR: APIFY_TOKEN not set in environment variables")
        sys.exit(1)
    
    if not settings.database_url:
        print("ERROR: DATABASE_URL not set in environment variables")
        sys.exit(1)
    
    apify_service = ApifyService()
    
    try:
        print(f"Downloading contact enrichment data from run: {run_id}")
        print("="*60)
        
        # Download enrichment data
        enrichment_data = await apify_service.download_run_data(run_id)
        
        if not enrichment_data:
            print(f"⚠ No data found in run {run_id}")
            return
        
        print(f"✓ Downloaded {len(enrichment_data)} enrichment records")
        
        # Match and enrich companies
        await match_and_enrich_companies(enrichment_data, dry_run=dry_run)
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await apify_service.close()


async def main():
    parser = argparse.ArgumentParser(description="Import contact enrichment data")
    parser.add_argument(
        "--run-id",
        type=str,
        required=True,
        help="Apify run ID for contact enrichment data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be updated without making changes",
    )
    
    args = parser.parse_args()
    
    await import_contact_enrichment(
        run_id=args.run_id,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    asyncio.run(main())

