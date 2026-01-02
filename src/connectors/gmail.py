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

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']


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
        Add a label to mark message as processed.

        Args:
            message_id: Gmail message ID
            label_name: Label name to add (will be created if doesn't exist)
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Get or create label
            label_id = self._get_or_create_label(label_name)

            # Add label to message
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()

            logger.info(f"Marked message {message_id} as processed")

        except HttpError as error:
            logger.error(f"Failed to mark message: {error}")
            raise

    def mark_as_read(self, message_id: str) -> None:
        """Mark a message as read."""
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            logger.info(f"Marked message {message_id} as read")

        except HttpError as error:
            logger.error(f"Failed to mark as read: {error}")

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
