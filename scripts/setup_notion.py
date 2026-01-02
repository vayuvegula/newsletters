#!/usr/bin/env python3
"""
Setup script for Notion databases.

This script creates the Newsletter and Stories databases in your Notion workspace.

Usage:
    python scripts/setup_notion.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from src.connectors.notion import NotionConnector


def main():
    print("=" * 60)
    print("Notion Database Setup")
    print("=" * 60)

    # Load config
    config_path = Path("config/credentials.yaml")
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("Create config/credentials.yaml with your Notion API key first.")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    notion_config = config.get('notion', {})
    api_key = notion_config.get('api_key')

    if not api_key:
        print("❌ Notion API key not found in config/credentials.yaml")
        print("\nGet your API key:")
        print("  1. Go to https://www.notion.so/my-integrations")
        print("  2. Create new integration")
        print("  3. Copy the 'Internal Integration Token'")
        print("  4. Add to config/credentials.yaml under notion.api_key")
        sys.exit(1)

    print(f"\n🔑 Notion API key found")

    # Test connection
    print("\n📡 Testing Notion connection...")
    connector = NotionConnector(api_key=api_key)

    if not connector.test_connection():
        print("❌ Connection failed. Check your API key.")
        sys.exit(1)

    print("✅ Connection successful!")

    # Create databases
    print("\n📊 Creating databases...")
    print("   (These will be created in your Notion workspace)")

    input("\nPress Enter to create databases...")

    try:
        # Create Newsletter database
        print("\n1️⃣  Creating 'AI Newsletter Insights' database...")
        newsletter_db_id = connector.create_newsletter_database()
        print(f"   ✓ Database ID: {newsletter_db_id}")

        # Create Stories database
        print("\n2️⃣  Creating 'Newsletter Stories' database...")
        stories_db_id = connector.create_stories_database()
        print(f"   ✓ Database ID: {stories_db_id}")

        # Update config file
        print("\n📝 Updating config/credentials.yaml with database IDs...")
        config['notion']['databases']['newsletters'] = newsletter_db_id
        config['notion']['databases']['stories'] = stories_db_id

        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print("   ✓ Config updated")

        print("\n" + "=" * 60)
        print("✨ Setup Complete!")
        print("=" * 60)
        print(f"\n📋 Newsletter Database: {newsletter_db_id}")
        print(f"📰 Stories Database: {stories_db_id}")
        print("\n🔗 Find them in your Notion workspace:")
        print("   - AI Newsletter Insights")
        print("   - Newsletter Stories")
        print("\n💡 Next step: Share these databases with your integration")
        print("   (Click '...' → 'Add connections' → Select your integration)")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
