#!/usr/bin/env python3
"""
Add VP Insights properties to existing Notion Stories database.

This script updates your Stories database schema to include all VP insights fields
without affecting existing data.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from notion_client import Client
import yaml


def load_credentials():
    """Load Notion credentials."""
    creds_path = Path("config/credentials.yaml")
    with open(creds_path) as f:
        creds = yaml.safe_load(f)
    return creds['notion']


def add_vp_insights_properties(client: Client, database_id: str):
    """
    Add VP insights properties to Stories database.

    Args:
        client: Notion client
        database_id: Stories database ID
    """
    print(f"\n📊 Adding VP Insights properties to database...")
    print(f"Database ID: {database_id}")

    # Define VP insights properties
    vp_properties = {
        "Insight Type": {
            "select": {
                "options": [
                    {"name": "Strategic Implication", "color": "blue"},
                    {"name": "Belief Update", "color": "purple"},
                    {"name": "Execution Risk", "color": "red"},
                    {"name": "Time Horizon Signal", "color": "orange"},
                    {"name": "Second-Order Effect", "color": "green"}
                ]
            }
        },
        "Core Claim": {
            "rich_text": {}
        },
        "Why It Matters": {
            "rich_text": {}
        },
        "Affected Functions": {
            "multi_select": {
                "options": [
                    {"name": "Engineering", "color": "blue"},
                    {"name": "Product", "color": "green"},
                    {"name": "Data", "color": "purple"},
                    {"name": "GTM", "color": "orange"},
                    {"name": "Leadership", "color": "red"},
                    {"name": "Research", "color": "pink"}
                ]
            }
        },
        "Time Horizon": {
            "select": {
                "options": [
                    {"name": "Now", "color": "red"},
                    {"name": "6-12mo", "color": "orange"},
                    {"name": "12-24mo", "color": "blue"},
                    {"name": "24mo+", "color": "gray"}
                ]
            }
        },
        "Confidence Level": {
            "select": {
                "options": [
                    {"name": "High", "color": "green"},
                    {"name": "Medium", "color": "yellow"},
                    {"name": "Speculative", "color": "red"}
                ]
            }
        },
        "Contrarian Angle": {
            "rich_text": {}
        },
        "Execution Constraint": {
            "rich_text": {}
        },
        "Second-Order Effect": {
            "rich_text": {}
        },
        "Follow-Up Questions": {
            "rich_text": {}
        },
        "Strategic Implication": {
            "rich_text": {}
        },
        "Source Context": {
            "rich_text": {}
        }
    }

    # Get current database schema
    database = client.databases.retrieve(database_id=database_id)
    existing_props = database.get("properties", {})

    print(f"\nExisting properties: {list(existing_props.keys())}")

    # Add new properties
    added = []
    skipped = []

    for prop_name, prop_config in vp_properties.items():
        if prop_name in existing_props:
            skipped.append(prop_name)
            print(f"  ⏭️  Skipping '{prop_name}' (already exists)")
        else:
            added.append(prop_name)
            print(f"  ➕ Adding '{prop_name}'...")

    # Update database with new properties
    if added:
        # Merge new properties with existing
        all_properties = {**existing_props, **vp_properties}

        try:
            client.databases.update(
                database_id=database_id,
                properties=vp_properties  # Only send new properties
            )
            print(f"\n✅ Successfully added {len(added)} new properties!")
            print(f"   Added: {', '.join(added)}")
        except Exception as e:
            print(f"\n❌ Error updating database: {e}")
            return False
    else:
        print(f"\n✅ All VP insights properties already exist!")

    if skipped:
        print(f"   Skipped: {', '.join(skipped)}")

    return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("ADD VP INSIGHTS PROPERTIES TO NOTION DATABASE")
    print("=" * 60)

    # Load credentials
    try:
        notion_config = load_credentials()
        api_key = notion_config['api_key']
        database_sets = notion_config.get('database_sets', {})
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        print("   Make sure config/credentials.yaml exists and has Notion config")
        sys.exit(1)

    # Initialize Notion client
    client = Client(auth=api_key)
    print("✓ Notion client initialized")

    # Get Stories database ID
    default_set = database_sets.get('default', {})
    stories_db_id = default_set.get('stories')

    if not stories_db_id:
        print("\n❌ Stories database ID not found in credentials.yaml")
        print("   Run scripts/setup_notion.py first to create databases")
        sys.exit(1)

    # Add VP insights properties
    success = add_vp_insights_properties(client, stories_db_id)

    if success:
        print("\n" + "=" * 60)
        print("✅ VP INSIGHTS DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run: newsletter run -n 1 --force")
        print("2. Check your Notion Stories database for VP insights fields")
        print("3. You should now see fields like:")
        print("   - Insight Type")
        print("   - Core Claim")
        print("   - Why It Matters")
        print("   - Contrarian Angle")
        print("   - etc.")
    else:
        print("\n❌ Setup failed. Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
