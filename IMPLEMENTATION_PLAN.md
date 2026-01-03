# Production Newsletter Pipeline - Implementation Plan

## Executive Summary

Transform the experimental extraction code into a production-ready pipeline that:
1. **Fetches** newsletters from Gmail via API
2. **Analyzes** them using the proven test2_agentic method
3. **Stores** insights in Notion database
4. **Tracks** trends and themes over time

**Timeline:** 5-7 implementation phases (can be done incrementally)

---

## Phase 1: Project Restructuring 🏗️

### Goal
Move from experimentation to production-ready codebase.

### Tasks

1. **Create production source structure:**
```
newsletters/
├── src/
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── base.py              # Base extractor interface
│   │   └── agentic.py           # Production version of test2_agentic.py
│   ├── connectors/
│   │   ├── __init__.py
│   │   ├── gmail.py             # Gmail API integration
│   │   └── notion.py            # Notion API integration
│   ├── storage/
│   │   ├── __init__.py
│   │   └── database.py          # Local DB (SQLite) for tracking
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── trends.py            # Trend analysis across newsletters
│   └── cli.py                   # CLI interface
├── scripts/
│   ├── setup_gmail.py           # One-time Gmail setup
│   └── setup_notion.py          # One-time Notion setup
├── config/
│   ├── newsletters.yaml         # Existing config
│   ├── credentials.example.yaml # Template for API keys
│   └── notion_schema.json       # Notion database schema
├── data/                        # Local storage (gitignored)
│   ├── newsletters/             # Downloaded .eml files
│   ├── extractions/             # JSON results
│   └── newsletter.db            # SQLite tracking database
├── experiments/                 # Keep for reference
├── tests/
│   └── test_extractors.py
└── requirements.txt             # Production dependencies
```

2. **Update dependencies:**
```txt
# Core
anthropic>=0.40.0
httpx>=0.27.0
beautifulsoup4>=4.12.0
lxml>=5.0.0

# Gmail API
google-auth>=2.25.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.110.0

# Notion API
notion-client>=2.2.0

# Storage & Analysis
sqlalchemy>=2.0.0
pandas>=2.0.0

# CLI
click>=8.1.0
python-dotenv>=1.0.0
pyyaml>=6.0

# Development
pytest>=7.4.0
black>=23.0.0
```

### Deliverables
- [ ] New directory structure created
- [ ] `src/extractors/agentic.py` - refactored from test2_agentic.py
- [ ] `requirements.txt` updated
- [ ] Basic CLI skeleton (`python -m src.cli --help`)

---

## Phase 2: Gmail API Integration 📧

### Goal
Automatically fetch newsletters from Gmail based on whitelist.

### Architecture

```python
# src/connectors/gmail.py

class GmailConnector:
    def __init__(self, credentials_path: str):
        """Initialize Gmail API connection"""

    def authenticate(self) -> None:
        """Handle OAuth flow, save token"""

    def search_newsletters(self,
                          sender_email: str,
                          since_date: str = None,
                          unread_only: bool = True) -> list[str]:
        """
        Search for newsletters matching criteria.
        Returns message IDs.
        """

    def download_message(self, message_id: str, output_path: str) -> str:
        """
        Download message as .eml file.
        Returns path to saved file.
        """

    def mark_as_processed(self, message_id: str, label: str = "PROCESSED"):
        """Add label to processed messages"""
```

### Setup Process

1. **Gmail API Credentials:**
   - Create project in Google Cloud Console
   - Enable Gmail API
   - Create OAuth 2.0 credentials (Desktop app)
   - Download `credentials.json`

2. **First-time authentication:**
```bash
python scripts/setup_gmail.py
# Opens browser for OAuth consent
# Saves token to config/gmail_token.json
```

3. **Configuration:**
```yaml
# config/credentials.yaml
gmail:
  credentials_file: "config/gmail_credentials.json"
  token_file: "config/gmail_token.json"
  labels:
    processed: "Newsletters/Processed"
    failed: "Newsletters/Failed"
```

### Query Strategy

For each newsletter in `newsletters.yaml`:
```
from:{email} after:{last_processed_date} is:unread
```

### Tasks
- [ ] Implement `GmailConnector` class
- [ ] Create `setup_gmail.py` script
- [ ] Add Gmail credentials template to config
- [ ] Implement message download as .eml
- [ ] Add Gmail query builder
- [ ] Implement label management (mark processed)

