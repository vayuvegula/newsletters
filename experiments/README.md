# Experiments

This directory contains experiments to determine the best approach for newsletter extraction.

## Current Experiments

### extraction-comparison/

Compares three extraction methods:

| Test | Method | Description |
|------|--------|-------------|
| test1 | Structured | Direct Claude API with pre-parsed content |
| test2 | Agentic | Multi-turn reasoning approach |
| test3 | Deep | Follow links for deeper context |

See `extraction-comparison/README.md` for details.

## Samples

The `samples/` directory contains newsletter EML files for testing.

## Running Experiments

```bash
cd extraction-comparison
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"
python compare_all.py ../samples/the_batch_2025-12-26.eml
```
