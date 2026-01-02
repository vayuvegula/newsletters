# Newsletters

Analyze newsletters and extract strategic insights for executive briefings.

## Status: 🧪 Experimentation Phase

Currently testing different extraction approaches before building the full pipeline.

## Quick Start

```bash
# Clone
git clone https://github.com/yourusername/newsletters.git
cd newsletters

# Run extraction experiment
cd experiments/extraction-comparison
pip install -r requirements.txt
export ANTHROPIC_API_KEY="your-key"

# Test with sample newsletter
python compare_all.py ../samples/the_batch_2025-12-26.eml
```

## Project Structure

```
newsletters/
├── experiments/          # 🧪 Testing different approaches
│   ├── extraction-comparison/
│   └── samples/
├── src/                  # 🏭 Production code (TBD)
├── skills/               # 🎯 Claude Skills (TBD)
└── config/               # ⚙️ Configuration
```

## Roadmap

- [x] Phase 1: Experiment with extraction methods
- [ ] Phase 2: Build production pipeline
- [ ] Phase 3: Gmail + Notion integration
- [ ] Phase 4: Claude Skill packaging
