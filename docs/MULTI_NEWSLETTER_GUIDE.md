# Managing Multiple Newsletters & Configurations

## Overview

The newsletter pipeline supports processing multiple newsletters with different extraction configurations and target databases. This allows you to:

- **Process multiple newsletters** from different sources
- **Use different extraction configs** per newsletter (executive, technical, custom)
- **Deploy to different Notion databases** based on analysis type
- **Enable/disable newsletters** without deleting configuration

## Quick Examples

### Example 1: Adding a New Newsletter (Same Config)

**Use case**: Add TLDR newsletter with same analysis as The Batch

```yaml
# config/newsletters.yaml
newsletters:
  - name: "The Batch"
    email: "thebatch@deeplearning.ai"
    enabled: true
    extraction_config: "default"
    database_set: "default"
    type: "analysis"
    priority: "high"

  - name: "TLDR AI"  # NEW!
    email: "dan@tldrnewsletter.com"
    enabled: true
    extraction_config: "default"  # Same analysis
    database_set: "default"        # Same databases
    type: "aggregator"
    priority: "medium"
    tags: ["AI", "brief"]
```

**Result**: Both newsletters use the same extraction config and go to the same Notion databases.

### Example 2: Different Analysis for Different Newsletters

**Use case**: Executive summaries for leadership, technical deep-dives for engineering

```yaml
# config/newsletters.yaml
newsletters:
  - name: "AI Executive Brief"
    email: "brief@company.com"
    enabled: true
    extraction_config: "executive"  # Short, strategic
    database_set: "executive"        # Leadership databases
    type: "summary"
    priority: "high"

  - name: "AI Research Weekly"
    email: "research@company.com"
    enabled: true
    extraction_config: "technical"  # Deep, detailed
    database_set: "technical"       # Research databases
    type: "research"
    priority: "medium"
```

**Setup required**:
1. Create extraction configs (already exists: `extraction_executive.yaml`, `extraction_technical.yaml`)
2. Create separate Notion database sets
3. Configure database IDs in `credentials.yaml`

### Example 3: Same Newsletter, Multiple Analyses

**Use case**: Process The Batch twice with different extraction styles

```yaml
# config/newsletters.yaml
newsletters:
  - name: "The Batch (Full Analysis)"
    email: "thebatch@deeplearning.ai"
    enabled: true
    extraction_config: "default"
    database_set: "default"
    type: "analysis"

  - name: "The Batch (Executive Brief)"
    email: "thebatch@deeplearning.ai"
    enabled: true
    extraction_config: "executive"
    database_set: "executive"
    type: "summary"
```

**Note**: The system will process the same email twice with different configs. Use the `enabled` flag to control which analysis runs.

## Configuration Files

### 1. newsletters.yaml - Newsletter Definitions

Location: `config/newsletters.yaml`

**Required fields:**
- `name`: Display name
- `email`: Sender email address

**Optional fields:**
- `enabled`: true/false (default: true)
- `extraction_config`: "default", "executive", "technical", or custom path (default: "default")
- `database_set`: Database set name from credentials.yaml (default: "default")
- `type`: Newsletter type for organization
- `priority`: "high", "medium", "low"
- `tags`: Array of tags for categorization

**Template:**
```yaml
newsletters:
  - name: "Newsletter Name"
    email: "sender@example.com"
    enabled: true
    extraction_config: "default"  # or "executive", "technical", "path/to/custom.yaml"
    database_set: "default"        # or "executive", "technical", custom name
    type: "analysis"
    priority: "high"
    tags: ["tag1", "tag2"]
```

### 2. credentials.yaml - Database Sets

Location: `config/credentials.yaml` (gitignored)

**New structure:**
```yaml
notion:
  api_key: "secret_..."

  database_sets:
    # Default set
    default:
      newsletters: "abc123..."
      stories: "def456..."
      trends: ""

    # Executive set (optional)
    executive:
      newsletters: "exec123..."
      stories: "exec456..."
      trends: ""

    # Technical set (optional)
    technical:
      newsletters: "tech123..."
      stories: "tech456..."
      trends: ""
      papers: "tech789..."  # Custom fields per set
```

**Key points:**
- Each database set is a named group of related databases
- Sets can have different database schemas
- Newsletters reference sets by name
- Legacy format (single `databases` key) still supported

### 3. Extraction Configs - Analysis Types

