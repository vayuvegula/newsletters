#!/usr/bin/env python3
"""
Check Notion setup and optionally update credentials.yaml with database IDs.

This script helps you verify your Notion setup and add missing database IDs
to config/credentials.yaml.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from src.connectors.notion import NotionConnector


def main():
    print("=" * 60)
    print("Notion Setup Checker")
    print("=" * 60)

    # Load config
    config_path = Path("config/credentials.yaml")
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    notion_config = config.get('notion', {})
    api_key = notion_config.get('api_key')

    if not api_key:
        print("❌ Notion API key not found in config/credentials.yaml")
        sys.exit(1)

    print("\n✓ Notion API key found")

    # Check current database IDs
    newsletters_db = notion_config.get('databases', {}).get('newsletters', '')
    stories_db = notion_config.get('databases', {}).get('stories', '')

    print("\n📊 Current Configuration:")
    print(f"  Newsletter DB: {newsletters_db if newsletters_db else '(not set)'}")
    print(f"  Stories DB:    {stories_db if stories_db else '(not set)'}")

    if newsletters_db and stories_db:
        print("\n✅ Databases are already configured!")

        # Test connection
        print("\n🔍 Testing connection to databases...")
        connector = NotionConnector(api_key=api_key)

        try:
            # Try to query the databases to verify they exist
            connector.client.databases.retrieve(newsletters_db)
            print("  ✓ Newsletter database accessible")
        except Exception as e:
            print(f"  ❌ Newsletter database error: {e}")

        try:
            connector.client.databases.retrieve(stories_db)
            print("  ✓ Stories database accessible")
        except Exception as e:
            print(f"  ❌ Stories database error: {e}")

        sys.exit(0)

    # Databases not configured
    print("\n⚠️  Database IDs not configured!")
    print("\nYou have two options:")
    print("\n1. Run the setup script to create new databases:")
    print("   python3 scripts/setup_notion.py")
    print("\n2. If you already created databases, enter their IDs manually:")

    choice = input("\nDo you want to enter database IDs now? (y/n): ").strip().lower()

    if choice != 'y':
        print("\nRun scripts/setup_notion.py to create databases.")
        sys.exit(0)

    # Get database IDs from user
    print("\n📋 Enter Database IDs:")
    print("(You can find these in the database URLs in Notion)")
    print("Format: https://www.notion.so/XXXXX?v=...")
    print("The ID is the XXXXX part (32 characters)\n")

    newsletter_id = input("Newsletter Database ID: ").strip().replace('-', '')
    stories_id = input("Stories Database ID: ").strip().replace('-', '')

    if len(newsletter_id) != 32 or len(stories_id) != 32:
        print("\n❌ Invalid database ID length (should be 32 characters)")
        sys.exit(1)

    # Update config
    print("\n💾 Updating config/credentials.yaml...")
    config['notion']['databases']['newsletters'] = newsletter_id
    config['notion']['databases']['stories'] = stories_id

    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print("✓ Config updated successfully!")

    # Test the IDs
    print("\n🔍 Testing database IDs...")
    connector = NotionConnector(api_key=api_key)

    try:
        connector.client.databases.retrieve(newsletter_id)
        print("  ✓ Newsletter database accessible")
    except Exception as e:
        print(f"  ❌ Newsletter database error: {e}")

    try:
        connector.client.databases.retrieve(stories_id)
        print("  ✓ Stories database accessible")
    except Exception as e:
        print(f"  ❌ Stories database error: {e}")

    print("\n✅ Setup complete! You can now run: newsletter run")


if __name__ == "__main__":
    main()
