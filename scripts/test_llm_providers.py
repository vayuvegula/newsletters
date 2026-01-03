#!/usr/bin/env python3
"""
Test script to verify access to different LLM providers.

This script tests:
- Anthropic Claude API
- OpenAI GPT API
- Google Gemini API

Run with API keys from environment or provide them when prompted.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_anthropic():
    """Test Anthropic Claude API."""
    print("\n" + "=" * 60)
    print("Testing Anthropic Claude API")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        api_key = input("Enter Anthropic API key (or press Enter to skip): ").strip()
        if not api_key:
            print("⏭️  Skipping Anthropic test")
            return None

    try:
        import anthropic
        print("✓ anthropic library imported")
    except ImportError:
        print("❌ anthropic library not installed")
        print("   Install with: pip install anthropic")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        print("✓ Client initialized")

        # Test simple completion
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Say 'Hello from Claude!' and nothing else."
            }]
        )

        content = response.content[0].text
        print(f"✓ API call successful")
        print(f"  Response: {content[:100]}")
        print(f"  Model: {response.model}")
        print(f"  Input tokens: {response.usage.input_tokens}")
        print(f"  Output tokens: {response.usage.output_tokens}")

        return {
            "provider": "anthropic",
            "success": True,
            "model": response.model,
            "response": content
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "provider": "anthropic",
            "success": False,
            "error": str(e)
        }


def test_openai():
    """Test OpenAI GPT API."""
    print("\n" + "=" * 60)
    print("Testing OpenAI GPT API")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = input("Enter OpenAI API key (or press Enter to skip): ").strip()
        if not api_key:
            print("⏭️  Skipping OpenAI test")
            return None

    try:
        import openai
        print("✓ openai library imported")
    except ImportError:
        print("❌ openai library not installed")
        print("   Install with: pip install openai")
        return None

    try:
        client = openai.OpenAI(api_key=api_key)
        print("✓ Client initialized")

        # Test simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use mini for cheaper testing
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Say 'Hello from GPT!' and nothing else."
            }]
        )

        content = response.choices[0].message.content
        print(f"✓ API call successful")
        print(f"  Response: {content[:100]}")
        print(f"  Model: {response.model}")
        print(f"  Input tokens: {response.usage.prompt_tokens}")
        print(f"  Output tokens: {response.usage.completion_tokens}")

        return {
            "provider": "openai",
            "success": True,
            "model": response.model,
            "response": content
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "provider": "openai",
            "success": False,
            "error": str(e)
        }


def test_gemini():
    """Test Google Gemini API."""
    print("\n" + "=" * 60)
    print("Testing Google Gemini API")
    print("=" * 60)

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        api_key = input("Enter Google/Gemini API key (or press Enter to skip): ").strip()
        if not api_key:
            print("⏭️  Skipping Gemini test")
            return None

    try:
        import google.generativeai as genai
        print("✓ google-generativeai library imported")
    except ImportError:
        print("❌ google-generativeai library not installed")
        print("   Install with: pip install google-generativeai")
        return None

    try:
        genai.configure(api_key=api_key)
        print("✓ API key configured")

        # Test simple completion
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        print("✓ Model initialized")

        response = model.generate_content(
            "Say 'Hello from Gemini!' and nothing else.",
            generation_config=genai.GenerationConfig(
                max_output_tokens=100,
            )
        )

        content = response.text
        print(f"✓ API call successful")
        print(f"  Response: {content[:100]}")
        print(f"  Model: gemini-2.0-flash-exp")
        print(f"  Input tokens: {response.usage_metadata.prompt_token_count}")
        print(f"  Output tokens: {response.usage_metadata.candidates_token_count}")

        return {
            "provider": "gemini",
            "success": True,
            "model": "gemini-2.0-flash-exp",
            "response": content
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            "provider": "gemini",
            "success": False,
            "error": str(e)
        }


def test_structured_json_extraction():
    """Test structured JSON extraction with each provider."""
    print("\n" + "=" * 60)
    print("Testing Structured JSON Extraction (Critical for Newsletter)")
    print("=" * 60)

    test_prompt = """Extract insights from this text and return ONLY valid JSON:

