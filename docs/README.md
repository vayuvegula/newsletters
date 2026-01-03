# Documentation Index

Complete documentation for the Newsletter Analysis Pipeline.

## Getting Started

**New to the project?** Start here:

1. 📖 [Main README](../README.md) - Project overview and quick start
2. 🧪 [Testing Guide](TESTING.md) - **START HERE to try it out!**
3. 📋 [Implementation Plan](../IMPLEMENTATION_PLAN.md) - Overall roadmap

## Core Documentation

### Phase 4: Production Pipeline

- **[Phase 4 Implementation Guide](PHASE4_IMPLEMENTATION.md)**
  - SQLite database for state tracking
  - Deduplication strategy
  - Modular extraction configuration
  - Pipeline orchestration
  - Troubleshooting

- **[Multi-Newsletter Guide](MULTI_NEWSLETTER_GUIDE.md)**
  - Adding multiple newsletters
  - Per-newsletter extraction configs
  - Per-newsletter database deployment
  - Common scenarios and examples
  - Best practices

- **[Testing Guide](TESTING.md)** ⭐
  - Step-by-step testing instructions
  - Dry run and real runs
  - Verification steps
  - Troubleshooting common issues
  - Performance benchmarks

## Quick Reference

### 🚀 How to Try It Out

```bash
# 1. Verify setup
python3 scripts/check_notion_setup.py

# 2. Dry run (safe - no changes)
newsletter run --dry-run -n 1

# 3. Process one newsletter
newsletter run -n 1

# 4. Check Notion databases for results!
```

See [Testing Guide](TESTING.md) for complete details.

### 📝 How to Add Newsletters

```yaml
# config/newsletters.yaml
newsletters:
  - name: "Your Newsletter"
    email: "newsletter@example.com"
    enabled: true
    extraction_config: "default"
    database_set: "default"
```

See [Multi-Newsletter Guide](MULTI_NEWSLETTER_GUIDE.md) for examples.

### 🔧 How to Customize Extraction

```yaml
# config/extraction_config.yaml
stories:
  required_fields:
    - title
    - your_custom_field  # Add new fields!
```

