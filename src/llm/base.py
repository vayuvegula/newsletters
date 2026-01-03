"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""

    content: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str


class BaseLLMProvider(ABC):
    """Base interface that all LLM providers must implement."""

    def __init__(self, api_key: str, model: str):
        """
        Initialize the provider.

        Args:
            api_key: API key for the provider
            model: Model identifier
        """
        self.api_key = api_key
        self.model = model
        self.provider_name = self.__class__.__name__.replace('Provider', '').lower()

    @abstractmethod
    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 8192
    ) -> LLMResponse:
        """
        Send a completion request with system and user prompts.

        Args:
            system_prompt: System prompt to set context
            user_prompt: User prompt with the task
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with standardized fields
        """
        pass

    @abstractmethod
    def complete_with_history(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096
    ) -> LLMResponse:
        """
        Send a completion request with message history.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate

        Returns:
            LLMResponse with standardized fields
        """
        pass