### Deliverables
```bash
# Test Gmail connection
python -m src.cli gmail test

# Download new newsletters
python -m src.cli gmail fetch --dry-run
python -m src.cli gmail fetch
```

---

## Phase 3: Notion Database Integration 🗄️

### Goal
Store extraction results in Notion for easy viewing and collaboration.

### Notion Database Schema

**Database: "AI Newsletter Insights"**

| Property | Type | Description |
|----------|------|-------------|
| Title | Title | Newsletter subject line |
| Source | Select | "The Batch", "TLDR", etc. |
| Date | Date | Newsletter publish date |
| Executive Summary | Text | 3-4 sentence summary |
| Stories Count | Number | # of stories extracted |
| Stories | Relation | → Stories database |
| Trend Signals | Multi-select | Tags for trends |
| Status | Select | Processing, Ready, Failed |
| Processed At | Date | When extraction completed |
| Token Cost | Number | API tokens used |
| Raw Data | URL | Link to JSON file |

**Database: "Stories"**

| Property | Type | Description |
|----------|------|-------------|
| Title | Title | Story headline |
| Newsletter | Relation | ← Newsletter |
| Category | Select | competitive_intelligence, talent_market, etc. |
| Companies | Multi-select | Meta, OpenAI, Google, etc. |
| Key Facts | Text | Bullet points |
| Google Implications | Text | Strategic implications |
| Confidence | Select | High, Medium, Low |
| Links | URL | Links worth following |

**Database: "Trends" (Phase 5)**

| Property | Type | Description |
|----------|------|-------------|
| Trend | Title | Trend name |
| First Seen | Date | When first detected |
| Last Seen | Date | Most recent mention |
| Frequency | Number | # of newsletters mentioning |
| Trajectory | Select | Accelerating, Stable, Declining |
| Related Stories | Relation | ← Stories |

### Implementation

```python
# src/connectors/notion.py

class NotionConnector:
    def __init__(self, api_key: str, database_ids: dict):
        """Initialize Notion client"""

    def create_newsletter_page(self, extraction_result: dict) -> str:
        """
        Create page in Newsletter database.
        Returns page ID.
        """

    def create_story_pages(self,
                          newsletter_page_id: str,
                          stories: list[dict]) -> list[str]:
        """
        Create story pages linked to newsletter.
        Returns story page IDs.
        """

    def update_processing_status(self,
                                 page_id: str,
                                 status: str) -> None:
        """Update newsletter processing status"""
```

### Setup Process

1. **Notion Integration:**
   - Go to notion.so/my-integrations
   - Create new integration
   - Copy API key
   - Share databases with integration

2. **Database setup:**
```bash
python scripts/setup_notion.py
# Creates databases with proper schema
# Outputs database IDs for config
```

3. **Configuration:**
```yaml
# config/credentials.yaml
notion:
  api_key: "secret_xyz..."
  databases:
    newsletters: "abc123..."
    stories: "def456..."
    trends: "ghi789..."
```

### Tasks
- [ ] Implement `NotionConnector` class
- [ ] Create `setup_notion.py` script (creates DBs)
- [ ] Implement newsletter page creation
- [ ] Implement story page creation with relations
- [ ] Add error handling and retry logic
- [ ] Create schema export to JSON

### Deliverables
```bash
# Test Notion connection
python -m src.cli notion test

# Upload a test extraction
python -m src.cli notion upload data/extractions/test.json
```

---

## Phase 4: Production Pipeline Integration 🔄

### Goal
Connect all pieces into a working end-to-end pipeline.

### Workflow

```
┌─────────────┐
│ 1. Fetch    │  Gmail API → Download .eml files
└──────┬──────┘
       │
┌──────▼──────┐
│ 2. Extract  │  Agentic Analyzer → JSON results
└──────┬──────┘
       │
┌──────▼──────┐
│ 3. Store    │  → Local DB + Notion
└──────┬──────┘
       │
┌──────▼──────┐
│ 4. Track    │  Update processing status
└─────────────┘
```

### Local Database (SQLite)

Track processing state to avoid duplicates:

