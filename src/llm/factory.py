"""Factory for creating LLM provider instances."""

from typing import Optional

from .base import BaseLLMProvider
from .claude_provider import ClaudeProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider


class LLMProviderFactory:
    """Factory to create LLM provider instances."""

    # Map provider names to classes
    PROVIDERS = {
        'anthropic': ClaudeProvider,
        'claude': ClaudeProvider,
        'openai': OpenAIProvider,
        'gpt': OpenAIProvider,
        'gemini': GeminiProvider,
        'google': GeminiProvider,
    }

    # Default models for each provider
    DEFAULT_MODELS = {
        'anthropic': 'claude-sonnet-4-20250514',
        'claude': 'claude-sonnet-4-20250514',
        'openai': 'gpt-4o',
        'gpt': 'gpt-4o',
        'gemini': 'gemini-2.0-flash-exp',
        'google': 'gemini-2.0-flash-exp',
    }

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str,
        model: Optional[str] = None
    ) -> BaseLLMProvider:
        """
        Create an LLM provider instance.

        Args:
            provider_name: Name of the provider (anthropic, openai, gemini, etc.)
            api_key: API key for the provider
            model: Optional model override. If not provided, uses default for provider.

        Returns:
            Instance of BaseLLMProvider

        Raises:
            ValueError: If provider name is unknown
        """
        provider_name_lower = provider_name.lower()

        if provider_name_lower not in cls.PROVIDERS:
            available = ', '.join(cls.PROVIDERS.keys())
            raise ValueError(
                f"Unknown provider: {provider_name}. "
                f"Available providers: {available}"
            )

        provider_class = cls.PROVIDERS[provider_name_lower]

        # Use provided model or default
        if model is None:
            model = cls.DEFAULT_MODELS[provider_name_lower]

        return provider_class(api_key=api_key, model=model)

    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider names."""
        # Return unique provider names (deduplicate aliases)
        return ['anthropic', 'openai', 'gemini']
