#!/usr/bin/env python3
"""
Compare Results from All Three Tests
=====================================
Runs all three tests and produces a comparison report.

Usage:
    export ANTHROPIC_API_KEY="your-key"
    python compare_all_tests.py newsletter.eml
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import test modules
from test1_structured import run_extraction as run_test1
from test2_agentic import run_agentic_extraction as run_test2
from test3_deep import run_deep_extraction as run_test3


def compare_results(results: dict) -> dict:
    """Compare results across all three tests."""
    
    comparison = {
        'test_date': datetime.now().isoformat(),
        'summary': {},
        'stories_comparison': [],
        'unique_insights': {},
        'cost_comparison': {},
        'recommendations': []
    }
    
    # Count stories per test
    for test_name, result in results.items():
        stories = result.get('stories', [])
        comparison['summary'][test_name] = {
            'stories_count': len(stories),
            'has_executive_summary': 'executive_summary' in result,
            'trend_signals': len(result.get('trend_signals', [])),
            'action_items': len(result.get('action_items', []))
        }
        
        # Token usage
        if '_metadata' in result:
            meta = result['_metadata']
            if 'total_tokens' in meta:
                comparison['cost_comparison'][test_name] = {
                    'total_tokens': meta['total_tokens'],
                    'estimated_cost_usd': meta['total_tokens'] * 0.000003  # rough Sonnet estimate
                }
            elif 'input_tokens' in meta and 'output_tokens' in meta:
                total = meta['input_tokens'] + meta['output_tokens']
                comparison['cost_comparison'][test_name] = {
                    'total_tokens': total,
                    'estimated_cost_usd': total * 0.000003
                }
    
    # Compare story extraction
    all_stories = {}
    for test_name, result in results.items():
        for story in result.get('stories', []):
            title = story.get('title', 'Unknown')
            if title not in all_stories:
                all_stories[title] = {'found_in': [], 'details': {}}
            all_stories[title]['found_in'].append(test_name)
            all_stories[title]['details'][test_name] = {
                'key_facts_count': len(story.get('key_facts', [])),
                'companies': story.get('companies_mentioned', story.get('companies', [])),
                'has_deeper_context': 'deeper_context' in story,
                'confidence': story.get('confidence', 'unknown')
            }
    
    comparison['stories_comparison'] = all_stories
    
    # Find unique insights per test
    for test_name, result in results.items():
        unique = []
        
        # Check for test-specific fields
        if test_name == 'test3' and 'competitive_landscape' in result:
            unique.append("Provides structured competitive landscape analysis")
        
        if test_name == 'test3' and '_fetched_articles' in result:
            count = len(result['_fetched_articles'])
            unique.append(f"Fetched {count} additional articles for context")
        
        if test_name == 'test2' and '_raw_reasoning' in result:
            unique.append("Includes Claude's reasoning process")
        
        comparison['unique_insights'][test_name] = unique
    
    # Generate recommendations
    if 'test3' in results and results['test3'].get('_metadata', {}).get('articles_fetched', 0) > 0:
        comparison['recommendations'].append(
            "Test 3 (Deep Links) provides the richest context by following links, "
            "but at higher cost and latency. Use for important newsletters."
        )
    
    comparison['recommendations'].append(
        "Test 1 (Structured API) is fastest and cheapest. Good for high-volume processing."
    )
    
    comparison['recommendations'].append(
        "Test 2 (Agentic) shows reasoning but similar depth to Test 1. "
        "Consider for debugging or understanding model decisions."
    )
    
    return comparison


def run_all_tests(eml_path: str) -> dict:
    """Run all three tests and return results."""
    
    results = {}
    
    print("\n" + "=" * 70)
    print("RUNNING TEST 1: Claude API Structured Extraction")
    print("=" * 70)
    try:
        results['test1'] = run_test1(eml_path)
        print("✓ Test 1 complete")
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
        results['test1'] = {'error': str(e)}
    
    print("\n" + "=" * 70)
    print("RUNNING TEST 2: Claude Code Agentic Extraction")
    print("=" * 70)
    try:
        results['test2'] = run_test2(eml_path)
        print("✓ Test 2 complete")
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
        results['test2'] = {'error': str(e)}
    
    print("\n" + "=" * 70)
    print("RUNNING TEST 3: Deep Link Following")
    print("=" * 70)
    try:
        results['test3'] = run_test3(eml_path, max_links=5, depth=2)
        print("✓ Test 3 complete")
    except Exception as e:
        print(f"✗ Test 3 failed: {e}")
        results['test3'] = {'error': str(e)}
    
    return results


def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_all_tests.py <newsletter.eml>")
        sys.exit(1)
    
    eml_path = sys.argv[1]
    
    if not Path(eml_path).exists():
        print(f"Error: File not found: {eml_path}")
        sys.exit(1)
    
    # Run all tests
    results = run_all_tests(eml_path)
    
    # Compare results
    comparison = compare_results(results)
    
    # Save everything
    output_base = Path(eml_path).stem
    
    with open(f"{output_base}_all_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(f"{output_base}_comparison.json", 'w') as f:
        json.dump(comparison, f, indent=2)
    
    # Print comparison summary
    print("\n" + "=" * 70)
    print("COMPARISON SUMMARY")
    print("=" * 70)
    
    print("\n📊 EXTRACTION COUNTS:")
    for test, summary in comparison['summary'].items():
        print(f"  {test}: {summary['stories_count']} stories, "
              f"{summary['trend_signals']} trends, "
              f"{summary['action_items']} action items")
    
    print("\n💰 COST COMPARISON:")
    for test, cost in comparison['cost_comparison'].items():
        print(f"  {test}: {cost['total_tokens']:,} tokens (~${cost['estimated_cost_usd']:.4f})")
    
    print("\n📖 STORY COVERAGE:")
    for story, data in comparison['stories_comparison'].items():
        found_in = ', '.join(data['found_in'])
        print(f"  • {story[:50]}... → Found in: {found_in}")
    
    print("\n🎯 RECOMMENDATIONS:")
    for rec in comparison['recommendations']:
        print(f"  → {rec}")
    
    print(f"\n📁 Results saved to:")
    print(f"   {output_base}_all_results.json")
    print(f"   {output_base}_comparison.json")


if __name__ == "__main__":
    main()
