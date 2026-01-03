"""Notion API connector for storing newsletter insights."""

import logging
from datetime import datetime
from typing import Optional, List, Dict

from notion_client import Client
from notion_client.errors import APIResponseError

logger = logging.getLogger(__name__)


class NotionConnector:
    """Connect to Notion API to store newsletter insights."""

    def __init__(self, api_key: str, database_ids: Optional[Dict[str, str]] = None):
        """
        Initialize Notion connector.

        Args:
            api_key: Notion integration token (starts with "secret_")
            database_ids: Dict with keys: "newsletters", "stories", "trends"
        """
        self.client = Client(auth=api_key)
        self.database_ids = database_ids or {}
        logger.info("Notion client initialized")

    def create_newsletter_database(self, parent_page_id: Optional[str] = None) -> str:
        """
        Create the Newsletter Insights database.

        Args:
            parent_page_id: Optional parent page ID (if None, creates in workspace root)

        Returns:
            Database ID
        """
        logger.info("Creating Newsletter Insights database...")

        # Define database schema
        properties = {
            "Title": {"title": {}},
            "Source": {
                "select": {
                    "options": [
                        {"name": "The Batch", "color": "blue"},
                        {"name": "TLDR", "color": "green"},
                        {"name": "Other", "color": "gray"}
                    ]
                }
            },
            "Date": {"date": {}},
            "Executive Summary": {"rich_text": {}},
            "Stories Count": {"number": {"format": "number"}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "Processing", "color": "yellow"},
                        {"name": "Ready", "color": "green"},
                        {"name": "Failed", "color": "red"}
                    ]
                }
            },
            "Processed At": {"date": {}},
            "Token Cost": {"number": {"format": "number"}},
            "Raw Data URL": {"url": {}}
        }

        # Create database
        parent = {"page_id": parent_page_id} if parent_page_id else {"type": "workspace", "workspace": True}

        database = self.client.databases.create(
            parent=parent,
            title=[{"type": "text", "text": {"content": "AI Newsletter Insights"}}],
            properties=properties
        )

        db_id = database["id"]
        logger.info(f"✓ Created Newsletter database: {db_id}")
        return db_id

    def create_stories_database(self, parent_page_id: Optional[str] = None) -> str:
        """
        Create the Stories database.

        Args:
            parent_page_id: Optional parent page ID

        Returns:
            Database ID
        """
        logger.info("Creating Stories database...")

        properties = {
            "Title": {"title": {}},
            "Category": {
                "select": {
                    "options": [
                        {"name": "competitive_intelligence", "color": "red"},
                        {"name": "talent_market", "color": "purple"},
                        {"name": "infrastructure", "color": "blue"},
                        {"name": "product_development", "color": "green"},
                        {"name": "regulation", "color": "orange"},
                        {"name": "research", "color": "pink"}
                    ]
                }
            },
            "Companies": {"multi_select": {}},
            "Key Facts": {"rich_text": {}},
            "Google Implications": {"rich_text": {}},
            "Confidence": {
                "select": {
                    "options": [
                        {"name": "High", "color": "green"},
                        {"name": "Medium", "color": "yellow"},
                        {"name": "Low", "color": "gray"}
                    ]
                }
            },
            "Links": {"url": {}}
        }

        parent = {"page_id": parent_page_id} if parent_page_id else {"type": "workspace", "workspace": True}

        database = self.client.databases.create(
            parent=parent,
            title=[{"type": "text", "text": {"content": "Newsletter Stories"}}],
            properties=properties
        )

        db_id = database["id"]
        logger.info(f"✓ Created Stories database: {db_id}")
        return db_id

    def create_newsletter_page(self, extraction_result: dict, database_id: str) -> str:
        """
        Create a page in the Newsletter database.

        Args:
            extraction_result: The extraction JSON from AgenticExtractor
            database_id: Newsletter database ID

        Returns:
            Page ID
        """
        # Parse metadata
        metadata = extraction_result.get('_metadata', {})
        source_file = metadata.get('source_file', '')
        source_name = "The Batch" if "batch" in source_file.lower() else "Other"

        # Build properties
        properties = {
            "Title": {
                "title": [{"text": {"content": extraction_result.get('executive_summary', '')[:100]}}]
            },
            "Source": {"select": {"name": source_name}},
            "Date": {"date": {"start": datetime.now().isoformat()}},
            "Executive Summary": {
                "rich_text": [{"text": {"content": extraction_result.get('executive_summary', '')[:2000]}}]
            },
            "Stories Count": {"number": len(extraction_result.get('stories', []))},
            "Status": {"select": {"name": "Ready"}},
            "Processed At": {"date": {"start": datetime.now().isoformat()}},
            "Token Cost": {"number": metadata.get('total_tokens', 0)}
        }

        # Create page
        page = self.client.pages.create(
            parent={"database_id": database_id},
            properties=properties
        )

        page_id = page["id"]
        logger.info(f"✓ Created newsletter page: {page_id}")
        return page_id

    def _build_story_properties(self, story: dict) -> dict:
        """
        Dynamically build Notion properties from story dict.
        Handles both default extraction and VP insights extraction.

        Args:
            story: Story dict from extraction

        Returns:
            Notion properties dict
        """
        properties = {}

        # Title is always required
        properties["Title"] = {
            "title": [{"text": {"content": story.get('title', 'Untitled')[:100]}}]
        }

        # VP Insights fields
        if 'insight_type' in story:
            properties["Insight Type"] = {
                "select": {"name": story.get('insight_type', 'Strategic Implication')}
            }

        if 'core_claim' in story:
            properties["Core Claim"] = {
                "rich_text": [{"text": {"content": story.get('core_claim', '')[:2000]}}]
            }

        if 'why_it_matters' in story:
            properties["Why It Matters"] = {
                "rich_text": [{"text": {"content": story.get('why_it_matters', '')[:2000]}}]
            }

        if 'affected_functions' in story:
            functions = story.get('affected_functions', [])
            if isinstance(functions, list):
                properties["Affected Functions"] = {
                    "multi_select": [{"name": func} for func in functions[:10]]
                }

        if 'time_horizon' in story:
            properties["Time Horizon"] = {
                "select": {"name": story.get('time_horizon', 'Now')}
            }

        if 'confidence_level' in story:
            properties["Confidence Level"] = {
                "select": {"name": story.get('confidence_level', 'Medium')}
            }

        if 'contrarian_angle' in story:
            properties["Contrarian Angle"] = {
                "rich_text": [{"text": {"content": story.get('contrarian_angle', '')[:2000]}}]
            }

        if 'execution_constraint' in story:
            properties["Execution Constraint"] = {
                "rich_text": [{"text": {"content": story.get('execution_constraint', '')[:2000]}}]
            }

        if 'second_order_effect' in story:
            properties["Second-Order Effect"] = {
                "rich_text": [{"text": {"content": story.get('second_order_effect', '')[:2000]}}]
            }

        if 'follow_up_questions' in story:
            questions = story.get('follow_up_questions', '')
            if isinstance(questions, list):
                questions = "\n".join(questions)
            properties["Follow-Up Questions"] = {
                "rich_text": [{"text": {"content": questions[:2000]}}]
            }

        if 'strategic_implication' in story:
            properties["Strategic Implication"] = {
                "rich_text": [{"text": {"content": story.get('strategic_implication', '')[:2000]}}]
            }

        if 'source_context' in story:
            properties["Source Context"] = {
                "rich_text": [{"text": {"content": story.get('source_context', '')[:2000]}}]
            }

        # Default extraction fields (for backwards compatibility)
        if 'category' in story:
            properties["Category"] = {
                "select": {"name": story.get('category', 'research')}
            }

        if 'companies' in story:
            properties["Companies"] = {
                "multi_select": [{"name": company} for company in story.get('companies', [])[:10]]
            }

        if 'key_facts' in story:
            key_facts = story.get('key_facts', [])
            if isinstance(key_facts, list):
                key_facts = "\n".join(key_facts)
            properties["Key Facts"] = {
                "rich_text": [{"text": {"content": key_facts[:2000]}}]
            }

        if 'google_implications' in story:
            properties["Google Implications"] = {
                "rich_text": [{"text": {"content": story.get('google_implications', '')[:2000]}}]
            }

        if 'confidence' in story and 'confidence_level' not in story:
            properties["Confidence"] = {
                "select": {"name": story.get('confidence', 'medium').capitalize()}
            }

        return properties

    def _ensure_database_properties(self, database_id: str, story: dict) -> None:
        """
        Ensure database has all required properties for this story.
        Auto-creates missing properties dynamically.

        Args:
            database_id: Notion database ID
            story: Story dict with fields to check
        """
        # Get current database schema
        try:
            database = self.client.databases.retrieve(database_id=database_id)
            existing_props = set(database.get("properties", {}).keys())
        except Exception as e:
            logger.warning(f"Could not retrieve database schema: {e}")
            return

        # Map story fields to Notion property names
        field_to_property = {
            'insight_type': 'Insight Type',
            'core_claim': 'Core Claim',
            'why_it_matters': 'Why It Matters',
            'affected_functions': 'Affected Functions',
            'time_horizon': 'Time Horizon',
            'confidence_level': 'Confidence Level',
            'contrarian_angle': 'Contrarian Angle',
            'execution_constraint': 'Execution Constraint',
            'second_order_effect': 'Second-Order Effect',
            'follow_up_questions': 'Follow-Up Questions',
            'strategic_implication': 'Strategic Implication',
            'source_context': 'Source Context',
            'category': 'Category',
            'companies': 'Companies',
            'key_facts': 'Key Facts',
            'google_implications': 'Google Implications',
            'confidence': 'Confidence'
        }

        # Find missing properties
        missing_props = {}
        for field, prop_name in field_to_property.items():
            if field in story and prop_name not in existing_props:
                # Determine property type based on field
                if field in ['affected_functions', 'companies']:
                    missing_props[prop_name] = {"multi_select": {"options": []}}
                elif field in ['insight_type', 'time_horizon', 'confidence_level', 'category', 'confidence']:
                    missing_props[prop_name] = {"select": {"options": []}}
                else:
                    missing_props[prop_name] = {"rich_text": {}}

        # Add missing properties if any
        if missing_props:
            logger.info(f"Auto-creating {len(missing_props)} new database properties: {list(missing_props.keys())}")
            try:
                self.client.databases.update(
                    database_id=database_id,
                    properties=missing_props
                )
            except Exception as e:
                logger.warning(f"Could not auto-create properties: {e}")

    def create_story_pages(
        self,
        newsletter_page_id: str,
        stories: List[dict],
        database_id: str
    ) -> List[str]:
        """
        Create story pages in the Stories database.
        Automatically creates missing database properties as needed.

        Args:
            newsletter_page_id: Parent newsletter page ID
            stories: List of story dicts from extraction
            database_id: Stories database ID

        Returns:
            List of created page IDs
        """
        page_ids = []

        # Ensure database has all needed properties (check first story as representative)
        if stories:
            self._ensure_database_properties(database_id, stories[0])

        for story in stories:
            # Build properties dynamically based on extraction fields
            properties = self._build_story_properties(story)

            # Create page
            page = self.client.pages.create(
                parent={"database_id": database_id},
                properties=properties
            )

            page_ids.append(page["id"])
            logger.info(f"  ✓ Created story: {story.get('title', 'Untitled')[:50]}")

        logger.info(f"Created {len(page_ids)} story pages")
        return page_ids

    def update_processing_status(
        self,
        page_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Update newsletter page status.

        Args:
            page_id: Newsletter page ID
            status: "Processing", "Ready", or "Failed"
            error_message: Optional error message if failed
        """
        properties = {
            "Status": {"select": {"name": status}}
        }

        self.client.pages.update(page_id=page_id, properties=properties)
        logger.info(f"Updated page {page_id} status to: {status}")

    def test_connection(self) -> bool:
        """
        Test Notion API connection.

        Returns:
            True if connection successful
        """
        try:
            # Try to list users (basic API test)
            self.client.users.me()
            logger.info("✓ Notion connection successful")
            return True
        except APIResponseError as e:
            logger.error(f"✗ Notion connection failed: {e}")
            return False

    def get_database_info(self, database_id: str) -> dict:
        """Get information about a database."""
        try:
            db = self.client.databases.retrieve(database_id=database_id)
            return {
                "title": db.get("title", [{}])[0].get("plain_text", "Unknown"),
                "properties": list(db.get("properties", {}).keys())
            }
        except APIResponseError as e:
            logger.error(f"Failed to get database info: {e}")
            return {}