See [Phase 4 Guide](PHASE4_IMPLEMENTATION.md#modular-extraction-config) for details.

## Configuration Files

### Required Setup

| File | Purpose | Setup |
|------|---------|-------|
| `config/credentials.yaml` | API keys, database IDs | Created manually, filled by setup scripts |
| `config/gmail_credentials.json` | Gmail OAuth client | Downloaded from Google Cloud Console |
| `config/gmail_token.json` | Gmail OAuth token | Created by `setup_gmail.py` |

### Customization

| File | Purpose | How to Modify |
|------|---------|---------------|
| `config/newsletters.yaml` | Newsletter whitelist | Add entries manually |
| `config/extraction_config.yaml` | Default extraction settings | Edit fields, prompts, categories |
| `config/extraction_executive.yaml` | Executive summary config | Use for strategic focus |
| `config/extraction_technical.yaml` | Technical deep-dive config | Use for research analysis |

## Architecture

### Components

```
newsletters/
├── src/
│   ├── extractors/        # Agentic extraction (Claude API)
│   ├── connectors/        # Gmail + Notion integrations
│   ├── storage/           # SQLite state tracking
│   └── cli.py             # Pipeline orchestration
├── config/                # Configuration files
├── scripts/               # Setup utilities
├── data/                  # Downloaded emails, extractions, database
└── docs/                  # This documentation
```

### Data Flow

```
Gmail API → Download → SQLite (track) → Extract (Claude) → Notion API
                ↓                            ↓
        .eml files                    .json files
```

## Guides by Use Case

### "I want to..."

**...try the system for the first time**
→ [Testing Guide](TESTING.md)

**...add more newsletters**
→ [Multi-Newsletter Guide](MULTI_NEWSLETTER_GUIDE.md#adding-a-new-newsletter-same-config)

**...change what insights are extracted**
→ [Phase 4 Guide](PHASE4_IMPLEMENTATION.md#modular-extraction-config)

**...use different extraction for different newsletters**
→ [Multi-Newsletter Guide](MULTI_NEWSLETTER_GUIDE.md#example-2-different-analysis-for-different-newsletters)

**...deploy to different Notion databases**
→ [Multi-Newsletter Guide](MULTI_NEWSLETTER_GUIDE.md#deploying-to-different-databases)

**...understand deduplication**
→ [Phase 4 Guide](PHASE4_IMPLEMENTATION.md#how-deduplication-works)

**...troubleshoot issues**
→ [Testing Guide](TESTING.md#common-issues-and-solutions)

**...see the implementation plan**
→ [Implementation Plan](../IMPLEMENTATION_PLAN.md)

## Command Reference

### Pipeline Commands

```bash
# Main pipeline
newsletter run                      # Process new newsletters
newsletter run -n 5                 # Process up to 5 emails
newsletter run --dry-run            # Preview without changes
newsletter run --force              # Reprocess all emails

# Individual operations
newsletter extract <file.eml>       # Extract from local file
newsletter show <extraction.json>  # Display results
newsletter status                   # Show system status
```

### Setup Commands

```bash
# Initial setup
python3 scripts/setup_gmail.py      # Gmail OAuth authentication
python3 scripts/setup_notion.py     # Create Notion databases

# Verification
python3 scripts/check_notion_setup.py  # Verify Notion configuration
```

### Database Commands

```bash
# View data
sqlite3 data/newsletter.db "SELECT * FROM newsletters;"
sqlite3 data/newsletter.db "SELECT * FROM processing_log;"

# Statistics
sqlite3 data/newsletter.db "SELECT COUNT(*), status FROM newsletters GROUP BY status;"
sqlite3 data/newsletter.db "SELECT SUM(tokens_used) FROM newsletters;"

# Reset (careful!)
rm data/newsletter.db              # Clear all state
```

## Development Phases

- ✅ **Phase 1**: Production code structure with agentic extraction
- ✅ **Phase 2**: Gmail API integration (read-only mode)
- ✅ **Phase 3**: Notion database integration
- ✅ **Phase 4**: Full pipeline automation with deduplication
- 🚧 **Phase 5**: Trend analysis across newsletters
- 🚧 **Phase 6**: Scheduled automation (cron/GitHub Actions)
- 🚧 **Phase 7**: Testing & deployment

## Examples

### Example 1: Single Newsletter, Default Config

```yaml
# config/newsletters.yaml
newsletters:
  - name: "The Batch"
    email: "thebatch@deeplearning.ai"
    enabled: true
    extraction_config: "default"
    database_set: "default"
```

### Example 2: Multiple Newsletters, Same Config

```yaml
newsletters:
  - name: "The Batch"
    email: "thebatch@deeplearning.ai"
    enabled: true
    extraction_config: "default"
    database_set: "default"

  - name: "TLDR AI"
    email: "dan@tldrnewsletter.com"
    enabled: true
    extraction_config: "default"
    database_set: "default"
```

### Example 3: Different Configs, Different Databases

```yaml
newsletters:
  - name: "Executive Brief"
    email: "brief@example.com"
    enabled: true
    extraction_config: "executive"    # Strategic focus
    database_set: "executive"          # Leadership databases

  - name: "Technical Deep Dive"
    email: "research@example.com"
    enabled: true
    extraction_config: "technical"    # Research focus
    database_set: "technical"          # Research databases
```

## Support

### Documentation

- This index for navigation
- Individual guides for deep dives
- Inline code comments
- Example configurations

### Debugging

- Detailed CLI output with progress indicators
- SQLite database for state inspection
- Local file storage (eml, json) for verification
- Comprehensive error messages

### Community

- GitHub Issues for bug reports
- Pull Requests for contributions
- Documentation updates welcome

---

**Ready to start?** → [Testing Guide](TESTING.md)
