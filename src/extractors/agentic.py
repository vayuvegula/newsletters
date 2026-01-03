"""Agentic extractor using two-pass LLM analysis."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Optional, Callable

import yaml

from .base import BaseExtractor
from ..llm import BaseLLMProvider

logger = logging.getLogger(__name__)


class AgenticExtractor(BaseExtractor):
    """
    Two-pass agentic extraction using any LLM provider.

    Pass 1: Analyze newsletter and reason through content
    Pass 2: Structure findings into JSON format

    Supports multiple LLM providers via abstraction layer.
    """

    MAX_EML_CHARS = 50000  # Truncate very long emails

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        progress_callback: Optional[Callable] = None,
        verbose: bool = False
    ):
        """
        Initialize the agentic extractor.

        Args:
            llm_provider: LLM provider instance (Claude, OpenAI, Gemini, etc.)
            progress_callback: Optional callback for progress updates
            verbose: If True, print detailed analysis to stdout
        """
        super().__init__(None, progress_callback)  # No longer uses api_key directly
        self.llm = llm_provider
        self.model = llm_provider.model
        self.provider_name = llm_provider.provider_name
        self.verbose = verbose

    def extract(self, eml_path: str | Path, config_path: Optional[str | Path] = None) -> dict:
        """
        Extract insights from newsletter using two-pass agentic analysis.

        Args:
            eml_path: Path to .eml file
            config_path: Optional path to extraction config YAML

        Returns:
            Structured extraction result as dict

        Raises:
            FileNotFoundError: If eml file doesn't exist
            ValueError: If file is invalid
            anthropic.APIError: For API errors
        """
        path = self._validate_eml_file(eml_path)

        # Load extraction config if provided
        config = self._load_config(config_path) if config_path else None

        self._log_progress(f"Reading {path.name}...")
        eml_content = self._read_eml(path)

        self._log_progress("Running pass 1: Analysis...")
        analysis_text, pass1_usage = self._analyze(eml_content, config)

        self._log_progress("Running pass 2: Structuring...")
        result, pass2_usage = self._structure(eml_content, analysis_text, config)

        # Add metadata
        result['_metadata'] = {
            'extractor': 'agentic',
            'provider': self.provider_name,
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

    def _load_config(self, config_path: str | Path) -> dict:
        """Load extraction config from YAML file."""
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"Config file not found: {path}, using defaults")
            return {}

        try:
            with open(path) as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded extraction config: {path.name}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load config {path}: {e}, using defaults")
            return {}

    def _read_eml(self, path: Path) -> str:
        """Read and truncate EML file content."""
        with open(path, 'r', errors='replace') as f:
            content = f.read()

        if len(content) > self.MAX_EML_CHARS:
            logger.warning(f"Truncating email from {len(content)} to {self.MAX_EML_CHARS} chars")
            content = content[:self.MAX_EML_CHARS]

        return content

    def _analyze(self, eml_content: str, config: Optional[dict] = None) -> tuple[str, 'LLMResponse']:
        """
        Pass 1: Let LLM analyze the newsletter and reason through it.

        Args:
            eml_content: Email content
            config: Optional extraction config dict

        Returns:
            (analysis_text, LLMResponse)
        """
        # Use config prompts if available, otherwise fall back to defaults
        if config and 'extraction' in config and 'prompts' in config['extraction']:
            prompts = config['extraction']['prompts']
            system_prompt = prompts.get('analysis_system_prompt', self._default_system_prompt())
            user_prompt_template = prompts.get('analysis_task_prompt', self._default_user_prompt())
            user_prompt = user_prompt_template.replace('{eml_content}', eml_content)
        else:
            system_prompt = self._default_system_prompt()
            user_prompt = self._default_user_prompt().replace('{eml_content}', eml_content)

        response = self.llm.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=8192
        )

        analysis_text = response.content

        if self.verbose:
            print("\n" + "=" * 60)
            print(f"{self.provider_name.upper()} ANALYSIS (Pass 1):")
            print("-" * 60)
            print(analysis_text[:3000])
            if len(analysis_text) > 3000:
                print("...")
            print("=" * 60)

        return analysis_text, response

    def _structure(
        self,
        eml_content: str,
        analysis_text: str,
        config: Optional[dict] = None
    ) -> tuple[dict, 'LLMResponse']:
        """
        Pass 2: Ask LLM to structure the analysis into JSON.

        Args:
            eml_content: Email content
            analysis_text: Analysis from pass 1
            config: Optional extraction config dict

        Returns:
            (structured_result_dict, LLMResponse)
        """
        # Build JSON schema from config if available
        if config and 'extraction' in config:
            json_schema = self._build_json_schema(config['extraction'])
            structuring_prompt = f"""Based on your analysis above, now provide a structured JSON output.

Your analysis:
{analysis_text}

Please provide the final output as JSON with this EXACT structure:

{json_schema}

IMPORTANT: Respond with ONLY valid JSON. No markdown, no code blocks, no commentary. Just the JSON object."""
        else:
            structuring_prompt = self._default_structuring_prompt(analysis_text)

        # Build message history (include pass 1 context)
        user_prompt = f"""Please analyze this newsletter email. It's from "The Batch" by DeepLearning.AI.

Here is the raw EML file content:

```
{eml_content}
```"""

        response = self.llm.complete_with_history(
            messages=[
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": analysis_text},
                {"role": "user", "content": structuring_prompt}
            ],
            max_tokens=4096
        )

        structured_text = response.content

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

        return result, response

    def _build_json_schema(self, extraction_config: dict) -> str:
        """Build JSON schema from extraction config."""
        stories_config = extraction_config.get('stories', {})
        required_fields = stories_config.get('required_fields', [])
        optional_fields = stories_config.get('optional_fields', [])

        # Build example story object
        story_fields = {}
        for field in required_fields:
            if field in ['companies', 'affected_functions', 'key_facts', 'follow_up_questions']:
                story_fields[field] = ["item1", "item2"]
            else:
                story_fields[field] = f"<{field} value>"

        for field in optional_fields:
            if field in ['companies', 'affected_functions']:
                story_fields[field] = ["item1", "item2"]
            else:
                story_fields[field] = f"<{field} value (optional)>"

        schema = {
            "executive_summary": "<3-4 sentence summary>",
            "stories": [story_fields]
        }

        return json.dumps(schema, indent=2)

    def _default_system_prompt(self) -> str:
        """Default system prompt for pass 1."""
        return """You are an AI research analyst with access to tools.
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

    def _default_user_prompt(self) -> str:
        """Default user prompt template for pass 1."""
        return """Please analyze this newsletter email. It's from "The Batch" by DeepLearning.AI.

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

    def _default_structuring_prompt(self, analysis_text: str) -> str:
        """Default structuring prompt for pass 2."""
        return f"""Based on your analysis above, now provide a structured JSON output.

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
