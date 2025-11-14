#!/usr/bin/env python3
"""
Helper script to set up database connection from Supabase CLI or manual input
"""

import re
import sys
from pathlib import Path


def update_env_file(password: str = None, connection_string: str = None):
    """Update DATABASE_URL in .env file"""
    env_file = Path(".env")

    if not env_file.exists():
        print("ERROR: .env file not found")
        sys.exit(1)

    # Read current .env
    with open(env_file, "r") as f:
        lines = f.readlines()

    # Update DATABASE_URL
    updated = False
    new_lines = []

    for line in lines:
        if line.startswith("DATABASE_URL="):
            if connection_string:
                # Use provided connection string
                new_lines.append(f"DATABASE_URL={connection_string}\n")
            elif password:
                # Replace password in existing URL
                new_url = re.sub(
                    r"postgresql\+asyncpg://postgres:\[.*?\]@",
                    f"postgresql+asyncpg://postgres:{password}@",
                    line,
                )
                new_url = re.sub(
                    r"postgresql\+asyncpg://postgres:[^@]+@",
                    f"postgresql+asyncpg://postgres:{password}@",
                    new_url,
                )
                new_lines.append(new_url)
            else:
                new_lines.append(line)
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        # Add DATABASE_URL if it doesn't exist
        if connection_string:
            new_lines.append(f"DATABASE_URL={connection_string}\n")
        elif password:
            new_lines.append(
                f"DATABASE_URL=postgresql+asyncpg://postgres:{password}@db.plcjedvqfchvurukdzoy.supabase.co:5432/postgres\n"
            )

    # Write back
    with open(env_file, "w") as f:
        f.writelines(new_lines)

    print("✓ Updated DATABASE_URL in .env file")


if __name__ == "__main__":
    import argparse
    import getpass

    parser = argparse.ArgumentParser(description="Update database connection in .env")
    parser.add_argument("--password", "-p", help="Database password")
    parser.add_argument("--connection-string", "-c", help="Full connection string")
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Prompt for password interactively",
    )

    args = parser.parse_args()

    if args.connection_string:
        update_env_file(connection_string=args.connection_string)
    elif args.password:
        update_env_file(password=args.password)
    elif args.interactive:
        print("\nEnter your Supabase database password:")
        print(
            "(Get it from: https://supabase.com/dashboard/project/plcjedvqfchvurukdzoy/settings/database)"
        )
        password = getpass.getpass("Password: ")
        if password:
            update_env_file(password=password)
            print("\n✓ Password updated! Testing connection...")
            # Test connection
            import asyncio
            import sys
            from pathlib import Path

            sys.path.insert(0, str(Path(__file__).parent.parent))
            from app.database import get_db

            async def test():
                try:
                    async for db in get_db():
                        await db.execute("SELECT 1")
                        print("✓ Connection test successful!")
                        return True
                except Exception as e:
                    print(f"✗ Connection test failed: {e}")
                    return False

            asyncio.run(test())
        else:
            print("✗ No password provided")
            sys.exit(1)
    else:
        print("""
Usage:
  python scripts/setup_database_connection.py --interactive
  python scripts/setup_database_connection.py --password YOUR_PASSWORD
  python scripts/setup_database_connection.py --connection-string "postgresql+asyncpg://postgres:PASSWORD@db.plcjedvqfchvurukdzoy.supabase.co:5432/postgres"

To get your password:
  1. Visit: https://supabase.com/dashboard/project/plcjedvqfchvurukdzoy/settings/database
  2. Copy the connection string from 'Connection string' → 'URI' tab
  3. Use --interactive to enter it securely, or use --connection-string/--password
        """)
        sys.exit(1)