```sql
-- newsletters table
CREATE TABLE newsletters (
    id INTEGER PRIMARY KEY,
    message_id TEXT UNIQUE,
    sender_email TEXT,
    subject TEXT,
    received_date TIMESTAMP,
    downloaded_at TIMESTAMP,
    eml_path TEXT,
    processed_at TIMESTAMP,
    extraction_path TEXT,
    notion_page_id TEXT,
    status TEXT,  -- pending, processing, completed, failed
    error_message TEXT,
    tokens_used INTEGER
);

-- processing_log table
CREATE TABLE processing_log (
    id INTEGER PRIMARY KEY,
    newsletter_id INTEGER,
    timestamp TIMESTAMP,
    event TEXT,  -- downloaded, extracted, uploaded, etc.
    details TEXT,
    FOREIGN KEY (newsletter_id) REFERENCES newsletters(id)
);
```

### Main Pipeline Script

```python
# src/cli.py

@click.group()
def cli():
    """Newsletter analysis pipeline"""
    pass

@cli.command()
@click.option('--dry-run', is_flag=True)
def run_pipeline(dry_run: bool):
    """Run full pipeline: fetch → extract → upload"""

    # 1. Load config
    config = load_config()

    # 2. Initialize connectors
    gmail = GmailConnector(config['gmail'])
    notion = NotionConnector(config['notion'])
    extractor = AgenticExtractor(config['anthropic'])
    db = Database(config['database'])

    # 3. For each whitelisted newsletter
    for newsletter in config['newsletters']:

        # 3a. Search Gmail
        message_ids = gmail.search_newsletters(
            newsletter['email'],
            since_date=db.get_last_processed_date(newsletter['email'])
        )

        logger.info(f"Found {len(message_ids)} new messages from {newsletter['name']}")

        # 3b. Process each message
        for msg_id in message_ids:
            try:
                # Download
                eml_path = gmail.download_message(msg_id, f"data/newsletters/{msg_id}.eml")
                db.mark_downloaded(msg_id, eml_path)

                # Extract
                result = extractor.extract(eml_path)
                result_path = f"data/extractions/{msg_id}.json"
                save_json(result, result_path)
                db.mark_extracted(msg_id, result_path, result['_metadata']['total_tokens'])

                # Upload to Notion
                if not dry_run:
                    page_id = notion.create_newsletter_page(result)
                    notion.create_story_pages(page_id, result['stories'])
                    db.mark_uploaded(msg_id, page_id)

                    # Mark processed in Gmail
                    gmail.mark_as_processed(msg_id)

                logger.info(f"✓ Processed {msg_id}")

            except Exception as e:
                logger.error(f"✗ Failed {msg_id}: {e}")
                db.mark_failed(msg_id, str(e))
```

### CLI Commands

```bash
# Full pipeline
python -m src.cli run --dry-run        # Preview
python -m src.cli run                  # Execute

# Individual steps
python -m src.cli gmail fetch          # Just download
python -m src.cli extract data/newsletters/*.eml  # Just extract
python -m src.cli notion upload data/extractions/*.json  # Just upload

# Status
python -m src.cli status               # Show processing stats
python -m src.cli list --pending       # List pending newsletters
```

### Tasks
- [ ] Implement SQLite database schema
- [ ] Create `Database` class for tracking
- [ ] Refactor `test2_agentic.py` into `AgenticExtractor` class
- [ ] Build CLI with click
- [ ] Implement main pipeline orchestration
- [ ] Add comprehensive logging
- [ ] Add error handling and retry logic
- [ ] Create dry-run mode

### Deliverables
- [ ] Working end-to-end pipeline
- [ ] CLI tool with all commands
- [ ] Logging to file + console
- [ ] Error recovery and retries

---

## Phase 5: Trend Analysis Features 📊

### Goal
Analyze newsletters over time to identify recurring topics and track trend evolution.

### Analysis Features

#### 1. **Topic Clustering**

```python
# src/analysis/trends.py

def identify_recurring_topics(extractions: list[dict]) -> list[Topic]:
    """
    Analyze multiple newsletter extractions to find recurring topics.

    Returns:
        Topics with frequency, sentiment, companies involved
    """
    # Use Claude to analyze patterns across extractions
    # Group similar stories by semantic similarity
    # Track frequency over time
```

Example output:
```json
{
  "topics": [
    {
      "name": "AI Reasoning Models",
      "frequency": 8,
      "first_seen": "2025-01-01",
      "last_seen": "2025-12-26",
      "related_stories": [12, 45, 67, 89, ...],
      "key_companies": ["OpenAI", "DeepSeek", "Google"],
      "sentiment": "accelerating"
    }
  ]
}
```

