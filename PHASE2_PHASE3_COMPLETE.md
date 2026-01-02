# Phase 2 & 3: Gmail + Notion Integration - ✅ COMPLETE

## What Was Built

### 🏗️ New Connectors

**1. Gmail Connector (`src/connectors/gmail.py`)**
- OAuth 2.0 authentication
- Search newsletters by sender email
- Download messages as .eml files
- Mark messages as processed with labels
- Automatic token refresh

**2. Notion Connector (`src/connectors/notion.py`)**
- Create Newsletter and Stories databases
- Upload extraction results to Notion
- Automatic page creation with rich formatting
- Update processing status

### 🛠️ Setup Scripts

**1. `scripts/setup_gmail.py`**
- One-time Gmail OAuth authentication
- Creates and saves access token
- Tests connection by counting newsletters

**2. `scripts/setup_notion.py`**
- Creates Notion databases with proper schema
- Automatically updates config with database IDs
- Tests connection before creating databases

### 📁 Files Created/Modified

- [x] src/connectors/gmail.py - Gmail API integration
- [x] src/connectors/notion.py - Notion API integration
- [x] src/connectors/__init__.py - Updated exports
- [x] scripts/setup_gmail.py - Gmail setup script
- [x] scripts/setup_notion.py - Notion setup script
- [x] config/credentials.yaml - Credentials stored (gitignored)
- [x] config/gmail_credentials.json - OAuth credentials (gitignored)
- [x] config/newsletters.yaml - Updated to use "agentic" method

## 🔒 Security Status

All sensitive files are **gitignored**:
- ✅ config/credentials.yaml (API keys)
- ✅ config/gmail_credentials.json (OAuth credentials)
- ✅ config/gmail_token.json (OAuth token - created after setup)

Only public configuration is committed:
- ✅ config/newsletters.yaml (whitelist only, no secrets)

## 📋 Setup Instructions

### Step 1: Run Gmail Setup

```bash
python scripts/setup_gmail.py
```

This will:
1. Check for Gmail credentials
2. Open browser for OAuth consent
3. Save access token to `config/gmail_token.json`
4. Test by counting newsletters from thebatch@deeplearning.ai

**What to expect:**
- Browser will open asking for permissions
- Grant access to Gmail (read and modify)
- Token is saved for future use
- No need to re-authenticate unless token expires

### Step 2: Run Notion Setup

```bash
python scripts/setup_notion.py
```

This will:
1. Test Notion API connection
2. Create "AI Newsletter Insights" database
3. Create "Newsletter Stories" database
4. Update `config/credentials.yaml` with database IDs

**After creation:**
- Go to Notion workspace
- Find the new databases
- Click "..." → "Add connections" → Select your integration
- This gives the integration permission to write to databases

## 🚀 What You Can Do Now

### Test Gmail Connection
```bash
python scripts/setup_gmail.py
```

### Test Notion Connection
```bash
python scripts/setup_notion.py
```

### Manual Pipeline (Phase 1 + 2 + 3 combined)

**1. Download newsletters from Gmail:**
```python
from src.connectors.gmail import GmailConnector
import yaml

# Load config
with open('config/credentials.yaml') as f:
    config = yaml.safe_load(f)

# Connect to Gmail
gmail = GmailConnector(
    credentials_path='config/gmail_credentials.json',
    token_path='config/gmail_token.json'
)
gmail.authenticate()

# Search for new newsletters
message_ids = gmail.search_newsletters(
    sender_email='thebatch@deeplearning.ai',
    max_results=5,
    unread_only=True
)

# Download each message
for msg_id in message_ids:
    gmail.download_message(msg_id, f"data/newsletters/{msg_id}.eml")
    gmail.mark_as_processed(msg_id)
```

**2. Extract insights (existing from Phase 1):**
```bash
python -m src.cli extract data/newsletters/*.eml
```

**3. Upload to Notion:**
```python
from src.connectors.notion import NotionConnector
import yaml
import json

# Load config
with open('config/credentials.yaml') as f:
    config = yaml.safe_load(f)

# Connect to Notion
notion = NotionConnector(
    api_key=config['notion']['api_key'],
    database_ids=config['notion']['databases']
)

# Upload extraction result
with open('data/extractions/result.json') as f:
    result = json.load(f)

newsletter_page_id = notion.create_newsletter_page(
    result,
    config['notion']['databases']['newsletters']
)

notion.create_story_pages(
    newsletter_page_id,
    result['stories'],
    config['notion']['databases']['stories']
)
```

## 📊 Database Schemas

### Newsletter Database

| Property | Type | Description |
|----------|------|-------------|
| Title | Title | Newsletter subject/summary |
| Source | Select | "The Batch", "TLDR", etc. |
| Date | Date | Newsletter date |
| Executive Summary | Text | 3-4 sentence summary |
| Stories Count | Number | # of stories extracted |
| Status | Select | Processing/Ready/Failed |
| Processed At | Date | Extraction timestamp |
| Token Cost | Number | API tokens used |
| Raw Data URL | URL | Link to JSON file |

### Stories Database

| Property | Type | Description |
|----------|------|-------------|
| Title | Title | Story headline |
| Category | Select | competitive_intelligence, talent_market, etc. |
| Companies | Multi-select | Meta, OpenAI, Google, etc. |
| Key Facts | Text | Bullet points |
| Google Implications | Text | Strategic implications |
| Confidence | Select | High, Medium, Low |
| Links | URL | Links worth following |

## 🔜 Next: Phase 4 - Full Pipeline Automation

Phase 4 will combine everything into a single command:
```bash
python -m src.cli run
```

This will:
1. Fetch new newsletters from Gmail ✓ (connector ready)
2. Extract insights ✓ (extractor ready)
3. Upload to Notion ✓ (connector ready)
4. Track state in SQLite database (to implement)
5. Handle errors and retries (to implement)

## 🧪 Testing

**Test Gmail:**
```bash
python scripts/setup_gmail.py
```

**Test Notion:**
```bash
python scripts/setup_notion.py
```

**Verify credentials:**
```bash
ls -la config/
# Should see:
# - credentials.yaml (gitignored)
# - gmail_credentials.json (gitignored)
# - newsletters.yaml (public config)
```

## 📝 Notes

- Gmail OAuth token lasts about 7 days, then auto-refreshes
- Notion API key doesn't expire unless manually revoked
- All credentials are stored locally, never committed to Git
- Setup scripts are idempotent - safe to run multiple times

## ✅ Phase 2 & 3 Status: COMPLETE

Ready for Phase 4 (Full Pipeline) implementation!
