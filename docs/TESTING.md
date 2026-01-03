# Testing the Newsletter Pipeline

This guide will walk you through testing the complete newsletter pipeline from start to finish.

## Prerequisites

Before testing, ensure you have:
- ✅ Gmail credentials configured (`config/gmail_credentials.json`)
- ✅ Gmail OAuth token (`config/gmail_token.json`) - created by `setup_gmail.py`
- ✅ Anthropic API key in `config/credentials.yaml`
- ✅ Notion API key in `config/credentials.yaml`
- ✅ Notion databases created and IDs in `config/credentials.yaml`

## Quick Pre-Flight Check

Run this to verify your setup:

```bash
# Check credentials file exists
cat config/credentials.yaml

# Verify Notion databases are configured
python3 scripts/check_notion_setup.py

# Check Gmail token exists
ls -la config/gmail_token.json

# View your newsletter configuration
cat config/newsletters.yaml
```

## Test Scenarios

### Test 1: Dry Run (Safest - No Changes)

**What it does**: Shows what would happen without actually processing anything

```bash
newsletter run --dry-run -n 1
```

**Expected output**:
```
============================================================
NEWSLETTER PIPELINE
============================================================

⚠️  DRY RUN MODE - No changes will be made

🔧 Initializing components...
  ✓ Database connected
  ✓ Gmail connected
  ✓ Notion connected
  ✓ Extractor initialized

📬 Processing 1 enabled newsletter(s)...

────────────────────────────────────────────────────────────
📰 The Batch (thebatch@deeplearning.ai)
────────────────────────────────────────────────────────────
  📋 Using extraction config: extraction_config.yaml
  💾 Using database set: default
  🔍 Searching for new emails...
  📨 Found X email(s)

  [1/X] Processing abc123def456...
    🔍 Would process this email

============================================================
SUMMARY
============================================================
  ✅ Processed: 0
  ⏭️  Skipped:   0
  ❌ Failed:    0

✨ Pipeline complete!
```

**What to check**:
- ✅ All components initialize successfully
- ✅ Gmail connection works
- ✅ Notion connection works
- ✅ Database set is found
- ✅ Emails are discovered