#### 2. **Trend Trajectory**

```python
def analyze_trend_trajectory(topic: str, timeframe: str = "6m") -> TrendReport:
    """
    Analyze how a topic has evolved over time.

    Returns:
        - Mention frequency over time
        - Sentiment changes
        - Key milestones
        - Prediction of future trajectory
    """
```

#### 3. **Competitive Intelligence Dashboard**

Track company mentions over time:
- Meta: 45 mentions (↑ 20% vs last quarter)
- OpenAI: 38 mentions (↓ 5% vs last quarter)
- Google: 52 mentions (↑ 10% vs last quarter)

### CLI Commands

```bash
# Analyze all extractions
python -m src.cli analyze trends --since 2025-01-01

# Specific topic
python -m src.cli analyze topic "reasoning models" --timeline

# Company mentions
python -m src.cli analyze company "Meta" --compare "OpenAI,Google"

# Export report
python -m src.cli analyze report --format pdf --output "Q4_2025_AI_Trends.pdf"
```

### Notion Integration

Create trend pages that auto-update:
- **Trend Dashboard** page with rollup formulas
- **Company Tracker** with mention counts
- **Timeline View** of all newsletters

### Tasks
- [ ] Implement topic clustering algorithm
- [ ] Build trend trajectory analysis
- [ ] Create company mention tracker
- [ ] Design trend visualization (charts)
- [ ] Add Notion trend database integration
- [ ] Build report generation (PDF/HTML)

---

## Phase 6: Automation & Scheduling 🤖

### Goal
Run pipeline automatically on a schedule.

### Options

#### Option A: Cron Job (Simple)

```bash
# crontab -e
# Run every 6 hours
0 */6 * * * cd /path/to/newsletters && python -m src.cli run >> logs/pipeline.log 2>&1
```

#### Option B: Systemd Timer (Linux)

```ini
# /etc/systemd/system/newsletter-pipeline.timer
[Unit]
Description=Newsletter Pipeline Timer

[Timer]
OnCalendar=*-*-* 00,06,12,18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

#### Option C: GitHub Actions (Cloud)

```yaml
# .github/workflows/process_newsletters.yml
name: Process Newsletters

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  process:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run pipeline
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GMAIL_CREDENTIALS: ${{ secrets.GMAIL_CREDENTIALS }}
          NOTION_API_KEY: ${{ secrets.NOTION_API_KEY }}
        run: python -m src.cli run
```

### Monitoring

Add notifications:
- Slack/Discord webhook on failures
- Daily summary email
- Notion status page

### Tasks
- [ ] Create systemd service files (if Linux)
- [ ] Add GitHub Actions workflow
- [ ] Implement notification system
- [ ] Add health check endpoint
- [ ] Create monitoring dashboard

---

## Phase 7: Testing & Documentation 📚

### Testing Strategy

```python
# tests/test_extractors.py
def test_agentic_extractor():
    extractor = AgenticExtractor()
    result = extractor.extract("tests/fixtures/sample.eml")

    assert "executive_summary" in result
    assert len(result["stories"]) > 0
    assert result["_metadata"]["total_tokens"] > 0

# tests/test_gmail.py
def test_gmail_connector(mock_gmail_api):
    connector = GmailConnector(credentials)
    messages = connector.search_newsletters("test@example.com")
    assert len(messages) > 0

# tests/test_notion.py
def test_notion_upload(mock_notion_api):
    connector = NotionConnector(api_key, db_ids)
    page_id = connector.create_newsletter_page(sample_extraction)
    assert page_id is not None
```

### Documentation

1. **README.md** - Project overview, quick start
2. **docs/SETUP.md** - Detailed setup instructions
3. **docs/ARCHITECTURE.md** - System design
4. **docs/API.md** - API documentation
5. **docs/TROUBLESHOOTING.md** - Common issues

### Tasks
- [ ] Write unit tests (80%+ coverage)
- [ ] Write integration tests
- [ ] Create comprehensive README
- [ ] Document all CLI commands
- [ ] Add inline code documentation
- [ ] Create setup guide with screenshots

---

## Security & Credentials Management 🔒

### Sensitive Files (add to .gitignore)

```gitignore
# Credentials
config/credentials.yaml
config/gmail_credentials.json
config/gmail_token.json
config/.env

