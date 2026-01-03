# Extraction Templates Guide

## Overview

The newsletter pipeline uses **goal-specific extraction templates** to customize what insights are extracted and how they're framed. This makes the system scalable for different use cases without code changes.

## Built-In Templates

| Template | Purpose | Best For | Output Focus |
|----------|---------|----------|--------------|
| **default** | Comprehensive analysis | General newsletter processing | All fields, detailed insights |
| **executive** | Strategic summaries | Leadership briefings | Business impact, action items |
| **technical** | Deep technical analysis | Engineering/research teams | Code, papers, benchmarks, detailed specs |
| **vp_insights** | Decision-relevant signals | VP-level strategy sessions | Strategic implications, belief updates, risks |

## Template Anatomy

Every extraction template has 4 core components:

### 1. **Fields to Extract** (What)
```yaml
stories:
  required_fields:
    - title
    - your_custom_field
    - another_field
```

### 2. **Taxonomies** (How to categorize)
```yaml
  insight_types:
    - "Type 1"
    - "Type 2"

  time_horizons:
    - "Now"
    - "Later"
```

### 3. **Prompts** (How to extract)
```yaml
prompts:
  analysis_system_prompt: |
    You are a [role] preparing [output] for [audience].
    Focus on [key principles].

  analysis_task_prompt: |
    Extract [specific things] using [framework].
```

### 4. **Model Settings** (Quality/cost trade-offs)
```yaml
model:
  name: "claude-sonnet-4-20250514"
  max_tokens: 16000  # Longer for detailed analysis
  temperature: 0.0   # Deterministic
```

---

## Creating a New Template

### Step 1: Define Your Goal

Ask:
- **Who is this for?** (CEO, PM, Researcher, Investor, etc.)
- **What decision are they making?** (Invest, Build, Acquire, etc.)
- **What format do they need?** (Brief, Detailed, Structured, etc.)

### Step 2: Choose a Base Template

Start with the closest match:
- **vp_insights** → For strategic/decision-focused
- **technical** → For research/implementation details
- **executive** → For high-level business impact
- **default** → For comprehensive coverage

### Step 3: Customize Fields

Identify what's unique about your goal:

**Example: Competitive Intelligence Template**
```yaml
required_fields:
  - title
  - competitor_mentioned  # NEW
  - competitive_move_type  # Product/Pricing/Partnership/Acquisition
  - threat_level  # Critical/High/Medium/Low
  - our_response_options  # What can we do?
  - time_to_respond  # How long do we have?
```

### Step 4: Write Goal-Specific Prompts

**Bad prompt (generic):**
```
Extract key insights from this newsletter.
```

**Good prompt (goal-specific):**
```
You are a competitive intelligence analyst tracking competitor moves.

For each story, identify:
1. Which competitor is making a move?
2. What type of move? (Product/Pricing/Partnership/Acquisition)
3. Threat level to our position?
4. Our response options? (Ignore/Monitor/Match/Leapfrog)
5. How long do we have to respond?

Focus on ACTIONABLE COMPETITIVE SIGNALS, not general industry news.
```

---

## Template Examples

### Example 1: Investment Thesis Template

**Goal**: Identify market opportunities for VC/corporate venture arm

**File**: `config/extraction_investment.yaml`

```yaml
extraction:
  stories:
    required_fields:
      - title
      - market_opportunity  # What market is emerging?
      - market_size_signal  # TAM indicators
      - technology_maturity  # Hype/Early/Scaling/Mature
      - defensibility  # What makes this sustainable?
      - timing_indicator  # Why now?
      - key_players  # Who's leading?
      - investment_thesis  # Why invest here?
      - risk_factors  # What could go wrong?

prompts:
  analysis_task_prompt: |
    You are an investment analyst identifying emerging market opportunities.

    For each story, extract:
    1. MARKET OPPORTUNITY: What new market/category is forming?
    2. SIZE SIGNALS: What indicates this could be big? (adoption, growth, funding)
    3. TECHNOLOGY MATURITY: Is this ready? (Hype/Early/Scaling/Mature)
    4. DEFENSIBILITY: What makes this sustainable vs a fad?
    5. TIMING: Why is now the right time? (enabling tech, regulatory, behavior change)
    6. KEY PLAYERS: Who's winning? Who to watch?
    7. INVESTMENT THESIS: Complete "We should invest because..."
    8. RISKS: What could kill this thesis?
```

