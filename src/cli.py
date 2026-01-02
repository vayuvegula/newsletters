#!/usr/bin/env python3
"""CLI for newsletter analysis pipeline."""

import json
import logging
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from .extractors import AgenticExtractor


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
def run():
    """Run the full pipeline: fetch → extract → upload (Phase 4)."""
    click.echo("Full pipeline integration coming in Phase 4!")
    click.echo("This will:")
    click.echo("  1. Fetch new newsletters from Gmail")
    click.echo("  2. Extract insights using agentic analysis")
    click.echo("  3. Upload results to Notion")


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
