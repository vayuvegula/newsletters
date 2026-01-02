#!/usr/bin/env python3
"""
Test 3: Deep Link Following with Claude Code
=============================================
This test goes beyond the newsletter content to follow links
and extract deeper context from referenced articles.

Approach:
1. Parse newsletter and extract all links
2. Resolve tracking redirects to get actual URLs
3. Use Claude to prioritize which links to follow
4. Fetch top N articles
5. Analyze articles with Claude (or Gemini for images)
6. Synthesize newsletter + articles into comprehensive briefing

Strengths:
- Gets the FULL context, not just summaries
- Can find primary sources (papers, filings, data)
- Discovers information not in the newsletter
- Much richer analysis

Weaknesses:
- Significantly more expensive
- Slower (network requests)
- May hit rate limits or paywalls
- More complex orchestration

Usage:
    export ANTHROPIC_API_KEY="your-key"
    export GEMINI_API_KEY="your-key"  # Optional, for image analysis
    python test3_deep_link_following.py newsletter.eml --depth 2 --max-links 10

Dependencies:
    pip install anthropic httpx beautifulsoup4 google-generativeai
"""

import anthropic
import json
import sys
import argparse
import email
from email import policy
from email.parser import BytesParser
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
import time

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    print("Warning: httpx not installed. Install with: pip install httpx")

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def parse_eml(eml_path: str) -> dict:
    """Parse EML file and extract content."""
    with open(eml_path, 'rb') as f:
        msg = BytesParser(policy=policy.default).parse(f)
    
    metadata = {
        'source': msg['from'],
        'date': msg['date'],
        'subject': msg['subject']
    }
    
    html_content = None
    plain_content = None
    for part in msg.walk():
        if part.get_content_type() == 'text/html':
            html_content = part.get_content()
        elif part.get_content_type() == 'text/plain':
            plain_content = part.get_content()
    
    soup = BeautifulSoup(html_content, 'html.parser') if html_content else None
    
    # Extract all links with full context
    links = []
    if soup:
        for a in soup.find_all('a'):
            text = a.get_text(strip=True)
            href = a.get('href', '')
            
            # Get surrounding context
            parent = a.parent
            context = parent.get_text(strip=True)[:300] if parent else ""
            
            if text and len(text) > 2 and href:
                links.append({
                    'anchor_text': text,
                    'url': href,
                    'context': context,
                    'is_tracking': 'e3t/Ctc' in href or 'hubspot' in href.lower()
                })
    
    # Extract images
    images = []
    if soup:
        for img in soup.find_all('img'):
            alt = img.get('alt', '')
            src = img.get('src', '')
            width = img.get('width', '')
            if width != '1' and alt:
                images.append({
                    'alt_text': alt,
                    'url': src
                })
    
    # Clean text
    if plain_content:
        clean_lines = [l.strip() for l in plain_content.split('\n') 
                       if l.strip() and not l.strip().startswith('http')]
        clean_text = '\n'.join(clean_lines)
    else:
        clean_text = soup.get_text() if soup else ""
    
    return {
        'metadata': metadata,
        'links': links,
        'images': images,
        'text': clean_text
    }


def resolve_tracking_url(url: str, timeout: int = 10) -> str:
    """Follow redirects to get the final URL."""
    if not HTTPX_AVAILABLE:
        return url
    
    try:
        # Don't actually fetch content, just follow redirects
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            response = client.head(url, follow_redirects=True)
            return str(response.url)
    except Exception as e:
        print(f"  Warning: Could not resolve {url[:50]}... ({e})")
        return url


