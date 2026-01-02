"""Agentic extractor using two-pass Claude analysis."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional, Callable

import anthropic

from .base import BaseExtractor

logger = logging.getLogger(__name__)


class AgenticExtractor(BaseExtractor):
    """
    Two-pass agentic extraction using Claude API.

    Pass 1: Analyze newsletter and reason through content
    Pass 2: Structure findings into JSON format

    This is the production version of test2_agentic.py from experiments.
    """

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    MAX_EML_CHARS = 50000  # Truncate very long emails

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        progress_callback: Optional[Callable] = None,
        verbose: bool = False
    ):
        """
        Initialize the agentic extractor.

        Args:
            api_key: Anthropic API key (falls back to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            progress_callback: Optional callback for progress updates
            verbose: If True, print detailed analysis to stdout
        """
        super().__init__(api_key, progress_callback)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or arguments")

        self.model = model
        self.verbose = verbose
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def extract(self, eml_path: str | Path) -> dict:
        """
        Extract insights from newsletter using two-pass agentic analysis.

        Args:
            eml_path: Path to .eml file

        Returns:
            Structured extraction result as dict

        Raises:
            FileNotFoundError: If eml file doesn't exist
            ValueError: If file is invalid
            anthropic.APIError: For API errors
        """
        path = self._validate_eml_file(eml_path)

        self._log_progress(f"Reading {path.name}...")
        eml_content = self._read_eml(path)

        self._log_progress("Running pass 1: Analysis...")
        analysis_text, pass1_usage = self._analyze(eml_content)

        self._log_progress("Running pass 2: Structuring...")
        result, pass2_usage = self._structure(eml_content, analysis_text)

        # Add metadata
        result['_metadata'] = {
            'extractor': 'agentic',
            'model': self.model,
            'pass1_input_tokens': pass1_usage.input_tokens,
            'pass1_output_tokens': pass1_usage.output_tokens,
            'pass2_input_tokens': pass2_usage.input_tokens,
            'pass2_output_tokens': pass2_usage.output_tokens,
            'total_tokens': (
                pass1_usage.input_tokens + pass1_usage.output_tokens +
                pass2_usage.input_tokens + pass2_usage.output_tokens
            ),
            'source_file': str(path)
        }

        # Store raw reasoning for debugging
        result['_raw_reasoning'] = analysis_text

        self._log_progress(f"✓ Extraction complete ({result['_metadata']['total_tokens']} tokens)")

        return result

    def _read_eml(self, path: Path) -> str:
        """Read and truncate EML file content."""
        with open(path, 'r', errors='replace') as f:
            content = f.read()

        if len(content) > self.MAX_EML_CHARS:
            logger.warning(f"Truncating email from {len(content)} to {self.MAX_EML_CHARS} chars")
            content = content[:self.MAX_EML_CHARS]

        return content

    def _analyze(self, eml_content: str) -> tuple[str, anthropic.types.Usage]:
        """
        Pass 1: Let Claude analyze the newsletter and reason through it.

        Returns:
            (analysis_text, usage_stats)
        """
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
{eml_content}
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

        response = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        analysis_text = response.content[0].text

        if self.verbose:
            print("\n" + "=" * 60)
            print("CLAUDE'S ANALYSIS (Pass 1):")
            print("-" * 60)
            print(analysis_text[:3000])
            if len(analysis_text) > 3000:
                print("...")
            print("=" * 60)

        return analysis_text, response.usage

    def _structure(
        self,
        eml_content: str,
        analysis_text: str
    ) -> tuple[dict, anthropic.types.Usage]:
        """
        Pass 2: Ask Claude to structure the analysis into JSON.

        Returns:
            (structured_result_dict, usage_stats)
        """
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

        # Build message history (include pass 1 context)
        user_prompt = f"""Please analyze this newsletter email. It's from "The Batch" by DeepLearning.AI.

Here is the raw EML file content:

```
{eml_content}
```"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": analysis_text},
                {"role": "user", "content": structuring_prompt}
            ]
        )

        structured_text = response.content[0].text

        # Parse JSON
        try:
            result = json.loads(structured_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks or text
            logger.warning("Failed to parse JSON directly, trying regex extraction")
            json_match = re.search(r'\{.*\}', structured_text, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    logger.error("Failed to parse extracted JSON")
                    result = {
                        "raw_analysis": analysis_text,
                        "raw_structured": structured_text,
                        "parse_error": True,
                        "error": "JSON parsing failed"
                    }
            else:
                logger.error("No JSON found in response")
                result = {
                    "raw_analysis": analysis_text,
                    "raw_structured": structured_text,
                    "parse_error": True,
                    "error": "No JSON found"
                }

        return result, response.usage
