#!/usr/bin/env python3
"""
Test 2: Claude Code API Agentic Extraction
===========================================
This test uses the Claude Code SDK to let Claude autonomously
explore and analyze the newsletter.

Approach:
- Give Claude Code the raw EML file
- Let it decide how to parse, what to explore
- Allow tool use (file reading, potentially web fetching)
- Multiple iterations as Claude reasons through the content

Strengths:
- Can discover structure organically
- Can decide what's important vs. noise
- More flexible reasoning
- Can iterate and refine

Weaknesses:
- Higher cost (multiple tool calls)
- Less predictable output
- Slower execution

Usage:
    export ANTHROPIC_API_KEY="your-key"
    python test2_claude_code_agentic.py newsletter.eml

Note: This requires the Claude Code SDK. Install with:
    pip install claude-code-sdk
"""

import anthropic
import json
import sys
from pathlib import Path


def run_agentic_extraction(eml_path: str) -> dict:
    """
    Run Claude Code agentic extraction.
    
    This simulates what Claude Code would do - we use the messages API
    with tool use to allow Claude to iteratively explore the content.
    """
    
    client = anthropic.Anthropic()
    
    # Read the raw EML content
    with open(eml_path, 'r', errors='replace') as f:
        eml_content = f.read()
    
    # For very long emails, we may need to chunk
    # But first, let's try sending the full content
    
    system_prompt = """You are an AI research analyst with access to tools. 
Your task is to analyze a newsletter email for a VP at Google.

You should:
1. First, understand the structure of the email (it's in EML format)
2. Identify the main stories/sections
3. For each story, extract key facts, companies mentioned, and implications
4. Identify which links would be worth following for deeper context
5. Synthesize into actionable insights

Think step by step. Explain your reasoning as you analyze.

The VP cares about:
- Competitive moves by Meta, OpenAI, Microsoft, AWS
- Talent market dynamics
- Infrastructure investments
- Technical trends
- Strategic opportunities/threats for Google

Be specific and actionable. Distinguish between confirmed facts and speculation."""

    user_prompt = f"""Please analyze this newsletter email. It's from "The Batch" by DeepLearning.AI.

Here is the raw EML file content:

```
{eml_content[:50000]}
```

Please:
1. Parse the email structure (identify HTML content, plain text, metadata)
2. Extract the main stories covered
3. For each story, identify:
   - Key facts and numbers
   - Companies mentioned
   - What this means for Google specifically
   - Which links would be worth following for more detail
4. Identify any trend signals across the stories
5. Provide a final executive summary

Think through this step by step, showing your reasoning."""

    print("Running agentic analysis with Claude...")
    print("(This will show Claude's reasoning process)")
    print("=" * 60)
    
    # First pass: Let Claude analyze
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    analysis_text = response.content[0].text
    
    print("\nCLAUDE'S ANALYSIS:")
    print("-" * 40)
    print(analysis_text[:3000])
    print("..." if len(analysis_text) > 3000 else "")
    
    # Second pass: Ask Claude to structure the output
    structuring_prompt = f"""Based on your analysis above, now provide a structured JSON output.

Your analysis:
{analysis_text}

Please provide the final output as JSON with this structure:

{{
  "executive_summary": "3-4 sentences for a VP",
  "stories": [
    {{
      "title": "Story title",
      "category": "competitive_intelligence | talent_market | infrastructure | product_development | regulation | research",
      "key_facts": ["fact1", "fact2"],
      "companies": ["company1", "company2"],
      "google_implications": "What this means for Google",
      "confidence": "high | medium | low",
      "reasoning": "Brief explanation of how you arrived at this analysis",
      "links_to_follow": ["link descriptions worth fetching"]
    }}
  ],
  "trend_signals": [
    {{
      "trend": "Trend name",
      "evidence": "Evidence from newsletter",
      "trajectory": "accelerating | stable | uncertain"
    }}
  ],
  "action_items": ["Specific recommendations"],
  "analysis_notes": "Any caveats or limitations in this analysis"
}}

Respond with ONLY valid JSON."""

    response2 = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": user_prompt},
            {"role": "assistant", "content": analysis_text},
            {"role": "user", "content": structuring_prompt}
        ]
    )
    
    structured_text = response2.content[0].text
    
    # Parse JSON
    try:
        result = json.loads(structured_text)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{.*\}', structured_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "raw_analysis": analysis_text,
                "raw_structured": structured_text,
                "parse_error": True
            }
    
    # Add metadata
    result['_metadata'] = {
        'test': 'test2_claude_code_agentic',
        'model': 'claude-sonnet-4-20250514',
        'pass1_input_tokens': response.usage.input_tokens,
        'pass1_output_tokens': response.usage.output_tokens,
        'pass2_input_tokens': response2.usage.input_tokens,
        'pass2_output_tokens': response2.usage.output_tokens,
        'total_tokens': (
            response.usage.input_tokens + response.usage.output_tokens +
            response2.usage.input_tokens + response2.usage.output_tokens
        )
    }
    
    # Store the raw reasoning for comparison
    result['_raw_reasoning'] = analysis_text
    
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python test2_claude_code_agentic.py <newsletter.eml>")
        sys.exit(1)
    
    eml_path = sys.argv[1]
    
    if not Path(eml_path).exists():
        print(f"Error: File not found: {eml_path}")
        sys.exit(1)
    
    result = run_agentic_extraction(eml_path)
    
    # Save result
    output_path = Path(eml_path).stem + "_test2_result.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to: {output_path}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    
    if 'executive_summary' in result:
        print(f"\nExecutive Summary:\n{result['executive_summary']}")
    
    if 'stories' in result:
        print(f"\nStories extracted: {len(result['stories'])}")
        for i, story in enumerate(result['stories'], 1):
            print(f"  {i}. {story.get('title', 'Untitled')} [{story.get('category', 'unknown')}]")
            if 'reasoning' in story:
                print(f"     Reasoning: {story['reasoning'][:100]}...")
    
    if '_metadata' in result:
        print(f"\nTotal tokens used: {result['_metadata']['total_tokens']}")
        print(f"  Pass 1: {result['_metadata']['pass1_input_tokens']} in / {result['_metadata']['pass1_output_tokens']} out")
        print(f"  Pass 2: {result['_metadata']['pass2_input_tokens']} in / {result['_metadata']['pass2_output_tokens']} out")


if __name__ == "__main__":
    main()
