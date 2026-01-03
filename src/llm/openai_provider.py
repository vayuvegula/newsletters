"""OpenAI GPT LLM provider."""

import openai
from typing import List, Dict

from .base import BaseLLMProvider, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT API provider."""

    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: GPT model to use
        """
        super().__init__(api_key, model)
        self.client = openai.OpenAI(api_key=api_key)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192
    ) -> LLMResponse:
        """Send a completion request to OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=response.model,
            provider="openai"
        )

    def complete_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096
    ) -> LLMResponse:
        """Send a completion request with message history to OpenAI."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=messages
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            model=response.model,
            provider="openai"
        )