---

### Example 2: Product Roadmap Template

**Goal**: Extract signals for product planning

**File**: `config/extraction_product_signals.yaml`

```yaml
extraction:
  stories:
    required_fields:
      - title
      - user_need_signal  # What do users want?
      - technology_enabler  # What new tech makes this possible?
      - adoption_barrier  # Why isn't this mainstream yet?
      - product_opportunity  # What should we build?
      - feature_priority  # Must-have/Nice-to-have/Future
      - competitive_pressure  # Who's building this?
      - time_to_market  # How urgent?

prompts:
  analysis_task_prompt: |
    You are a product strategist extracting signals for roadmap planning.

    For each story, identify:
    1. USER NEED: What problem is being solved? (cite evidence)
    2. ENABLER: What technology/change makes this possible now?
    3. BARRIER: Why isn't everyone doing this yet?
    4. OPPORTUNITY: What product/feature should we consider?
    5. PRIORITY: Must-have (competitive) vs Nice-to-have (differentiation) vs Future
    6. COMPETITIVE PRESSURE: Who else is building this?
    7. TIME TO MARKET: How quickly should we move?
```

---

### Example 3: Hiring/Talent Template

**Goal**: Identify talent needs and skill gaps

**File**: `config/extraction_talent_signals.yaml`

```yaml
extraction:
  stories:
    required_fields:
      - title
      - emerging_skill  # What skill is becoming important?
      - skill_scarcity  # Hard to hire/Easy to hire/Can train
      - role_evolution  # How are job descriptions changing?
      - team_structure_implication  # How should we organize?
      - hire_vs_train_decision  # Should we hire externally or upskill?
      - talent_market_signal  # Where are great people going?

prompts:
  analysis_task_prompt: |
    You are a talent strategist identifying skill requirements and market signals.

    For each story, extract:
    1. EMERGING SKILL: What new capability is becoming critical?
    2. SCARCITY: Can we hire for this or must we train?
    3. ROLE EVOLUTION: How are job descriptions changing?
    4. TEAM STRUCTURE: How should we organize teams differently?
    5. HIRE VS TRAIN: Should we hire externally or upskill existing team?
    6. MARKET SIGNAL: Where are top practitioners going? (companies, roles, geographies)
```

---

## Template Naming Convention

Use descriptive names that indicate the goal:

**Good names:**
- `extraction_vp_insights.yaml` - Decision signals for VPs
- `extraction_competitive_intel.yaml` - Competitor tracking
- `extraction_investment_thesis.yaml` - Market opportunities
- `extraction_product_signals.yaml` - Product roadmap inputs
- `extraction_talent_signals.yaml` - Hiring/skill planning

**Bad names:**
- `extraction_v2.yaml` - What's v2?
- `extraction_new.yaml` - What's new about it?
- `extraction_test.yaml` - Is this production-ready?

---

## Using Templates

### In newsletters.yaml

```yaml
newsletters:
  # Same newsletter, different goals
  - name: "The Batch (VP Insights)"
    email: "thebatch@deeplearning.ai"
    enabled: true
    extraction_config: "vp_insights"  # Decision signals
    database_set: "default"

  - name: "The Batch (Competitive Intel)"
    email: "thebatch@deeplearning.ai"
    enabled: false  # Run separately
    extraction_config: "competitive_intel"  # Competitor tracking
    database_set: "competitive"

  - name: "TechCrunch (Investment Signals)"
    email: "newsletter@techcrunch.com"
    enabled: true
    extraction_config: "investment_thesis"  # Market opportunities
    database_set: "investment"
```

---

## Template Design Patterns

### Pattern 1: Role-Based Templates

**Principle**: Different roles need different insights

**Examples**:
- `extraction_ceo.yaml` - Strategic, financial, competitive
- `extraction_cto.yaml` - Technical architecture, team, risk
- `extraction_cpo.yaml` - User needs, features, roadmap
- `extraction_vp_eng.yaml` - Hiring, process, tooling

### Pattern 2: Decision-Based Templates