Text: "OpenAI released GPT-5 with 10 trillion parameters. Microsoft invested $5B."

Return JSON with this structure:
{
  "stories": [
    {
      "title": "Story title",
      "key_fact": "Main fact",
      "company": "Company name"
    }
  ]
}

Respond with ONLY valid JSON. No markdown, no code blocks, no commentary."""

    results = {}

    # Test Anthropic
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": test_prompt}]
            )
            content = response.content[0].text

            # Try to parse as JSON
            import json
            try:
                parsed = json.loads(content)
                print("✓ Anthropic: Returns valid JSON")
                results["anthropic"] = {"success": True, "returns_json": True}
            except json.JSONDecodeError:
                print("⚠️  Anthropic: Does not return pure JSON, needs parsing")
                print(f"   Response preview: {content[:200]}")
                results["anthropic"] = {"success": True, "returns_json": False}
        except Exception as e:
            print(f"❌ Anthropic JSON test failed: {e}")
            results["anthropic"] = {"success": False, "error": str(e)}

    # Test OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            import openai
            import json
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=500,
                messages=[{"role": "user", "content": test_prompt}]
            )
            content = response.choices[0].message.content

            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                print("✓ OpenAI: Returns valid JSON")
                results["openai"] = {"success": True, "returns_json": True}
            except json.JSONDecodeError:
                print("⚠️  OpenAI: Does not return pure JSON, needs parsing")
                print(f"   Response preview: {content[:200]}")
                results["openai"] = {"success": True, "returns_json": False}
        except Exception as e:
            print(f"❌ OpenAI JSON test failed: {e}")
            results["openai"] = {"success": False, "error": str(e)}

    # Test Gemini
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            import google.generativeai as genai
            import json
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(test_prompt)
            content = response.text

            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                print("✓ Gemini: Returns valid JSON")
                results["gemini"] = {"success": True, "returns_json": True}
            except json.JSONDecodeError:
                print("⚠️  Gemini: Does not return pure JSON, needs parsing")
                print(f"   Response preview: {content[:200]}")
                results["gemini"] = {"success": True, "returns_json": False}
        except Exception as e:
            print(f"❌ Gemini JSON test failed: {e}")
            results["gemini"] = {"success": False, "error": str(e)}

    return results


def main():
    """Run all tests."""
    print("=" * 60)
    print("LLM PROVIDER COMPATIBILITY TEST")
    print("=" * 60)
    print("\nThis script will test access to:")
    print("  1. Anthropic Claude API")
    print("  2. OpenAI GPT API")
    print("  3. Google Gemini API")
    print("\nYou can provide API keys via environment variables or when prompted.")

    results = []

    # Test each provider
    result = test_anthropic()
    if result:
        results.append(result)

    result = test_openai()
    if result:
        results.append(result)

    result = test_gemini()
    if result:
        results.append(result)

    # Test JSON extraction
    json_results = test_structured_json_extraction()

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    print(f"\n✅ Successful: {len(successful)}/{len(results)}")
    for r in successful:
        print(f"   - {r['provider']}: {r['model']}")

    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(results)}")
        for r in failed:
            print(f"   - {r['provider']}: {r.get('error', 'Unknown error')}")

    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if len(successful) == 0:
        print("\n⚠️  No providers working. Check your API keys.")
    elif len(successful) < len(results):
        print("\n⚠️  Some providers failed. Install missing libraries:")
        if not any(r['provider'] == 'anthropic' for r in successful):
            print("   pip install anthropic")
        if not any(r['provider'] == 'openai' for r in successful):
            print("   pip install openai")
        if not any(r['provider'] == 'gemini' for r in successful):
            print("   pip install google-generativeai")
    else:
        print("\n✅ All providers working! Ready to implement multi-provider support.")

    print("\nNext steps:")
    print("1. Save working API keys to config/credentials.yaml")
    print("2. Implement provider abstraction layer")
    print("3. Add provider selection to newsletters.yaml")


if __name__ == "__main__":
    main()