Location: `config/extraction_*.yaml`

**Built-in configs:**
- `extraction_config.yaml` - Default comprehensive analysis
- `extraction_executive.yaml` - Executive summaries (concise, strategic)
- `extraction_technical.yaml` - Technical deep-dives (detailed, research-focused)

**Custom configs:**
Create `config/extraction_custom.yaml` and reference it:
```yaml
# newsletters.yaml
extraction_config: "config/extraction_custom.yaml"
```

## Step-by-Step Guides

### Adding a New Newsletter (Same Config)

**Step 1**: Add to newsletters.yaml
```yaml
  - name: "New Newsletter"
    email: "news@example.com"
    enabled: true
    extraction_config: "default"
    database_set: "default"
    type: "analysis"
    priority: "medium"
```

**Step 2**: Run pipeline
```bash
newsletter run
```

**That's it!** The new newsletter uses existing extraction config and databases.

### Creating a New Analysis Type

**Use case**: Create "competitive-analysis" extraction config

**Step 1**: Create extraction config
```bash
cp config/extraction_config.yaml config/extraction_competitive.yaml
# Edit extraction_competitive.yaml with your custom analysis
```

**Step 2**: Add competitive intelligence focus
```yaml
# config/extraction_competitive.yaml
extraction:
  stories:
    required_fields:
      - competitor_mentioned
      - competitive_advantage
      - market_positioning
      - threat_level
```

**Step 3**: Reference in newsletters.yaml
```yaml
  - name: "Competitor Watch"
    email: "competitor@example.com"
    enabled: true
    extraction_config: "competitive"  # Auto-finds extraction_competitive.yaml
    database_set: "default"
    type: "competitive"
```

**Step 4**: Run
```bash
newsletter run
```

### Deploying to Different Databases

**Use case**: Executive newsletters go to leadership databases

**Step 1**: Create Notion databases for executives
- Go to Notion
- Create page "Executive Briefings"
- Share with integration
- Run setup script or create databases manually

**Step 2**: Add database set to credentials.yaml
```yaml
# config/credentials.yaml
notion:
  database_sets:
    executive:
      newsletters: "exec_newsletter_db_id"
      stories: "exec_stories_db_id"
```

**Step 3**: Configure newsletter to use executive set
```yaml
# config/newsletters.yaml
  - name: "Executive AI Brief"
    email: "brief@company.com"
    enabled: true
    extraction_config: "executive"
    database_set: "executive"  # Uses executive databases!
```

**Step 4**: Run
```bash
newsletter run
```

**Result**: Executive newsletter goes to separate databases with executive-focused analysis.

### Disabling a Newsletter Temporarily

Don't delete the configuration - just disable it:

```yaml
  - name: "Vacation Newsletter"
    email: "vacation@example.com"
    enabled: false  # Skip during processing
    extraction_config: "default"
    database_set: "default"
```

## Common Scenarios

### Scenario 1: Testing New Extraction Config

**Goal**: Test new extraction approach without affecting production

```yaml
# Create test database set
notion:
  database_sets:
    test:
      newsletters: "test_db_id"
      stories: "test_stories_id"

# Add test newsletter
newsletters:
  - name: "The Batch (Test)"
    email: "thebatch@deeplearning.ai"
    enabled: false  # Disabled by default
    extraction_config: "config/extraction_test.yaml"
    database_set: "test"
```

**Test**:
```bash
# Enable in yaml, then run
newsletter run -n 1
# Review results in test database
# Iterate on extraction_test.yaml
```

### Scenario 2: Different Newsletters, Different Teams

**Goal**: Engineering team gets technical analysis, leadership gets executive summaries

```yaml
newsletters:
  # Engineering newsletters → Technical databases
  - name: "ArXiv Weekly"
    email: "arxiv@example.com"
    enabled: true
    extraction_config: "technical"
    database_set: "engineering"

  - name: "Papers with Code"
    email: "pwc@example.com"
    enabled: true
    extraction_config: "technical"
    database_set: "engineering"

  # Leadership newsletters → Executive databases
  - name: "Industry Brief"
    email: "brief@example.com"
    enabled: true
    extraction_config: "executive"
    database_set: "leadership"

  - name: "Market Intelligence"
    email: "market@example.com"
    enabled: true
    extraction_config: "executive"
    database_set: "leadership"
```

