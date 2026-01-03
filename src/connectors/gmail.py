"""Gmail API connector for fetching newsletters."""

import base64
import email
import logging
import os
import pickle
from pathlib import Path
from typing import Optional, List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Gmail API scopes - using readonly only for security
# Note: Without modify scope, we can't mark messages as processed in Gmail
# We'll track processed messages in local database instead
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailConnector:
    """Connect to Gmail API to fetch and manage newsletters."""

    def __init__(self, credentials_path: str, token_path: str = "config/gmail_token.json"):
        """
        Initialize Gmail connector.

        Args:
            credentials_path: Path to OAuth credentials JSON file
            token_path: Path to store OAuth token (created after first auth)
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.service = None
        self.creds = None

    def authenticate(self) -> None:
        """
        Authenticate with Gmail API using OAuth 2.0.

        On first run, opens browser for user consent.
        Subsequent runs use saved token.
        """
        # Check if token already exists
        if self.token_path.exists():
            logger.info(f"Loading existing token from {self.token_path}")
            self.creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)

        # If no valid credentials, authenticate
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                logger.info("Refreshing expired token...")
                self.creds.refresh(Request())
            else:
                logger.info("Starting OAuth flow...")
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Gmail credentials not found: {self.credentials_path}\n"
                        f"Download from Google Cloud Console and save to this path."
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                self.creds = flow.run_local_server(port=8080)

            # Save credentials for next run
            logger.info(f"Saving token to {self.token_path}")
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())

        # Build Gmail service
        self.service = build('gmail', 'v1', credentials=self.creds)
        logger.info("✓ Gmail API authenticated successfully")

    def search_newsletters(
        self,
        sender_email: str,
        since_date: Optional[str] = None,
        max_results: int = 10,
        unread_only: bool = False
    ) -> List[str]:
        """
        Search for newsletters from a specific sender.

        Args:
            sender_email: Email address to search for (e.g., "thebatch@deeplearning.ai")
            since_date: Optional date filter in format "YYYY/MM/DD"
            max_results: Maximum number of messages to return
            unread_only: If True, only return unread messages

        Returns:
            List of message IDs
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Build search query
        query_parts = [f"from:{sender_email}"]
        if since_date:
            query_parts.append(f"after:{since_date}")
        if unread_only:
            query_parts.append("is:unread")

        query = " ".join(query_parts)
        logger.info(f"Searching Gmail: {query}")

        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            message_ids = [msg['id'] for msg in messages]

            logger.info(f"Found {len(message_ids)} messages")
            return message_ids

        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            raise

    def download_message(self, message_id: str, output_path: str) -> dict:
        """
        Download a message as .eml file.

        Args:
            message_id: Gmail message ID
            output_path: Path to save .eml file

        Returns:
            Message metadata (subject, date, from, etc.)
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Get the full message
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='raw'
            ).execute()

            # Decode the raw message
            msg_bytes = base64.urlsafe_b64decode(message['raw'])

            # Save as .eml file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'wb') as f:
                f.write(msg_bytes)

            # Parse for metadata
            msg = email.message_from_bytes(msg_bytes)
            metadata = {
                'message_id': message_id,
                'subject': msg.get('Subject', ''),
                'from': msg.get('From', ''),
                'date': msg.get('Date', ''),
                'to': msg.get('To', ''),
                'file_path': str(output_file)
            }

            logger.info(f"Downloaded: {metadata['subject']}")
            return metadata

        except HttpError as error:
            logger.error(f"Failed to download message {message_id}: {error}")
            raise

    def mark_as_processed(self, message_id: str, label_name: str = "Newsletters/Processed") -> None:
        """
        Mark message as processed (readonly mode - no-op).

        Note: In readonly mode, we can't modify Gmail.
        Processed messages are tracked in local database instead.

        Args:
            message_id: Gmail message ID
            label_name: Label name (ignored in readonly mode)
        """
        logger.info(f"Readonly mode: Skipping Gmail label for {message_id} (will track in database)")
        # No-op in readonly mode

    def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read (readonly mode - no-op)."""
        logger.info(f"Readonly mode: Skipping mark as read for {message_id}")
        # No-op in readonly mode

    def _get_or_create_label(self, label_name: str) -> str:
        """
        Get label ID, creating it if it doesn't exist.

        Args:
            label_name: Label name (can include slashes for nested labels)

        Returns:
            Label ID
        """
        # List existing labels
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])

        # Check if label exists
        for label in labels:
            if label['name'] == label_name:
                return label['id']

        # Create new label
        logger.info(f"Creating new label: {label_name}")
        label_object = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show'
        }

        created_label = self.service.users().labels().create(
            userId='me',
            body=label_object
        ).execute()

        return created_label['id']

    def get_message_count(self, sender_email: str) -> int:
        """Get total count of messages from a sender."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        query = f"from:{sender_email}"
        results = self.service.users().messages().list(
            userId='me',
            q=query,
            maxResults=1
        ).execute()

        return results.get('resultSizeEstimate', 0)
