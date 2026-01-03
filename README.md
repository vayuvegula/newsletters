# Newsletters

Automated newsletter analysis pipeline with Gmail integration and Notion storage. Extracts strategic insights from newsletters using Claude AI.

## Status: ✅ Production Ready (Phase 4 Complete)

Fully automated pipeline with deduplication, state tracking, and modular extraction configuration.

## Features

- 📬 **Gmail Integration**: Automatically fetch newsletters (read-only mode)
- 🧠 **Agentic Extraction**: Two-pass Claude analysis for deep insights
- 📊 **Notion Databases**: Store insights in structured Notion databases
- 💾 **SQLite Tracking**: Prevent duplicate processing with state management
- 🔧 **Modular Config**: Easy iteration on extraction insights without code changes
- 📈 **Progress Tracking**: Full visibility into processing status
- 🔀 **Multi-Newsletter Support**: Process multiple newsletters with different configs
- 🎯 **Flexible Deployment**: Deploy to different databases based on analysis type

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/yourusername/newsletters.git
cd newsletters

# Install dependencies
pip install -r requirements.txt

# Install CLI tool
pip install -e .
```

### 2. Configuration

```bash
# Create config from template
cp config/credentials.yaml.template config/credentials.yaml

# Add your API keys to config/credentials.yaml:
# - Anthropic API key
# - Notion API key
# - Gmail credentials (from Google Cloud Console)

# Setup Gmail authentication
python3 scripts/setup_gmail.py

# Setup Notion databases
python3 scripts/setup_notion.py
```

### 3. Run Pipeline

```bash
# Process newsletters automatically
newsletter run

# Preview without making changes
newsletter run --dry-run

# Process specific number of emails
newsletter run -n 5

# View status
newsletter status
```

## Project Structure

```
newsletters/
├── src/                       # Production code
│   ├── extractors/           # Newsletter extraction (agentic, structured, deep)
│   ├── connectors/           # Gmail and Notion integrations
│   ├── storage/              # SQLite database for state tracking
│   └── cli.py                # Command-line interface
├── config/
│   ├── credentials.yaml      # API keys (gitignored)
│   ├── newsletters.yaml      # Newsletter whitelist
│   └── extraction_config.yaml # Modular extraction configuration
├── scripts/                   # Setup and utility scripts
├── experiments/              # Extraction method comparison tests
├── data/
│   ├── newsletters/          # Downloaded .eml files
│   ├── extractions/          # JSON extraction results
│   └── newsletter.db         # SQLite state database
└── docs/                     # Documentation
    ├── IMPLEMENTATION_PLAN.md
    └── PHASE4_IMPLEMENTATION.md
```

## Pipeline Workflow

```
Gmail → Download → Extract → Notion
  ↓        ↓         ↓         ↓
Track in SQLite Database (deduplication)
```

## Adding More Newsletters

Simply add to `config/newsletters.yaml`:

```yaml
newsletters:
  - name: "The Batch"
    email: "thebatch@deeplearning.ai"
    enabled: true
    extraction_config: "default"
    database_set: "default"

  - name: "TLDR AI"  # NEW NEWSLETTER!
    email: "dan@tldrnewsletter.com"
    enabled: true
    extraction_config: "default"
    database_set: "default"
```

**Different analysis types? Different databases?**
- Use `extraction_config: "executive"` for strategic summaries
- Use `extraction_config: "technical"` for deep research analysis
- Use `database_set: "executive"` to deploy to different Notion databases

See [Multi-Newsletter Guide](docs/MULTI_NEWSLETTER_GUIDE.md) for complete examples.

## Iterating on Extraction Insights

Want to change what insights are extracted? No code changes needed!

1. Edit `config/extraction_config.yaml`
2. Modify fields, categories, or prompts
3. Run `newsletter run --force` to reprocess

**Example**: Add new story field
```yaml
# config/extraction_config.yaml
stories:
  required_fields:
    - title
    - category
    - summary
    - author_sentiment  # NEW!
```

**Built-in configs:**
- `default` - Comprehensive analysis (all newsletters)
- `executive` - Strategic summaries (leadership briefings)
- `technical` - Deep research analysis (engineering/research teams)

See [Phase 4 Documentation](docs/PHASE4_IMPLEMENTATION.md) for details.

## Roadmap

- [x] **Phase 1**: Production code structure with agentic extraction
- [x] **Phase 2**: Gmail API integration (read-only mode)
- [x] **Phase 3**: Notion database integration
- [x] **Phase 4**: Full pipeline automation with deduplication
- [ ] **Phase 5**: Trend analysis across newsletters
- [ ] **Phase 6**: Scheduled automation (cron/GitHub Actions)
- [ ] **Phase 7**: Testing & deployment

## Documentation

- [Implementation Plan](IMPLEMENTATION_PLAN.md) - Overall project plan
- [Phase 4 Guide](docs/PHASE4_IMPLEMENTATION.md) - Pipeline automation details
- [Multi-Newsletter Guide](docs/MULTI_NEWSLETTER_GUIDE.md) - Managing multiple newsletters and configs

## Development

```bash
# Extract from local .eml file
newsletter extract data/newsletters/message.eml

# Show extraction results
newsletter show data/extractions/message_extraction.json

# View pipeline status
newsletter status
```

## Security

- Gmail: **Read-only access** (no delete/modify/send permissions)
- All credentials gitignored
- Local SQLite database (no remote access)
- Notion: Create-only permissions

## Cost

Approximately $0.30 per newsletter (The Batch):
- ~66k tokens per extraction
- Claude Sonnet 4: $3/MTok input, $15/MTok output

View total usage:
```bash
sqlite3 data/newsletter.db "SELECT SUM(tokens_used) FROM newsletters;"
```

## Troubleshooting

See [Phase 4 Documentation](docs/PHASE4_IMPLEMENTATION.md#troubleshooting) for common issues and solutions.