**Result**:
- Engineering databases: Deep technical analysis with code, papers, benchmarks
- Leadership databases: Strategic summaries with business impact, action items

### Scenario 3: Progressive Rollout

**Goal**: Add newsletters gradually

```yaml
# Week 1: Start with one
newsletters:
  - name: "The Batch"
    email: "thebatch@deeplearning.ai"
    enabled: true

# Week 2: Add more
  - name: "TLDR AI"
    email: "dan@tldrnewsletter.com"
    enabled: true  # Enable when ready

  - name: "Import AI"
    email: "jack@example.com"
    enabled: false  # Not ready yet
```

## Best Practices

### 1. Start Simple

Begin with one newsletter and default config:
```yaml
newsletters:
  - name: "First Newsletter"
    email: "first@example.com"
    enabled: true
    extraction_config: "default"
    database_set: "default"
```

### 2. Test Before Production

Use `--dry-run` to preview:
```bash
newsletter run --dry-run -n 1
```

### 3. Use Meaningful Names

```yaml
# Good
- name: "The Batch - Full Analysis"
  database_set: "comprehensive"

# Not ideal
- name: "NL1"
  database_set: "db1"
```

### 4. Document Custom Configs

Add comments in custom extraction configs:
```yaml
# config/extraction_custom.yaml
# Purpose: Competitive intelligence extraction
# Owner: Strategy team
# Last updated: 2025-01-03
```

### 5. Use Tags for Organization

```yaml
tags: ["AI", "research", "weekly", "priority"]
```

Query later in database:
```sql
SELECT * FROM newsletters WHERE tags LIKE '%priority%';
```

## Troubleshooting

### "Database set 'X' not found"

**Solution**: Add database set to credentials.yaml:
```yaml
notion:
  database_sets:
    X:
      newsletters: "id123"
      stories: "id456"
```

### "Extraction config not found"

**Solution**: Check path:
```bash
ls config/extraction_*.yaml
# Make sure your config exists
```

Or use built-in:
```yaml
extraction_config: "executive"  # or "technical"
```

### "No enabled newsletters found"

**Solution**: Set `enabled: true` for at least one newsletter

### "Using legacy database format"

**Warning**: Update credentials.yaml structure:
```yaml
# Old (still works)
notion:
  databases:
    newsletters: "id"

# New (recommended)
notion:
  database_sets:
    default:
      newsletters: "id"
```

## Examples in Action

### Example: Research Lab Setup

```yaml
# config/newsletters.yaml
newsletters:
  # Daily research papers
  - name: "ArXiv CS.AI Daily"
    email: "arxiv@example.com"
    enabled: true
    extraction_config: "technical"
    database_set: "research"
    tags: ["papers", "daily"]

  # Weekly industry news for leadership
  - name: "AI Business Weekly"
    email: "business@example.com"
    enabled: true
    extraction_config: "executive"
    database_set: "executive"
    tags: ["business", "weekly"]

  # Engineering blog digests
  - name: "Engineering Blogs"
    email: "blogs@example.com"
    enabled: true
    extraction_config: "technical"
    database_set: "engineering"
    tags: ["blogs", "engineering"]
```

```yaml
# config/credentials.yaml
notion:
  database_sets:
    research:
      newsletters: "research_newsletters"
      stories: "research_papers"
      papers: "arxiv_papers"

    executive:
      newsletters: "exec_briefings"
      stories: "strategic_insights"

    engineering:
      newsletters: "eng_newsletters"
      stories: "technical_articles"
      code_samples: "code_database"
```

**Result**:
- Research team sees detailed paper analysis
- Executives see strategic summaries
- Engineering sees implementation-focused content

All from one `newsletter run` command!

## Next Steps

1. **Start with one newsletter**: Get comfortable with the system
2. **Add more newsletters**: Use same config initially
3. **Create custom configs**: As needs evolve
4. **Set up multiple database sets**: When teams have different needs
5. **Automate**: Schedule with cron/GitHub Actions (Phase 6)

## Summary

✅ **Add newsletters**: Just edit `newsletters.yaml`
✅ **Change analysis**: Use different `extraction_config`
✅ **Deploy to new databases**: Use different `database_set`
✅ **Enable/disable**: Use `enabled` flag
✅ **Organize**: Use `type`, `priority`, `tags`

The system is designed to be flexible - start simple and grow as needed!
