#!/usr/bin/env python3
"""
Test 1: Claude API Structured Extraction
=========================================
This test uses a direct Claude API call with a well-structured prompt
to extract insights from the newsletter.

Approach:
- Pre-parse the EML file to extract clean text, images, and links
- Send structured context to Claude API
- Use a detailed JSON schema to guide extraction
- Single API call (no iteration)

Strengths:
- Predictable output structure
- Lower cost (single call)
- Fast execution

Weaknesses:
- Can't follow links
- Limited reasoning depth
- Relies on prompt engineering quality

Usage:
    export ANTHROPIC_API_KEY="your-key"
    python test1_claude_api_structured.py newsletter.eml
"""

import anthropic
import json
import sys
import email
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from pathlib import Path


def parse_eml(eml_path: str) -> dict:
    """Parse EML file and extract structured content."""
    with open(eml_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    
    # Get metadata
    metadata = {
        'source': msg['from'],
        'date': msg['date'],
        'subject': msg['subject']
    }
    
    # Extract HTML and plain text
    html_content = None
    plain_content = None
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            html_content = part.get_content()
        elif part.get_content_type() == 'text/plain':
            plain_content = part.get_content()
    
    soup = BeautifulSoup(html_content, 'html.parser') if html_content else None
    
    # Extract images with alt text
    images = []
    if soup:
        for img in soup.find_all('img'):
            alt = img.get('alt', '')
            width = img.get('width', '')
            src = img.get('src', '')
            if width != '1' and alt:
                filename = src.split('/')[-1].split('?')[0] if '/' in src else ''
                images.append({
                    'alt_text': alt,
                    'filename_hint': filename,
                    'url': src
                })
    
    # Extract links
    links = []
    if soup:
        for a in soup.find_all('a'):
            text = a.get_text(strip=True)
            href = a.get('href', '')
            if text and len(text) > 2:
                links.append({
                    'anchor_text': text,
                    'url': href,
                    'is_tracking': 'e3t/Ctc' in href or 'hubspot' in href.lower()
                })
    
    # Clean plain text
    if plain_content:
        clean_lines = []
        for line in plain_content.split('\n'):
            line = line.strip()
            if not line.startswith('http') and not line.startswith('(http'):
                if line:
                    clean_lines.append(line)
        clean_text = '\n'.join(clean_lines)
    else:
        clean_text = soup.get_text() if soup else ""
    
    return {
        'metadata': metadata,
        'images': images,
        'links': links,
        'text': clean_text
    }


def build_prompt(newsletter_data: dict) -> tuple[str, str]:
    """Build system and user prompts for Claude API."""
    
    system_prompt = """You are an AI analyst preparing a briefing for a VP at Google who has both technical and business responsibilities.

The VP cares about:
- Competitive intelligence (what are AWS, Microsoft, Meta, OpenAI, startups doing?)
- Emerging technology trends (what's gaining momentum?)
- Enterprise/B2B market signals
- Strategic opportunities or threats for Google
- Technical developments worth watching
- Talent market dynamics

Your analysis should be:
- Specific and actionable (not generic observations)
- Focused on "so what does this mean for Google?"
- Distinguished between noise and signal
- Honest about what's confirmed vs. rumored"""

    user_prompt = f"""Analyze this newsletter and extract strategic insights.

## NEWSLETTER METADATA
Source: {newsletter_data['metadata']['source']}
Date: {newsletter_data['metadata']['date']}
Subject: {newsletter_data['metadata']['subject']}

## IMAGES IN NEWSLETTER
(These are decorative illustrations, but filenames hint at topics)
{json.dumps(newsletter_data['images'][:10], indent=2)}

## KEY LINKS REFERENCED
{json.dumps([l for l in newsletter_data['links'] if len(l['anchor_text']) > 3][:30], indent=2)}

## FULL NEWSLETTER TEXT
{newsletter_data['text'][:30000]}

---

Please provide your analysis in the following JSON structure:

{{
  "executive_summary": "3-4 sentences summarizing what a VP needs to know from this issue",
  
  "stories": [
    {{
      "title": "Story headline",
      "category": "one of: competitive_intelligence | talent_market | infrastructure | product_development | regulation | research",
      "summary": "2-3 sentence summary",
      "key_facts": ["specific fact 1", "specific fact 2"],
      "companies_mentioned": ["company1", "company2"],
      "google_implications": "What this means specifically for Google",
      "confidence": "high | medium | low (based on source quality)",
      "links_to_follow": ["anchor text of links worth fetching for more detail"]
    }}
  ],
  
  "trend_signals": [
    {{
      "trend": "Name of emerging trend",
      "evidence": "What in this newsletter supports this",
      "trajectory": "accelerating | stable | uncertain"
    }}
  ],
  
  "action_items": [
    "Specific thing Google should monitor or consider"
  ],
  
  "links_worth_following": [
    {{
      "anchor_text": "text from the newsletter",
      "reason": "why this link would provide valuable additional context"
    }}
  ]
}}

Respond with ONLY the JSON, no additional text."""

    return system_prompt, user_prompt


def run_extraction(eml_path: str) -> dict:
    """Run the Claude API extraction."""
    
    # Parse newsletter
    print(f"Parsing {eml_path}...")
    newsletter_data = parse_eml(eml_path)
    print(f"  - Found {len(newsletter_data['images'])} images")
    print(f"  - Found {len(newsletter_data['links'])} links")
    print(f"  - Text length: {len(newsletter_data['text'])} chars")
    
    # Build prompts
    system_prompt, user_prompt = build_prompt(newsletter_data)
    
    # Call Claude API
    print("\nCalling Claude API (claude-sonnet-4-20250514)...")
    client = anthropic.Anthropic()
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    
    result_text = response.content[0].text
    
    # Parse JSON response
    try:
        result = json.loads(result_text)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {"raw_response": result_text, "parse_error": True}
    
    # Add metadata
    result['_metadata'] = {
        'test': 'test1_claude_api_structured',
        'model': 'claude-sonnet-4-20250514',
        'input_tokens': response.usage.input_tokens,
        'output_tokens': response.usage.output_tokens,
        'newsletter_source': newsletter_data['metadata']['source'],
        'newsletter_date': newsletter_data['metadata']['date']
    }
    
    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python test1_claude_api_structured.py <newsletter.eml>")
        sys.exit(1)
    
    eml_path = sys.argv[1]
    
    if not Path(eml_path).exists():
        print(f"Error: File not found: {eml_path}")
        sys.exit(1)
    
    result = run_extraction(eml_path)
    
    # Save result
    output_path = Path(eml_path).stem + "_test1_result.json"
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
    
    if '_metadata' in result:
        print(f"\nTokens used: {result['_metadata']['input_tokens']} in / {result['_metadata']['output_tokens']} out")


if __name__ == "__main__":
    main()