def fetch_article(url: str, timeout: int = 30) -> dict:
    """Fetch and parse an article."""
    if not HTTPX_AVAILABLE:
        return {'error': 'httpx not available', 'url': url}
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            response = client.get(url, headers=headers)
            
            if response.status_code != 200:
                return {
                    'url': url,
                    'error': f'HTTP {response.status_code}',
                    'status': response.status_code
                }
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title = title.get_text(strip=True) if title else ""
            
            # Try to find main content (common patterns)
            article = (
                soup.find('article') or 
                soup.find('main') or 
                soup.find(class_='article-content') or
                soup.find(class_='post-content') or
                soup.find(class_='entry-content') or
                soup.body
            )
            
            if article:
                # Remove scripts, styles, nav
                for tag in article.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    tag.decompose()
                
                text = article.get_text(separator='\n', strip=True)
            else:
                text = soup.get_text(separator='\n', strip=True)
            
            # Extract images from article
            images = []
            for img in (article or soup).find_all('img'):
                src = img.get('src', '')
                alt = img.get('alt', '')
                if src and alt and 'logo' not in alt.lower():
                    images.append({'url': src, 'alt': alt})
            
            # Extract links from article
            links = []
            for a in (article or soup).find_all('a'):
                href = a.get('href', '')
                anchor = a.get_text(strip=True)
                if href and anchor and href.startswith('http'):
                    links.append({'url': href, 'text': anchor})
            
            return {
                'url': url,
                'title': title,
                'text': text[:15000],  # Limit size
                'images': images[:10],
                'links': links[:20],
                'text_length': len(text)
            }
            
    except Exception as e:
        return {
            'url': url,
            'error': str(e)
        }


def prioritize_links(newsletter_data: dict, client: anthropic.Anthropic) -> list:
    """Use Claude to prioritize which links to follow."""
    
    links_summary = []
    for link in newsletter_data['links']:
        if len(link['anchor_text']) > 3:
            links_summary.append({
                'anchor': link['anchor_text'],
                'context': link['context'][:200]
            })
    
    prompt = f"""You are helping analyze a newsletter for a VP at Google.

Newsletter subject: {newsletter_data['metadata']['subject']}

Here are the links found in the newsletter:
{json.dumps(links_summary[:50], indent=2)}

Based on the anchor text and context, identify the TOP 10 links that would provide 
the most valuable additional context for strategic analysis.

Prioritize:
1. Links to primary sources (research papers, company announcements, SEC filings)
2. Links about competitive intelligence (Meta, Microsoft, OpenAI, etc.)
3. Links with specific data or facts
4. Links about talent, infrastructure, or major strategic moves

Avoid:
- Generic "subscribe" or "view in browser" links
- Social media share links
- Links to previous issues (unless highly relevant)

Return a JSON array of the top 10 link anchor texts, in priority order:
["anchor text 1", "anchor text 2", ...]

Respond with ONLY the JSON array."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        priority_anchors = json.loads(response.content[0].text)
        return priority_anchors
    except:
        # Fallback: just take the first 10 substantive links
        return [l['anchor_text'] for l in newsletter_data['links'] 
                if len(l['anchor_text']) > 10][:10]


def analyze_with_gemini(image_url: str, context: str) -> dict:
    """Use Gemini to analyze an image (chart, graph, etc.)."""
    if not GEMINI_AVAILABLE:
        return {'error': 'Gemini not available'}
    
    import os
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        return {'error': 'GEMINI_API_KEY not set'}
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Download image
        with httpx.Client() as client:
            img_response = client.get(image_url)
            if img_response.status_code != 200:
                return {'error': f'Could not fetch image: HTTP {img_response.status_code}'}
        
        # Analyze with Gemini
        prompt = f"""Analyze this image from a tech industry article.
Context: {context}

If it's a chart or graph:
- Extract the key data points
- Identify trends
- Note what's significant

If it's a screenshot:
- Describe what it shows
- Note any notable UI or features

If it's a photo:
- Describe the subject
- Note relevance to the context