**If errors occur**, see [Troubleshooting](#troubleshooting) below.

---

### Test 2: Process One Newsletter (Real Run)

**What it does**: Processes a single email from The Batch

```bash
newsletter run -n 1
```

**Expected timeline**:
1. **Initialize** (~2 seconds)
2. **Search Gmail** (~2 seconds)
3. **Download email** (~3 seconds)
4. **Extract insights** (~30-60 seconds) ← Longest step
5. **Upload to Notion** (~5 seconds)

**Expected output**:
```
============================================================
NEWSLETTER PIPELINE
============================================================

🔧 Initializing components...
  ✓ Database connected
  ✓ Gmail connected
  ✓ Notion connected
  ✓ Extractor initialized

📬 Processing 1 enabled newsletter(s)...

────────────────────────────────────────────────────────────
📰 The Batch (thebatch@deeplearning.ai)
────────────────────────────────────────────────────────────
  📋 Using extraction config: extraction_config.yaml
  💾 Using database set: default
  🔍 Searching for new emails...
  📨 Found 1 email(s)

  [1/1] Processing abc123def456...
    ⬇️  Downloading...
    🧠 Extracting insights...
      Pass 1: Analyzing newsletter content...
      Pass 2: Structuring insights...
    💾 Extracted (66,789 tokens)
    ⬆️  Uploading to Notion...
    ✅ Completed successfully

============================================================
SUMMARY
============================================================
  ✅ Processed: 1
  ⏭️  Skipped:   0
  ❌ Failed:    0

📊 Database Stats:
  Total newsletters: 1
  By status: {'completed': 1}
  Total tokens used: 66,789

✨ Pipeline complete!
```

**What to verify**:
1. **Check Notion databases**:
   - Open your Notion Newsletter database
   - Look for new entry with today's date
   - Verify stories are linked

2. **Check local files**:
   ```bash
   # View downloaded email
   ls data/newsletters/

   # View extraction JSON
   ls data/extractions/
   cat data/extractions/*_extraction.json | jq .
   ```

3. **Check database**:
   ```bash
   sqlite3 data/newsletter.db "SELECT subject, status, tokens_used FROM newsletters ORDER BY created_at DESC LIMIT 1;"
   ```

---

### Test 3: Deduplication (Run Twice)

**What it does**: Verifies that running again doesn't reprocess the same email

```bash
# First run
newsletter run -n 1

# Second run (should skip)
newsletter run -n 1
```

**Expected output (second run)**:
```
📰 The Batch (thebatch@deeplearning.ai)
  📋 Using extraction config: extraction_config.yaml
  💾 Using database set: default
  🔍 Searching for new emails...
  📨 Found 1 email(s)

  [1/1] Processing abc123def456...
    ⏭️  Already processed, skipping

SUMMARY
  ✅ Processed: 0
  ⏭️  Skipped:   1  ← Should be 1!
  ❌ Failed:    0
```

**What to verify**:
- ✅ Email is skipped (not reprocessed)
- ✅ "Already processed, skipping" message appears
- ✅ Skipped count increases

---

### Test 4: Force Reprocess

**What it does**: Reprocesses an email even if already in database (useful for testing config changes)

```bash
newsletter run -n 1 --force
```

**Expected**: Processes the email again, even though it was already done

**Use case**: You changed `extraction_config.yaml` and want to re-extract with new settings

---

### Test 5: Add a Second Newsletter (Multi-Newsletter Test)

**What it does**: Tests processing multiple newsletters

**Step 1**: Add a newsletter to `config/newsletters.yaml`

```yaml
newsletters:
  - name: "The Batch"
    email: "thebatch@deeplearning.ai"
    enabled: true
    extraction_config: "default"
    database_set: "default"
    type: "analysis"
    priority: "high"
    tags: ["AI", "ML", "industry-news"]

  # NEW NEWSLETTER!
  - name: "TLDR AI"
    email: "dan@tldrnewsletter.com"
    enabled: true
    extraction_config: "default"
    database_set: "default"
    type: "aggregator"
    priority: "medium"
    tags: ["AI", "brief"]
```

**Step 2**: Run pipeline

```bash
newsletter run -n 1
```

**Expected**: Processes 1 email from each newsletter (2 total)

**What to verify**:
- ✅ Both newsletters are processed
- ✅ Both appear in Notion databases
- ✅ Database tracks both separately

---

### Test 6: Different Extraction Configs (Advanced)

**What it does**: Tests using different extraction configs per newsletter

**Step 1**: Create executive-focused newsletter entry

```yaml
  - name: "The Batch (Executive)"
    email: "thebatch@deeplearning.ai"
    enabled: false  # Disable to avoid double-processing
    extraction_config: "executive"
    database_set: "default"  # Using same databases for now
    type: "summary"
    priority: "high"
```

**Step 2**: Enable it, disable the default one temporarily

```yaml
  - name: "The Batch"
    enabled: false  # Turn off

  - name: "The Batch (Executive)"
    enabled: true   # Turn on
```

**Step 3**: Run

```bash
newsletter run -n 1 --force
```

**Expected**:
- Uses `extraction_executive.yaml` config
- Shorter, more strategic summary
- Fewer stories (max 5 vs 10)
- Different fields extracted

**What to compare**:
```bash
# Compare extraction outputs
cat data/extractions/*_extraction.json | jq '.stories | length'
# Executive should have fewer stories

cat data/extractions/*_extraction.json | jq '.executive_summary'
# Executive should be shorter (~300 chars vs 500)
```

---

## Common Issues and Solutions

### Issue 1: "Database IDs not configured"

**Error**:
```
❌ Database IDs not configured for set 'default'
Run scripts/setup_notion.py or configure manually in credentials.yaml
```

**Solution**:
```bash
# Option 1: Run setup script
python3 scripts/setup_notion.py

# Option 2: Check and update manually
python3 scripts/check_notion_setup.py
```

---

### Issue 2: "Gmail token expired"

**Error**:
```
Failed to initialize components
...RefreshError...
```

**Solution**:
```bash
# Delete old token and re-authenticate
rm config/gmail_token.json
python3 scripts/setup_gmail.py
```

---

### Issue 3: "No new emails found" (but you know there are emails)

**Cause**: Database thinks emails are already processed

**Solution**:
```bash
# Check what's in database
sqlite3 data/newsletter.db "SELECT message_id, subject, status FROM newsletters WHERE sender_email='thebatch@deeplearning.ai' ORDER BY received_date DESC LIMIT 5;"

# Option 1: Force reprocess
newsletter run --force -n 1

# Option 2: Clear database (nuclear option)
rm data/newsletter.db
newsletter run -n 1
```

---

### Issue 4: "Extraction config not found"

**Error**:
```
⚠️  Extraction config not found: config/extraction_custom.yaml, using default extractor
```

**Solution**:
- Use built-in configs: `"default"`, `"executive"`, `"technical"`
- Or create the custom config file:
  ```bash
  cp config/extraction_config.yaml config/extraction_custom.yaml
  # Edit extraction_custom.yaml
  ```

---

### Issue 5: Extraction takes too long / times out

**Cause**: Large newsletter or slow API response

**Solution**:
- Wait it out (Claude API can take 30-60 seconds for large newsletters)
- Check extraction config token limits
- Use `extraction_executive.yaml` for faster processing (shorter responses)

---

## Understanding the Output Files

After a successful run, you'll have:

### 1. Downloaded Email (.eml file)

**Location**: `data/newsletters/`

```bash
ls -lh data/newsletters/
# -rw------- 1 root root 245K Jan  3 12:34 abc123def456.eml
```

**What it is**: Raw email file in RFC 822 format

**View it**:
```bash
head -50 data/newsletters/*.eml
```

---

### 2. Extraction JSON

**Location**: `data/extractions/`

```bash
ls -lh data/extractions/
# -rw------- 1 root root 45K Jan  3 12:35 abc123def456_extraction.json
```

**What it contains**:
- Executive summary
- Stories array (with all extracted fields)
- Trend signals
- Metadata (tokens used, model, etc.)

**View it**:
```bash
cat data/extractions/*_extraction.json | jq '.'

# Just the summary
cat data/extractions/*_extraction.json | jq '.executive_summary'

# Story count
cat data/extractions/*_extraction.json | jq '.stories | length'

# Token usage
cat data/extractions/*_extraction.json | jq '._metadata.total_tokens'
```

---

### 3. Database Records

**Location**: `data/newsletter.db`

```bash
# View all newsletters
sqlite3 data/newsletter.db "SELECT subject, status, tokens_used, received_date FROM newsletters ORDER BY received_date DESC;"

# View processing log
sqlite3 data/newsletter.db "SELECT timestamp, event, details FROM processing_log ORDER BY timestamp DESC LIMIT 10;"

# Statistics
sqlite3 data/newsletter.db "
SELECT
  COUNT(*) as total,
  SUM(tokens_used) as total_tokens,
  AVG(tokens_used) as avg_tokens,
  status
FROM newsletters
GROUP BY status;
"
```

---

### 4. Notion Pages

**Location**: Your Notion workspace

**Newsletter Database**:
- Title: Newsletter name + date
- Source: "The Batch"
- Date: When received
- Executive Summary: Extracted summary
- Stories Count: Number of stories
- Status: "Ready" (green)

**Stories Database**:
- One entry per story
- Linked to parent newsletter
- All extracted fields (title, category, summary, etc.)

**View in Notion**:
1. Go to your Notion workspace
2. Find the Newsletter database
3. Click to see full details
4. Check linked stories

---

## Performance Benchmarks

Based on "The Batch" newsletter:

| Metric | Value |
|--------|-------|
| **Email size** | ~200-300 KB |
| **Extraction time** | 30-60 seconds |
| **Tokens used** | ~66,000 (default config) |
| **Stories extracted** | 3-5 stories |
| **Cost per newsletter** | ~$0.30 USD |
| **Total pipeline time** | ~1-2 minutes |

**Executive config** (faster):
- Tokens: ~20,000
- Time: ~15-20 seconds
- Cost: ~$0.10 USD

**Technical config** (slower):
- Tokens: ~100,000+
- Time: ~60-90 seconds
- Cost: ~$0.50 USD

---

## Next Steps After Testing

Once you've verified everything works:

1. **Add more newsletters** to `config/newsletters.yaml`
2. **Customize extraction** in `config/extraction_config.yaml`
3. **Set up automation** (Phase 6 - coming soon):
   - Cron job to run every 6 hours
   - Or GitHub Actions workflow
4. **Monitor costs**:
   ```bash
   sqlite3 data/newsletter.db "SELECT SUM(tokens_used) FROM newsletters;"
   ```
5. **Iterate on insights** by modifying extraction configs

---

## Testing Checklist

Before considering the system fully tested:

- [ ] Dry run completes without errors
- [ ] Single newsletter processes successfully
- [ ] Results appear in Notion databases
- [ ] Local files created (eml, json, db)
- [ ] Deduplication works (second run skips processed emails)
- [ ] Force reprocess works (`--force` flag)
- [ ] Multiple newsletters can be added
- [ ] Different extraction configs can be used
- [ ] Database tracking is accurate
- [ ] Token usage is reasonable

---

## Getting Help

If you encounter issues:

1. **Check logs**: The CLI outputs detailed progress
2. **Check documentation**:
   - [Phase 4 Implementation Guide](PHASE4_IMPLEMENTATION.md)
   - [Multi-Newsletter Guide](MULTI_NEWSLETTER_GUIDE.md)
3. **Inspect database**:
   ```bash
   sqlite3 data/newsletter.db ".tables"
   sqlite3 data/newsletter.db ".schema newsletters"
   ```
4. **Verify configs**:
   ```bash
   cat config/credentials.yaml
   cat config/newsletters.yaml
   cat config/extraction_config.yaml
   ```

---

## Success!

If you've completed the testing successfully, you should have:

✅ A working end-to-end pipeline
✅ Emails automatically fetched from Gmail
✅ Insights extracted and stored in Notion
✅ Deduplication preventing reprocessing
✅ Multiple newsletters supported
✅ Flexible extraction configurations

**You're ready for production!** 🎉

Consider setting up automation (Phase 6) to run this automatically every few hours.
