# Extraction Method Comparison

Compare three different approaches to extracting insights from newsletters.

## Methods

### Test 1: Structured (Claude API)

**File:** `test1_structured.py`

- Pre-parses EML file to extract clean text, images, links
- Sends structured prompt to Claude API
- Single API call, predictable output

**Best for:** High-volume processing, simple newsletters

```bash
python test1_structured.py ../samples/the_batch_2025-12-26.eml
```

### Test 2: Agentic (Multi-turn)

**File:** `test2_agentic.py`

- Two-pass approach: analyze first, then structure
- Shows Claude's reasoning process
- Good for debugging and understanding

**Best for:** Debugging, understanding extraction decisions

```bash
python test2_agentic.py ../samples/the_batch_2025-12-26.eml
```

### Test 3: Deep (Link Following)

**File:** `test3_deep.py`

- Resolves tracking redirects (HubSpot, etc.)
- Fetches linked articles for deeper context
- Can follow links within articles (depth=2)
- Synthesizes newsletter + articles

**Best for:** Important newsletters, link-heavy content

```bash
python test3_deep.py ../samples/the_batch_2025-12-26.eml --max-links 10 --depth 2
```

## Running All Tests

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key"

# Run comparison
python compare_all.py ../samples/the_batch_2025-12-26.eml
```

This produces:
- `<newsletter>_test1_result.json`
- `<newsletter>_test2_result.json`
- `<newsletter>_test3_result.json`
- `<newsletter>_comparison.json`

## Expected Output

All tests produce JSON with this structure:

```json
{
  "executive_summary": "3-4 sentences for a VP",
  "stories": [
    {
      "title": "Story headline",
      "category": "competitive_intelligence | talent_market | ...",
      "key_facts": ["fact 1", "fact 2"],
      "companies_mentioned": ["Meta", "OpenAI"],
      "google_implications": "What this means for Google"
    }
  ],
  "trend_signals": [...],
  "action_items": [...]
}
```

## Cost Estimates

| Test | Tokens | Est. Cost |
|------|--------|-----------|
| Test 1 | ~10-15K | ~$0.03-0.05 |
| Test 2 | ~20-30K | ~$0.06-0.10 |
| Test 3 | ~50-100K | ~$0.15-0.30 |

## Results

Store results in `results/` directory:
- Not committed to git (in .gitignore)
- Compare across runs