Be concise but precise."""

        response = model.generate_content([prompt, img_response.content])
        return {
            'image_url': image_url,
            'analysis': response.text
        }
        
    except Exception as e:
        return {'error': str(e)}


def run_deep_extraction(eml_path: str, max_links: int = 10, depth: int = 2) -> dict:
    """Run the full deep extraction pipeline."""
    
    client = anthropic.Anthropic()
    
    print(f"=== DEEP EXTRACTION (max_links={max_links}, depth={depth}) ===\n")
    
    # Step 1: Parse newsletter
    print("Step 1: Parsing newsletter...")
    newsletter_data = parse_eml(eml_path)
    print(f"  Found {len(newsletter_data['links'])} links")
    print(f"  Found {len(newsletter_data['images'])} images")
    
    # Step 2: Prioritize links
    print("\nStep 2: Prioritizing links with Claude...")
    priority_anchors = prioritize_links(newsletter_data, client)
    print(f"  Top {len(priority_anchors)} links to follow:")
    for i, anchor in enumerate(priority_anchors[:5], 1):
        print(f"    {i}. {anchor[:60]}...")
    
    # Step 3: Resolve tracking URLs and fetch articles
    print("\nStep 3: Resolving URLs and fetching articles...")
    fetched_articles = []
    
    for anchor in priority_anchors[:max_links]:
        # Find the link
        link = next((l for l in newsletter_data['links'] if l['anchor_text'] == anchor), None)
        if not link:
            continue
        
        print(f"\n  Fetching: {anchor[:50]}...")
        
        # Resolve tracking URL
        if link['is_tracking']:
            resolved_url = resolve_tracking_url(link['url'])
            print(f"    Resolved to: {resolved_url[:60]}...")
        else:
            resolved_url = link['url']
        
        # Fetch article
        article = fetch_article(resolved_url)
        
        if 'error' in article:
            print(f"    Error: {article['error']}")
        else:
            print(f"    Fetched: {article['title'][:50]}... ({article['text_length']} chars)")
            article['newsletter_anchor'] = anchor
            article['newsletter_context'] = link['context']
            fetched_articles.append(article)
        
        # Rate limiting
        time.sleep(1)
    
    print(f"\n  Successfully fetched {len(fetched_articles)} articles")
    
    # Step 4: Optional depth=2 - follow links in articles
    secondary_articles = []
    if depth >= 2 and fetched_articles:
        print("\nStep 4: Following secondary links (depth=2)...")
        
        # Collect all secondary links
        all_secondary = []
        for article in fetched_articles:
            for link in article.get('links', [])[:5]:
                all_secondary.append({
                    'url': link['url'],
                    'text': link['text'],
                    'source_article': article['title']
                })
        
        # Ask Claude which secondary links are worth following
        if all_secondary:
            secondary_prompt = f"""Given these links from articles about AI industry news,
which 5 would provide the most valuable primary source data?

Links:
{json.dumps(all_secondary[:30], indent=2)}

Prioritize: research papers (arxiv), official announcements, SEC filings, datasets.
Avoid: news aggregators, social media, generic company pages.

Return JSON array of URLs to fetch: ["url1", "url2", ...]"""

            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=512,
                messages=[{"role": "user", "content": secondary_prompt}]
            )
            
            try:
                secondary_urls = json.loads(response.content[0].text)
                
                for url in secondary_urls[:5]:
                    print(f"  Fetching secondary: {url[:50]}...")
                    article = fetch_article(url)
                    if 'error' not in article:
                        secondary_articles.append(article)
                    time.sleep(1)
                    
            except Exception as e:
                print(f"  Error parsing secondary links: {e}")
    
    # Step 5: Synthesize everything with Claude
    print("\nStep 5: Synthesizing with Claude...")
    
    # Build context from all fetched content
    articles_context = ""
    for article in fetched_articles:
        articles_context += f"""
--- ARTICLE: {article.get('title', 'Unknown')} ---
Source: {article.get('url', '')}
Newsletter reference: {article.get('newsletter_anchor', '')}

{article.get('text', '')[:5000]}

"""
    
    for article in secondary_articles:
        articles_context += f"""
--- SECONDARY SOURCE: {article.get('title', 'Unknown')} ---
Source: {article.get('url', '')}

{article.get('text', '')[:3000]}

"""
    
    synthesis_prompt = f"""You are preparing a comprehensive briefing for a VP at Google.

NEWSLETTER SUMMARY:
Subject: {newsletter_data['metadata']['subject']}
Date: {newsletter_data['metadata']['date']}

NEWSLETTER CONTENT:
{newsletter_data['text'][:10000]}

FETCHED ARTICLES (following links from the newsletter):
{articles_context[:30000]}

Based on the newsletter AND the additional context from fetched articles, provide a 
comprehensive analysis in JSON format:

