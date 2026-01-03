#!/usr/bin/env python3
"""CLI for newsletter analysis pipeline."""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import click
import yaml
from dotenv import load_dotenv

from .extractors import AgenticExtractor
from .connectors.gmail import GmailConnector
from .connectors.notion import NotionConnector
from .storage import Database


# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Newsletter analysis pipeline.

    Extract insights from newsletters and store them in Notion.
    """
    pass


@cli.command()
@click.argument('eml_files', nargs=-1, type=click.Path(exists=True))
@click.option('--output-dir', '-o', default='data/extractions',
              help='Output directory for JSON results')
@click.option('--verbose', '-v', is_flag=True,
              help='Show detailed analysis output')
def extract(eml_files, output_dir, verbose):
    """Extract insights from .eml newsletter files.

    Examples:
        newsletter extract data/newsletters/message1.eml
        newsletter extract data/newsletters/*.eml -o results/
    """
    if not eml_files:
        click.echo("Error: No .eml files provided", err=True)
        click.echo("Usage: newsletter extract <file.eml> [<file2.eml> ...]")
        sys.exit(1)

    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize extractor
    try:
        extractor = AgenticExtractor(
            progress_callback=lambda msg: click.echo(f"  {msg}"),
            verbose=verbose
        )
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nSet ANTHROPIC_API_KEY environment variable or use .env file")
        sys.exit(1)

    # Process each file
    success_count = 0
    for eml_file in eml_files:
        eml_path = Path(eml_file)
        click.echo(f"\n📧 Processing: {eml_path.name}")

        try:
            # Extract
            result = extractor.extract(eml_path)

            # Save result
            output_file = output_path / f"{eml_path.stem}_extraction.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)

            click.echo(f"✓ Saved to: {output_file}")

            # Show summary
            if 'executive_summary' in result:
                click.echo(f"\n  Summary: {result['executive_summary'][:200]}...")

            if 'stories' in result:
                click.echo(f"  Stories: {len(result['stories'])}")

            if '_metadata' in result:
                tokens = result['_metadata']['total_tokens']
                click.echo(f"  Tokens: {tokens:,}")

            success_count += 1

        except Exception as e:
            click.echo(f"✗ Failed: {e}", err=True)
            logger.exception(f"Extraction failed for {eml_path}")

    # Final summary
    click.echo(f"\n{'='*60}")
    click.echo(f"Processed {success_count}/{len(eml_files)} files successfully")


@cli.command()
def status():
    """Show pipeline status and configuration."""
    click.echo("Newsletter Pipeline Status")
    click.echo("=" * 60)

    # Check API keys
    click.echo("\n🔑 API Keys:")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    click.echo(f"  Anthropic: {'✓ Set' if anthropic_key else '✗ Not set'}")

    gmail_creds = os.getenv("GMAIL_CREDENTIALS_PATH")
    click.echo(f"  Gmail:     {'✓ Set' if gmail_creds else '✗ Not set (Phase 2)'}")

    notion_key = os.getenv("NOTION_API_KEY")
    click.echo(f"  Notion:    {'✓ Set' if notion_key else '✗ Not set (Phase 3)'}")

    # Check directories
    click.echo("\n📁 Directories:")
    dirs = {
        "Newsletters": "data/newsletters",
        "Extractions": "data/extractions",
        "Config": "config"
    }
    for name, path in dirs.items():
        exists = Path(path).exists()
        click.echo(f"  {name}: {path} {'✓' if exists else '✗ (will create)'}")

    # Show recent extractions
    click.echo("\n📊 Recent Extractions:")
    extraction_dir = Path("data/extractions")
    if extraction_dir.exists():
        extractions = sorted(extraction_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:5]
        if extractions:
            for ext in extractions:
                click.echo(f"  - {ext.name}")
        else:
            click.echo("  (none yet)")
    else:
        click.echo("  (directory not created)")


@cli.command()
@click.argument('extraction_file', type=click.Path(exists=True))
def show(extraction_file):
    """Display extraction results in a readable format.

    Example:
        newsletter show data/extractions/the_batch_extraction.json
    """
    with open(extraction_file) as f:
        data = json.load(f)

    click.echo("\n" + "=" * 60)
    click.echo("NEWSLETTER EXTRACTION")
    click.echo("=" * 60)

    # Executive summary
    if 'executive_summary' in data:
        click.echo(f"\n📋 Executive Summary:\n{data['executive_summary']}\n")

    # Stories
    if 'stories' in data:
        click.echo(f"\n📰 Stories ({len(data['stories'])}):\n")
        for i, story in enumerate(data['stories'], 1):
            click.echo(f"{i}. {story.get('title', 'Untitled')}")
            click.echo(f"   Category: {story.get('category', 'unknown')}")
            click.echo(f"   Confidence: {story.get('confidence', 'unknown')}")

            if 'key_facts' in story:
                click.echo(f"   Key Facts:")
                for fact in story['key_facts'][:3]:
                    click.echo(f"     • {fact}")

            if 'google_implications' in story:
                click.echo(f"   Google Implications: {story['google_implications'][:150]}...")

            click.echo()

    # Trends
    if 'trend_signals' in data:
        click.echo(f"\n📈 Trend Signals ({len(data['trend_signals'])}):\n")
        for trend in data['trend_signals']:
            click.echo(f"  • {trend.get('trend', 'Unknown')}: {trend.get('trajectory', 'unknown')}")

    # Metadata
    if '_metadata' in data:
        meta = data['_metadata']
        click.echo(f"\n📊 Metadata:")
        click.echo(f"  Model: {meta.get('model', 'unknown')}")
        click.echo(f"  Tokens: {meta.get('total_tokens', 0):,}")


@cli.group()
def gmail():
    """Gmail integration commands (Phase 2)."""
    pass


@gmail.command()
def test():
    """Test Gmail API connection."""
    click.echo("Gmail integration coming in Phase 2!")
    click.echo("This will test your Gmail API credentials.")


@cli.group()
def notion():
    """Notion integration commands (Phase 3)."""
    pass


@notion.command()
def test():
    """Test Notion API connection."""
    click.echo("Notion integration coming in Phase 3!")
    click.echo("This will test your Notion API credentials.")


@cli.command()
@click.option('--max-emails', '-n', default=10, help='Maximum emails to process per newsletter')
@click.option('--dry-run', is_flag=True, help='Preview what would be processed without making changes')
@click.option('--force', is_flag=True, help='Reprocess emails even if already in database')
def run(max_emails, dry_run, force):
    """Run the full pipeline: fetch → extract → upload.

    This command orchestrates the complete newsletter processing workflow:
    1. Connects to Gmail and fetches new newsletters
    2. Extracts insights using agentic analysis
    3. Uploads results to Notion databases
    4. Tracks processing state to avoid duplicates

    Examples:
        newsletter run                    # Process up to 10 new emails
        newsletter run -n 5               # Process up to 5 new emails
        newsletter run --dry-run          # Preview without processing
        newsletter run --force            # Reprocess all emails
    """
    click.echo("=" * 60)
    click.echo("NEWSLETTER PIPELINE")
    click.echo("=" * 60)

    if dry_run:
        click.echo("\n⚠️  DRY RUN MODE - No changes will be made\n")

    # Load configuration
    config_path = Path("config/credentials.yaml")
    newsletters_path = Path("config/newsletters.yaml")

    if not config_path.exists():
        click.echo("❌ Config file not found: config/credentials.yaml", err=True)
        click.echo("Run setup scripts first (setup_gmail.py, setup_notion.py)")
        sys.exit(1)

    if not newsletters_path.exists():
        click.echo("❌ Newsletter config not found: config/newsletters.yaml", err=True)
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    with open(newsletters_path) as f:
        newsletters_config = yaml.safe_load(f)

    # Initialize components
    click.echo("\n🔧 Initializing components...")

    try:
        # Database for tracking state
        db = Database(db_path=config.get('database', {}).get('path', 'data/newsletter.db'))
        click.echo("  ✓ Database connected")

        # Gmail connector
        gmail_config = config.get('gmail', {})
        gmail = GmailConnector(
            credentials_path=gmail_config.get('credentials_file', 'config/gmail_credentials.json'),
            token_path=gmail_config.get('token_file', 'config/gmail_token.json')
        )
        gmail.authenticate()  # Authenticate before using
        click.echo("  ✓ Gmail connected")

        # Notion connector
        notion_config = config.get('notion', {})
        notion = NotionConnector(api_key=notion_config.get('api_key'))
        click.echo("  ✓ Notion connected")

        # Extractor
        anthropic_config = config.get('anthropic', {})
        extractor = AgenticExtractor(
            api_key=anthropic_config.get('api_key'),
            progress_callback=lambda msg: click.echo(f"    {msg}"),
            verbose=False
        )
        click.echo("  ✓ Extractor initialized")

    except Exception as e:
        click.echo(f"\n❌ Initialization failed: {e}", err=True)
        logger.exception("Failed to initialize components")
        sys.exit(1)

    # Process each newsletter in whitelist
    newsletters = newsletters_config.get('newsletters', [])
    if not newsletters:
        click.echo("\n⚠️  No newsletters configured in config/newsletters.yaml")
        sys.exit(0)

    # Filter enabled newsletters
    enabled_newsletters = [n for n in newsletters if n.get('enabled', True)]
    if not enabled_newsletters:
        click.echo("\n⚠️  No enabled newsletters found in config/newsletters.yaml")
        sys.exit(0)

    click.echo(f"\n📬 Processing {len(enabled_newsletters)} enabled newsletter(s)...")

    total_processed = 0
    total_skipped = 0
    total_failed = 0

    for newsletter in enabled_newsletters:
        name = newsletter.get('name', 'Unknown')
        email = newsletter.get('email')

        if not email:
            click.echo(f"\n⚠️  Skipping {name}: No email configured")
            continue

        click.echo(f"\n{'─' * 60}")
        click.echo(f"📰 {name} ({email})")
        click.echo(f"{'─' * 60}")

        # Load newsletter-specific extraction config
        extraction_config_name = newsletter.get('extraction_config', 'default')
        if extraction_config_name == 'default':
            extraction_config_path = Path("config/extraction_config.yaml")
        elif extraction_config_name in ['executive', 'technical']:
            extraction_config_path = Path(f"config/extraction_{extraction_config_name}.yaml")
        else:
            extraction_config_path = Path(extraction_config_name)

        if extraction_config_path.exists():
            click.echo(f"  📋 Using extraction config: {extraction_config_path.name}")
        else:
            click.echo(f"  ⚠️  Extraction config not found: {extraction_config_path}, using default extractor")

        # Get newsletter-specific database set
        database_set_name = newsletter.get('database_set', 'default')
        database_sets = notion_config.get('database_sets', {})

        # Support legacy format (databases directly under notion)
        if not database_sets and 'databases' in notion_config:
            click.echo(f"  ⚠️  Using legacy database format - consider updating credentials.yaml")
            newsletter_db_id = notion_config['databases'].get('newsletters')
            stories_db_id = notion_config['databases'].get('stories')
        else:
            db_set = database_sets.get(database_set_name, {})
            if not db_set:
                click.echo(f"  ❌ Database set '{database_set_name}' not found in credentials.yaml", err=True)
                click.echo(f"  Available sets: {', '.join(database_sets.keys())}")
                continue

            newsletter_db_id = db_set.get('newsletters')
            stories_db_id = db_set.get('stories')

            if not newsletter_db_id or not stories_db_id:
                click.echo(f"  ❌ Database IDs not configured for set '{database_set_name}'", err=True)
                click.echo(f"  Run scripts/setup_notion.py or configure manually in credentials.yaml")
                continue

            click.echo(f"  💾 Using database set: {database_set_name}")

        try:
            # Get last processed date for smart querying
            since_date = None
            if not force:
                since_date = db.get_last_processed_date(email)
                if since_date:
                    click.echo(f"  📅 Last processed: {since_date}")

            # Search for new newsletters
            click.echo(f"  🔍 Searching for new emails...")
            message_ids = gmail.search_newsletters(
                sender_email=email,
                since_date=since_date,
                max_results=max_emails,
                unread_only=False
            )

            if not message_ids:
                click.echo(f"  ✓ No new emails found")
                continue

            click.echo(f"  📨 Found {len(message_ids)} email(s)")

            # Process each message
            for i, message_id in enumerate(message_ids, 1):
                click.echo(f"\n  [{i}/{len(message_ids)}] Processing {message_id[:12]}...")

                # Check if already processed (deduplication)
                if not force and db.is_processed(message_id):
                    click.echo(f"    ⏭️  Already processed, skipping")
                    total_skipped += 1
                    continue

                if dry_run:
                    click.echo(f"    🔍 Would process this email")
                    continue

                try:
                    # Download email
                    click.echo(f"    ⬇️  Downloading...")
                    # Create output directory and file path
                    output_dir = Path("data/newsletters")
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_path = output_dir / f"{message_id}.eml"

                    metadata = gmail.download_message(message_id, str(output_path))
                    eml_path = Path(metadata['file_path'])

                    # Add to database (only if not already exists)
                    if not db.is_processed(message_id):
                        db.add_newsletter(
                            message_id=message_id,
                            sender_email=email,
                            subject=metadata.get('subject'),
                            received_date=metadata.get('date')
                        )
                    db.mark_downloaded(message_id, str(eml_path))

                    # Extract insights
                    click.echo(f"    🧠 Extracting insights...")
                    extraction_result = extractor.extract(eml_path)

                    # Save extraction to file
                    extraction_dir = Path("data/extractions")
                    extraction_dir.mkdir(parents=True, exist_ok=True)
                    extraction_path = extraction_dir / f"{message_id}_extraction.json"

                    with open(extraction_path, 'w') as f:
                        json.dump(extraction_result, f, indent=2)

                    tokens_used = extraction_result.get('_metadata', {}).get('total_tokens', 0)
                    db.mark_extracted(message_id, str(extraction_path), tokens_used)

                    click.echo(f"    💾 Extracted ({tokens_used:,} tokens)")

                    # Upload to Notion
                    click.echo(f"    ⬆️  Uploading to Notion...")
                    page_id = notion.create_newsletter_page(
                        extraction_result,
                        database_id=newsletter_db_id
                    )

                    # Upload stories
                    stories = extraction_result.get('stories', [])
                    if stories and stories_db_id:
                        notion.create_story_pages(
                            newsletter_page_id=page_id,
                            stories=stories,
                            database_id=stories_db_id
                        )

                    db.mark_uploaded(message_id, page_id)

                    click.echo(f"    ✅ Completed successfully")
                    total_processed += 1

                except Exception as e:
                    click.echo(f"    ❌ Failed: {e}", err=True)
                    logger.exception(f"Failed to process message {message_id}")

                    # Mark as failed in database
                    try:
                        db.mark_failed(message_id, str(e))
                    except:
                        pass

                    total_failed += 1
                    continue

        except Exception as e:
            click.echo(f"\n❌ Error processing {name}: {e}", err=True)
            logger.exception(f"Failed to process newsletter {name}")
            continue

    # Final summary
    click.echo(f"\n{'=' * 60}")
    click.echo(f"SUMMARY")
    click.echo(f"{'=' * 60}")
    click.echo(f"  ✅ Processed: {total_processed}")
    click.echo(f"  ⏭️  Skipped:   {total_skipped}")
    click.echo(f"  ❌ Failed:    {total_failed}")

    if not dry_run:
        # Show database stats
        stats = db.get_stats()
        click.echo(f"\n📊 Database Stats:")
        click.echo(f"  Total newsletters: {stats['total']}")
        click.echo(f"  By status: {stats.get('by_status', {})}")
        click.echo(f"  Total tokens used: {stats['total_tokens']:,}")

    # Close database
    db.close()

    click.echo(f"\n✨ Pipeline complete!\n")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