**Principle**: Optimize for specific decisions

**Examples**:
- `extraction_build_vs_buy.yaml` - Technology evaluation
- `extraction_hire_vs_train.yaml` - Talent decisions
- `extraction_invest_vs_wait.yaml` - Investment timing
- `extraction_partner_vs_build.yaml` - Partnership opportunities

### Pattern 3: Time-Horizon Templates

**Principle**: Different urgency levels

**Examples**:
- `extraction_immediate_threats.yaml` - 0-3 months
- `extraction_quarterly_planning.yaml` - 3-12 months
- `extraction_strategic_positioning.yaml` - 12-24 months
- `extraction_long_term_bets.yaml` - 24+ months

---

## Best Practices

### 1. **Be Specific in Prompts**

❌ Bad:
```
Extract insights from this newsletter.
```

✅ Good:
```
You are a [specific role] preparing [specific output] for [specific audience].

For each story, extract [exactly what] by asking [specific questions].

Format as [specific structure].
```

### 2. **Design for Decisions**

Every field should help answer:
- What should we do?
- What should we stop doing?
- What should we reconsider?

### 3. **Test with Real Content**

Run your template on 2-3 real newsletters and check:
- Are the extracted fields useful?
- Is anything missing?
- Is anything redundant?

### 4. **Iterate Based on Usage**

Track which fields get used/ignored:
```sql
-- In future: which fields are actually used in Notion?
SELECT field_name, COUNT(*)
FROM field_usage
GROUP BY field_name
ORDER BY COUNT(*) DESC;
```

### 5. **Document the "Why"**

At the top of each template:
```yaml
# Investment Thesis Template
# Purpose: Identify market opportunities for venture investments
# Audience: Investment committee, corporate venture team
# Output: Investment memos with thesis + risks
# Designed: 2026-01-03
# Maintained by: [Your team]
```

---

## Template Lifecycle

### 1. Create
- Copy closest template
- Customize fields and prompts
- Test on 1-2 newsletters

### 2. Validate
- Run on 5-10 newsletters
- Review output quality
- Adjust prompts based on results

### 3. Production
- Enable in newsletters.yaml
- Monitor extraction quality
- Collect user feedback

### 4. Iterate
- Quarterly review of field usage
- Remove unused fields
- Add requested fields
- Refine prompts

### 5. Archive
- When no longer needed
- Move to `config/archive/`
- Document why archived

---

## Troubleshooting Templates

### Problem: Extractions are too generic

**Solution**: Make prompts more specific

Before:
```
Extract key insights.
```

After:
```
For each story, answer:
1. What should we do differently because of this?
2. What assumption does this challenge?
3. What's the 2nd-order effect if everyone does this?
```

### Problem: Missing important information

**Solution**: Add to required_fields and prompts

```yaml
required_fields:
  - your_missing_field

prompts:
  analysis_task_prompt: |
    Also extract: [description of missing field]
```

### Problem: Too much information

**Solution**: Reduce max_stories or make fields optional

```yaml
stories:
  max_stories: 3  # Quality over quantity

  optional_fields:
    - verbose_field  # Only extract if clearly present
```

---

## Quick Start: Create Your First Template

1. **Copy a base template:**
```bash
cp config/extraction_vp_insights.yaml config/extraction_mygoal.yaml
```

2. **Edit the header:**
```yaml
# My Goal Template
# Purpose: [What is this for?]
# Audience: [Who will use this?]
```

3. **Customize fields:**
```yaml
required_fields:
  - title
  - my_custom_field
  - another_field
```

4. **Update prompts:**
```yaml
prompts:
  analysis_task_prompt: |
    You are a [role] extracting [what] for [purpose].

    For each story, identify:
    1. [Question 1]
    2. [Question 2]
    3. [Question 3]
```

5. **Test:**
```bash
# Update newsletters.yaml to use your template
nano config/newsletters.yaml

# Run test
newsletter run -n 1 --force
```

6. **Iterate based on results!**

---

## Next Steps

- Create your first custom template
- Test on real newsletters
- Share successful templates with your team
- Build a template library for different goals

**Remember**: The goal is not to extract everything—it's to extract exactly what helps you make better decisions.
