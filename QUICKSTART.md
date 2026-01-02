# Quick Start Guide - Phase 1

## Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment:**
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. **Install the package (optional):**
```bash
pip install -e .
```

## Usage

### CLI Commands

**Check status:**
```bash
python -m src.cli status
```

**Extract insights from a newsletter:**
```bash
python -m src.cli extract experiments/samples/the_batch_2025-12-26.eml
```

**Extract multiple newsletters:**
```bash
python -m src.cli extract data/newsletters/*.eml --output-dir data/extractions
```

**View extraction results:**
```bash
python -m src.cli show data/extractions/the_batch_2025-12-26_extraction.json
```

### If you installed with setup.py:
```bash
newsletter status
newsletter extract <file.eml>
newsletter show <result.json>
```

## Testing the Extractor

**Quick test with the sample newsletter:**
```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run extraction on the sample
python -m src.cli extract experiments/samples/the_batch_2025-12-26.eml -v

# View the results
python -m src.cli show data/extractions/the_batch_2025-12-26_extraction.json
```

## Directory Structure

```
newsletters/
├── src/                      # Production code
│   ├── extractors/           # Agentic extractor (ready!)
│   ├── connectors/           # Gmail & Notion (Phase 2 & 3)
│   ├── storage/              # Database (Phase 4)
│   ├── analysis/             # Trends (Phase 5)
│   └── cli.py                # Command-line interface
├── data/                     # Local storage
│   ├── newsletters/          # Downloaded .eml files
│   └── extractions/          # Extracted JSON results
├── experiments/              # Testing & experiments
└── config/                   # Configuration files
```

## What Works Now (Phase 1)

✅ Agentic extraction using test2 method
✅ CLI tool for extraction
✅ JSON output with structured insights
✅ Progress tracking and logging

## Coming Next

- Phase 2: Gmail API integration
- Phase 3: Notion database integration
- Phase 4: Full pipeline automation
- Phase 5: Trend analysis

## Examples

**Extract and see verbose output:**
```bash
python -m src.cli extract experiments/samples/the_batch_2025-12-26.eml -v
```

**Batch process multiple newsletters:**
```bash
python -m src.cli extract experiments/samples/*.eml
```

## Troubleshooting

**"ANTHROPIC_API_KEY not found"**
- Make sure you've created a `.env` file with your API key
- Or export it: `export ANTHROPIC_API_KEY="sk-ant-..."`

**"No module named 'src'"**
- Run commands from the project root directory
- Or install with: `pip install -e .`

**Import errors**
- Install dependencies: `pip install -r requirements.txt`
