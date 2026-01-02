"""Connectors for external services (Gmail, Notion)."""

from .gmail import GmailConnector
from .notion import NotionConnector

__all__ = ["GmailConnector", "NotionConnector"]
