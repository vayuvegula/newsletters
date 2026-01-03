#!/usr/bin/env python3
"""
Setup script for Gmail API authentication.

This script performs the initial OAuth flow to authenticate with Gmail.
It will open a browser window for you to grant permissions.

Usage:
    python scripts/setup_gmail.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from src.connectors.gmail import GmailConnector


def main():
    print("=" * 60)
    print("Gmail API Setup")
    print("=" * 60)

    # Load config
    config_path = Path("config/credentials.yaml")
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        print("Create config/credentials.yaml with your API keys first.")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    gmail_config = config.get('gmail', {})
    creds_file = gmail_config.get('credentials_file', 'config/gmail_credentials.json')
    token_file = gmail_config.get('token_file', 'config/gmail_token.json')

    # Check credentials exist
    if not Path(creds_file).exists():
        print(f"❌ Gmail credentials not found: {creds_file}")
        print("\nDownload from Google Cloud Console:")
        print("  1. Go to https://console.cloud.google.com")
        print("  2. Enable Gmail API")
        print("  3. Create OAuth 2.0 credentials (Desktop app)")
        print("  4. Download and save to", creds_file)
        sys.exit(1)

    print(f"\n📧 Gmail credentials found: {creds_file}")
    print(f"🔑 Token will be saved to: {token_file}")
    print("\nThis will open a browser window for OAuth authentication.")
    print("Grant permissions to read and modify Gmail.")

    input("\nPress Enter to continue...")

    # Initialize connector and authenticate
    try:
        connector = GmailConnector(
            credentials_path=creds_file,
            token_path=token_file
        )

        print("\n🔐 Starting OAuth flow...")
        connector.authenticate()

        print("\n✅ Gmail authentication successful!")
        print(f"Token saved to: {token_file}")

        # Test by searching for newsletters
        sender = gmail_config.get('sender_email', 'thebatch@deeplearning.ai')
        print(f"\n📊 Testing: Searching for newsletters from {sender}...")

        count = connector.get_message_count(sender)
        print(f"   Found {count} total messages from {sender}")

        if count > 0:
            print(f"\n✨ Setup complete! You can now fetch newsletters.")
        else:
            print(f"\n⚠️  No messages found from {sender}")
            print("   Make sure the email address is correct in config/credentials.yaml")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