# Data
data/
*.eml
*.db

# Notion exports
exports/
```

### Environment Variables

```bash
# .env.example
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_CREDENTIALS_PATH=config/gmail_credentials.json
GMAIL_TOKEN_PATH=config/gmail_token.json
NOTION_API_KEY=secret_...
NOTION_NEWSLETTER_DB=abc123...
NOTION_STORIES_DB=def456...
DATABASE_PATH=data/newsletter.db
```

### Credential Storage

Use environment variables or secure secrets management:
- Local: `.env` file (gitignored)
- CI/CD: GitHub Secrets / GitLab CI Variables
- Production: AWS Secrets Manager / Vault

---

## Migration from Experiments 🔄

### Step-by-step

1. **Preserve experiments:**
```bash
# Keep experiments for reference
git mv experiments experiments_archive
```

2. **Extract reusable code:**
```bash
# Copy test2_agentic.py → src/extractors/agentic.py
# Refactor into class-based design
# Add proper error handling
# Add progress callbacks
```

3. **Update config:**
```bash
# Update newsletters.yaml
# Change method: "structured" → method: "agentic"
```

4. **Test migration:**
```bash
# Run on same sample
python -m src.cli extract experiments_archive/samples/the_batch_2025-12-26.eml

# Compare with test2 results
diff <(cat experiments_archive/extraction-comparison/the_batch_2025-12-26_test2_result.json) \
     <(cat data/extractions/the_batch_2025-12-26.json)
```

---

## Cost Estimation 💰

### Per Newsletter

Using test2_agentic method:
- Average: ~68,000 tokens (~$0.20 per newsletter)
- The Batch frequency: ~3 per week
- Monthly cost: ~$2.40 for The Batch alone

### Scaling

With 5 newsletters, 3x/week each:
- 15 newsletters/week = 60/month
- 60 × $0.20 = **$12/month** in API costs

### Storage

- Gmail: Free (part of Google account)
- Notion: Free tier supports 1,000 blocks (upgrade at $10/user/month if needed)
- Local storage: Negligible (<1GB for years of data)

**Total estimated monthly cost: $12-22**

---

## Questions to Answer Before Implementation

1. **Gmail Access:**
   - Which Gmail account should we use?
   - Do you have admin access to create API credentials?

2. **Notion Setup:**
   - Do you have a Notion workspace?
   - Should databases be shared with a team?

3. **Hosting:**
   - Run locally on your machine?
   - Cloud VM (AWS/GCP/DigitalOcean)?
   - GitHub Actions (serverless)?

4. **Notifications:**
   - How should failures be reported? (Email, Slack, Discord)
   - Daily summary needed?

5. **Additional Newsletters:**
   - Which other newsletters beyond The Batch?
   - Any specific categories or senders to whitelist?

6. **Trend Analysis Priorities:**
   - What specific trends/topics are most important?
   - How far back should we analyze? (3 months, 6 months, 1 year?)

7. **Access Control:**
   - Who needs access to Notion database?
   - Should raw .eml files be preserved or deleted after processing?

---

## Recommended Implementation Order

**Week 1-2: Core Infrastructure**
- Phase 1: Project restructuring
- Phase 4: Pipeline integration (partial)

**Week 3: Integrations**
- Phase 2: Gmail API
- Phase 3: Notion API

**Week 4: Complete Pipeline**
- Phase 4: Full pipeline integration
- Testing and debugging

**Week 5: Automation**
- Phase 6: Scheduling
- Phase 7: Documentation

**Week 6+: Advanced Features**
- Phase 5: Trend analysis
- Optimization and refinement

---

## Success Metrics

- [ ] ✅ Pipeline runs automatically every 6 hours
- [ ] ✅ 95%+ success rate on extractions
- [ ] ✅ All newsletters appear in Notion within 1 hour of receipt
- [ ] ✅ Trend analysis identifies 5+ recurring topics
- [ ] ✅ Zero manual intervention needed for 30 days
- [ ] ✅ Cost stays under $25/month
- [ ] ✅ Complete documentation for handoff

---

## Next Steps

Ready to start implementation! Please answer the questions above, and I'll:

1. Create the initial project structure (Phase 1)
2. Set up Gmail API integration (Phase 2)
3. Set up Notion database (Phase 3)
4. Build the pipeline (Phase 4)

Which phase would you like to tackle first?
