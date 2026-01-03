# Phase 4: Full Pipeline Automation - Implementation Guide

## Overview

Phase 4 integrates all components into a fully automated newsletter processing pipeline with deduplication and state tracking.

## Key Features

### 1. **SQLite Database for State Tracking**
- Location: `src/storage/database.py`
- Tracks all newsletter processing states
- Prevents duplicate processing using Gmail message_id as unique key
- Maintains processing history and logs

**Tables:**
- `newsletters`: Main tracking table with status, timestamps, file paths
- `processing_log`: Audit trail of all processing events

**Key Methods:**
- `is_processed(message_id)`: Check if email already processed
- `get_last_processed_date(sender_email)`: Get last processed date for smart Gmail queries
- `mark_downloaded/extracted/uploaded/failed()`: Track processing stages
- `get_stats()`: View processing statistics

### 2. **Modular Extraction Configuration**
- Location: `config/extraction_config.yaml`
- **Purpose**: Easy iteration on extraction insights without code changes
- Configurable fields:
  - Executive summary settings
  - Story extraction parameters
  - Trend analysis configuration
  - Entity extraction (companies, technologies, people)
  - Google-specific analysis focus areas
  - Custom prompt templates
  - Model selection and fallbacks

**To iterate on insights:**
1. Edit `config/extraction_config.yaml`
2. Modify enabled fields, categories, or prompts
3. Run pipeline again - no code changes needed!

### 3. **Automated Pipeline**
- Location: `src/cli.py` - `run` command
- Full workflow orchestration: Gmail → Extract → Notion
- Automatic deduplication
- Error handling and retry logic
- Progress tracking and reporting

## Usage

### Running the Full Pipeline

```bash
# Process up to 10 new newsletters (default)
newsletter run

# Process up to 5 new newsletters
newsletter run -n 5

# Preview what would be processed (no changes)
newsletter run --dry-run

# Reprocess all emails (bypass deduplication)
newsletter run --force
```

### How Deduplication Works

1. **First run**: Processes all newsletters up to `max_emails` limit
2. **Subsequent runs**: Only processes emails received AFTER the last successfully processed email
3. **Database tracking**: Uses Gmail message_id as unique identifier
4. **Smart queries**: Automatically adds `after:YYYY/MM/DD` to Gmail queries

**Example:**
```
Run 1: Processes emails from 2024-12-01 to 2024-12-15
Run 2: Only searches for emails after 2024-12-15 (automatic!)
```

### Extraction Iteration Workflow

**Scenario**: You want to add a new field to extract (e.g., "author sentiment")

1. **Edit extraction config:**
   ```yaml
   # config/extraction_config.yaml
   stories:
     required_fields:
       - title
       - category
       - summary
       - author_sentiment  # NEW FIELD
   ```

2. **Update prompts if needed:**
   ```yaml
   prompts:
     analysis_task_prompt: |
       Analyze this newsletter and extract:
       ...
       - Author's sentiment toward each story (positive/negative/neutral)
   ```

3. **Reprocess with new config:**
   ```bash
   # Reprocess to extract new fields
   newsletter run --force
   ```

4. **No code changes required!**

## Setup Requirements

Before running the pipeline, ensure:

### 1. Gmail Setup
```bash
python3 scripts/setup_gmail.py
```
- Creates OAuth 2.0 authentication
- Saves token to `config/gmail_token.json`
- **Read-only mode** (no delete/modify permissions)

### 2. Notion Setup
```bash
python3 scripts/setup_notion.py
```
- Creates Newsletter and Stories databases
- Saves database IDs to `config/credentials.yaml`
- Requires a parent page in Notion

**Verify databases are configured:**
```bash
python3 scripts/check_notion_setup.py
```

### 3. Configuration Files

**config/credentials.yaml** (gitignored):
```yaml
anthropic:
  api_key: "sk-ant-..."

gmail:
  credentials_file: "config/gmail_credentials.json"
  token_file: "config/gmail_token.json"
  sender_email: "thebatch@deeplearning.ai"

notion:
  api_key: "secret_..."
  databases:
    newsletters: "abc123..."  # Fill via setup_notion.py
    stories: "def456..."       # Fill via setup_notion.py

database:
  path: "data/newsletter.db"
```

**config/newsletters.yaml** (committed):
```yaml
newsletters:
  - name: "The Batch"
    email: "thebatch@deeplearning.ai"
    type: "analysis"
    priority: "high"
    method: "agentic"
```

## Pipeline Workflow

```
1. Load Configuration
   ├─ credentials.yaml (API keys, database IDs)
   ├─ newsletters.yaml (newsletter whitelist)
   └─ extraction_config.yaml (insights to extract)

2. Initialize Components
   ├─ Database (SQLite for state tracking)
   ├─ GmailConnector (read-only access)
   ├─ NotionConnector (database access)
   └─ AgenticExtractor (Claude API)

3. For Each Newsletter in Whitelist:
   ├─ Get last processed date from database
   ├─ Query Gmail for new emails (after last processed date)
   ├─ For each email:
   │  ├─ Check if already processed (skip if yes)
   │  ├─ Download → mark downloaded
   │  ├─ Extract insights → mark extracted
   │  ├─ Upload to Notion → mark uploaded
   │  └─ Handle errors → mark failed
   └─ Continue to next newsletter

4. Summary Report
   ├─ Total processed/skipped/failed
   ├─ Database statistics
   └─ Token usage
```

