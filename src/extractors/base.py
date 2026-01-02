"""Base extractor interface for newsletter content extraction."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Callable


class BaseExtractor(ABC):
    """Base class for newsletter content extractors."""

    def __init__(self, api_key: Optional[str] = None, progress_callback: Optional[Callable] = None):
        """
        Initialize the extractor.

        Args:
            api_key: API key for the extraction service (e.g., Anthropic)
            progress_callback: Optional callback function for progress updates
        """
        self.api_key = api_key
        self.progress_callback = progress_callback

    @abstractmethod
    def extract(self, eml_path: str | Path) -> dict:
        """
        Extract insights from a newsletter email file.

        Args:
            eml_path: Path to the .eml file

        Returns:
            Dictionary containing extraction results with structure:
            {
                "executive_summary": str,
                "stories": list[dict],
                "trend_signals": list[dict],
                "action_items": list[str],
                "_metadata": dict
            }

        Raises:
            FileNotFoundError: If the eml file doesn't exist
            ValueError: If the file is not a valid .eml file
            Exception: For extraction errors
        """
        pass

    def _log_progress(self, message: str) -> None:
        """Log progress update if callback is provided."""
        if self.progress_callback:
            self.progress_callback(message)

    def _validate_eml_file(self, eml_path: str | Path) -> Path:
        """
        Validate that the file exists and is an .eml file.

        Args:
            eml_path: Path to validate

        Returns:
            Path object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not .eml
        """
        path = Path(eml_path)
        if not path.exists():
            raise FileNotFoundError(f"EML file not found: {eml_path}")
        if path.suffix.lower() != ".eml":
            raise ValueError(f"File must be .eml format, got: {path.suffix}")
        return path
