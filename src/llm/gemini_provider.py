"""Google Gemini LLM provider."""

from google import genai
from typing import List, Dict

from .base import BaseLLMProvider, LLMResponse


class GeminiProvider(BaseLLMProvider):
    """Google Gemini API provider using new google-genai SDK."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google/Gemini API key
            model: Gemini model to use
        """
        super().__init__(api_key, model)
        self.client = genai.Client(api_key=api_key)

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192
    ) -> LLMResponse:
        """
        Send a completion request to Gemini.

        Note: Gemini combines system and user prompts.
        """
        # Gemini doesn't have separate system prompt in generate_content
        # Combine them
        combined_prompt = f"{system_prompt}\n\n{user_prompt}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=combined_prompt
        )

        # Extract token counts
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata'):
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

        return LLMResponse(
            content=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            provider="gemini"
        )

    def complete_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096
    ) -> LLMResponse:
        """
        Send a completion request with message history to Gemini.

        Note: Gemini uses a different message format. We'll convert.
        """
        # Convert messages to Gemini format
        # Gemini doesn't support system role, so we'll prepend it to first user message
        gemini_contents = []

        for msg in messages:
            role = msg.get('role')
            content = msg.get('content')

            if role == 'system':
                # System messages get prepended to next user message
                # For now, we'll just combine into a single prompt
                continue
            elif role == 'user':
                gemini_contents.append(content)
            elif role == 'assistant':
                gemini_contents.append(content)

        # For simplicity with multi-turn, just use the full conversation as text
        full_conversation = "\n\n".join(gemini_contents)

        response = self.client.models.generate_content(
            model=self.model,
            contents=full_conversation
        )

        # Extract token counts
        input_tokens = 0
        output_tokens = 0
        if hasattr(response, 'usage_metadata'):
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count

        return LLMResponse(
            content=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            provider="gemini"
        )