## Database Schema

### newsletters table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| message_id | TEXT | Gmail message ID (UNIQUE) |
| sender_email | TEXT | Newsletter sender |
| subject | TEXT | Email subject |
| received_date | TIMESTAMP | When email was received |
| downloaded_at | TIMESTAMP | When downloaded |
| eml_path | TEXT | Path to .eml file |
| processed_at | TIMESTAMP | When insights extracted |
| extraction_path | TEXT | Path to JSON extraction |
| notion_page_id | TEXT | Notion page ID |
| status | TEXT | pending/completed/failed |
| error_message | TEXT | Error if failed |
| tokens_used | INTEGER | API tokens consumed |
| created_at | TIMESTAMP | Database entry created |
| updated_at | TIMESTAMP | Last updated |

### processing_log table
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| newsletter_id | INTEGER | Foreign key to newsletters |
| timestamp | TIMESTAMP | Event time |
| event | TEXT | Event type |
| details | TEXT | Event details |

## Monitoring & Debugging

### View Database Stats
```bash
# Through CLI
newsletter run  # Shows stats at end

# Direct database query
sqlite3 data/newsletter.db "SELECT status, COUNT(*) FROM newsletters GROUP BY status;"
```

### Check Processing History
```bash
sqlite3 data/newsletter.db "
SELECT subject, status, tokens_used, received_date
FROM newsletters
ORDER BY received_date DESC
LIMIT 10;
"
```

### View Failed Newsletters
```bash
sqlite3 data/newsletter.db "
SELECT subject, error_message, received_date
FROM newsletters
WHERE status = 'failed';
"
```

### Reprocess Failed Emails
```bash
# Force reprocess all
newsletter run --force

# Or manually delete from database and re-run
sqlite3 data/newsletter.db "DELETE FROM newsletters WHERE status = 'failed';"
newsletter run
```

## Error Handling

The pipeline handles errors at multiple levels:

1. **Initialization errors**: Exit with clear error message
2. **Per-newsletter errors**: Log and continue to next newsletter
3. **Per-email errors**: Mark as failed and continue to next email
4. **Database errors**: Logged and reported

All errors are:
- Logged to console
- Saved to processing_log table
- Stored in newsletters.error_message field

## Security & Privacy

- **Gmail**: Read-only access (no delete/modify/send)
- **Credentials**: All API keys gitignored
- **Database**: Local SQLite (no remote access)
- **Notion**: Only creates pages (no delete permissions)

## Cost Management

**Token Usage:**
- Tracked per newsletter in database
- Visible in summary report
- Average: ~66k tokens per newsletter (The Batch)

**View total cost:**
```bash
sqlite3 data/newsletter.db "SELECT SUM(tokens_used) FROM newsletters;"
```

**Anthropic pricing (as of 2024):**
- Claude Sonnet 4: Input $3/MTok, Output $15/MTok
- Estimated cost: ~$0.30 per newsletter

## Next Steps

### Phase 5: Trend Analysis
- Cross-newsletter topic clustering
- Track trend evolution over time
- Company/technology mention tracking
- Generate trend reports

### Phase 6: Automation
- Scheduled execution (cron/systemd/GitHub Actions)
- Run every 6 hours automatically
- Email notifications on failures
- Slack/Discord integration

### Phase 7: Testing & Documentation
- Unit tests for all components
- Integration tests for pipeline
- Complete user documentation
- Deployment guide

## Troubleshooting

### "Notion database IDs not configured"
```bash
# Run setup
python3 scripts/setup_notion.py

# Or check current setup
python3 scripts/check_notion_setup.py
```

### "Gmail token expired"
```bash
# Re-authenticate
rm config/gmail_token.json
python3 scripts/setup_gmail.py
```

### "No new emails found" (but emails exist)
```bash
# Check last processed date
sqlite3 data/newsletter.db "SELECT sender_email, MAX(received_date) FROM newsletters GROUP BY sender_email;"

# Force reprocess
newsletter run --force
```

### Database locked
```bash
# Close any open connections
# Or delete and recreate
rm data/newsletter.db
newsletter run  # Recreates database
```

## Files Added/Modified in Phase 4

**New files:**
- `src/storage/database.py` - SQLite database class
- `config/extraction_config.yaml` - Modular extraction configuration
- `scripts/check_notion_setup.py` - Notion setup verification
- `docs/PHASE4_IMPLEMENTATION.md` - This file

**Modified files:**
- `src/cli.py` - Implemented full `run` command with orchestration
- `src/storage/__init__.py` - Export Database class

**Database file:**
- `data/newsletter.db` - Created automatically on first run

## Testing

**Dry run (recommended first):**
```bash
newsletter run --dry-run -n 1
```

**Process one newsletter:**
```bash
newsletter run -n 1
```

**Full run:**
```bash
newsletter run
```

## Success Criteria

✅ Phase 4 is complete when:
- [ ] Pipeline processes new newsletters automatically
- [ ] Deduplication works (no duplicate processing)
- [ ] Database tracks all processing states
- [ ] Extraction config is modular and easy to iterate
- [ ] Error handling works correctly
- [ ] End-to-end test succeeds
- [ ] Documentation is complete