{{
  "executive_summary": "4-5 sentences with the key takeaways for a Google VP",
  
  "stories": [
    {{
      "title": "Story headline",
      "category": "competitive_intelligence | talent_market | infrastructure | product_development | regulation | research",
      "summary": "3-4 sentence comprehensive summary",
      "key_facts": ["specific fact with source", "another fact"],
      "primary_sources": ["Source 1", "Source 2"],
      "companies_mentioned": ["company1", "company2"],
      "people_mentioned": ["Name - Role"],
      "numbers_and_data": ["$300M packages", "80% SWE-bench"],
      "google_implications": "Specific implications for Google",
      "confidence": "high | medium | low",
      "deeper_context": "What we learned from following the links"
    }}
  ],
  
  "trend_signals": [
    {{
      "trend": "Trend name",
      "evidence": "Evidence from newsletter AND articles",
      "trajectory": "accelerating | stable | uncertain",
      "google_relevance": "Why this matters to Google"
    }}
  ],
  
  "competitive_landscape": {{
    "meta": "What we learned about Meta's moves",
    "openai": "What we learned about OpenAI",
    "microsoft": "What we learned about Microsoft",
    "other": "Other notable competitors"
  }},
  
  "action_items": [
    {{
      "action": "Specific recommendation",
      "urgency": "high | medium | low",
      "rationale": "Why based on evidence"
    }}
  ],
  
  "gaps_and_limitations": "What we couldn't determine or verify"
}}

Respond with ONLY valid JSON."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=6000,
        messages=[{"role": "user", "content": synthesis_prompt}]
    )
    
    try:
        result = json.loads(response.content[0].text)
    except json.JSONDecodeError:
        import re
        json_match = re.search(r'\{.*\}', response.content[0].text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = {
                "raw_response": response.content[0].text,
                "parse_error": True
            }
    
    # Add metadata
    result['_metadata'] = {
        'test': 'test3_deep_link_following',
        'depth': depth,
        'max_links': max_links,
        'articles_fetched': len(fetched_articles),
        'secondary_articles_fetched': len(secondary_articles),
        'newsletter_source': newsletter_data['metadata']['source'],
        'newsletter_date': newsletter_data['metadata']['date']
    }
    
    result['_fetched_articles'] = [
        {'url': a.get('url'), 'title': a.get('title'), 'anchor': a.get('newsletter_anchor')}
        for a in fetched_articles
    ]
    
    return result


def main():
    parser = argparse.ArgumentParser(description='Deep newsletter analysis with link following')
    parser.add_argument('eml_path', help='Path to the EML file')
    parser.add_argument('--depth', type=int, default=2, help='Link following depth (1 or 2)')
    parser.add_argument('--max-links', type=int, default=10, help='Max links to follow')
    
    args = parser.parse_args()
    
    if not Path(args.eml_path).exists():
        print(f"Error: File not found: {args.eml_path}")
        sys.exit(1)
    
    result = run_deep_extraction(args.eml_path, max_links=args.max_links, depth=args.depth)
    
    # Save result
    output_path = Path(args.eml_path).stem + "_test3_result.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n{'=' * 60}")
    print(f"Results saved to: {output_path}")
    print('=' * 60)
    
    if 'executive_summary' in result:
        print(f"\nEXECUTIVE SUMMARY:\n{result['executive_summary']}")
    
    if 'stories' in result:
        print(f"\nSTORIES ({len(result['stories'])}):")
        for i, story in enumerate(result['stories'], 1):
            print(f"\n  {i}. {story.get('title', 'Untitled')}")
            print(f"     Category: {story.get('category', 'unknown')}")
            print(f"     Key facts: {len(story.get('key_facts', []))}")
            if story.get('deeper_context'):
                print(f"     Deeper context: {story['deeper_context'][:100]}...")
    
    if 'competitive_landscape' in result:
        print("\nCOMPETITIVE LANDSCAPE:")
        for company, intel in result['competitive_landscape'].items():
            if intel:
                print(f"  {company.upper()}: {intel[:100]}...")
    
    if '_metadata' in result:
        print(f"\nARTICLES FETCHED: {result['_metadata']['articles_fetched']}")
        print(f"SECONDARY SOURCES: {result['_metadata']['secondary_articles_fetched']}")


if __name__ == "__main__":
    main()
