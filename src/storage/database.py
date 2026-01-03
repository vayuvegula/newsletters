"""SQLite database for tracking newsletter processing state."""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)


class Database:
    """Track newsletter processing state in SQLite."""

    def __init__(self, db_path: str = "data/newsletter.db"):
        """
        Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Access columns by name

        self._create_tables()
        logger.info(f"Database initialized: {self.db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Newsletters table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS newsletters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                sender_email TEXT NOT NULL,
                subject TEXT,
                received_date TIMESTAMP,
                downloaded_at TIMESTAMP,
                eml_path TEXT,
                processed_at TIMESTAMP,
                extraction_path TEXT,
                notion_page_id TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                tokens_used INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Processing log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                newsletter_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (newsletter_id) REFERENCES newsletters(id)
            )
        """)

        # Index for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_message_id
            ON newsletters(message_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sender_email
            ON newsletters(sender_email)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status
            ON newsletters(status)
        """)

        self.conn.commit()

    def is_processed(self, message_id: str) -> bool:
        """
        Check if a message has already been processed.

        Args:
            message_id: Gmail message ID

        Returns:
            True if message exists in database
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM newsletters WHERE message_id = ?",
            (message_id,)
        )
        return cursor.fetchone() is not None

    def add_newsletter(
        self,
        message_id: str,
        sender_email: str,
        subject: str = None,
        received_date: datetime = None
    ) -> int:
        """
        Add a new newsletter to track.

        Args:
            message_id: Gmail message ID
            sender_email: Sender email address
            subject: Email subject
            received_date: When email was received

        Returns:
            Newsletter ID (database primary key)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO newsletters (message_id, sender_email, subject, received_date)
            VALUES (?, ?, ?, ?)
        """, (message_id, sender_email, subject, received_date))

        self.conn.commit()
        newsletter_id = cursor.lastrowid

        self._log_event(newsletter_id, "added", f"Newsletter added: {subject}")
        logger.info(f"Added newsletter {message_id} to database")

        return newsletter_id

    def mark_downloaded(self, message_id: str, eml_path: str):
        """Mark newsletter as downloaded."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE newsletters
            SET downloaded_at = ?, eml_path = ?, updated_at = ?
            WHERE message_id = ?
        """, (datetime.now(), eml_path, datetime.now(), message_id))

        self.conn.commit()
        self._log_event_by_message_id(message_id, "downloaded", eml_path)

    def mark_extracted(self, message_id: str, extraction_path: str, tokens_used: int = None):
        """Mark newsletter as extracted."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE newsletters
            SET processed_at = ?, extraction_path = ?, tokens_used = ?, updated_at = ?
            WHERE message_id = ?
        """, (datetime.now(), extraction_path, tokens_used, datetime.now(), message_id))

        self.conn.commit()
        self._log_event_by_message_id(message_id, "extracted", f"Tokens: {tokens_used}")

    def mark_uploaded(self, message_id: str, notion_page_id: str):
        """Mark newsletter as uploaded to Notion."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE newsletters
            SET notion_page_id = ?, status = 'completed', updated_at = ?
            WHERE message_id = ?
        """, (notion_page_id, datetime.now(), message_id))

        self.conn.commit()
        self._log_event_by_message_id(message_id, "uploaded", notion_page_id)

    def mark_failed(self, message_id: str, error_message: str):
        """Mark newsletter as failed."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE newsletters
            SET status = 'failed', error_message = ?, updated_at = ?
            WHERE message_id = ?
        """, (error_message, datetime.now(), message_id))

        self.conn.commit()
        self._log_event_by_message_id(message_id, "failed", error_message)

    def get_last_processed_date(self, sender_email: str) -> Optional[str]:
        """
        Get the date of the last processed newsletter from a sender.

        Args:
            sender_email: Sender email address

        Returns:
            Date in YYYY/MM/DD format for Gmail query, or None
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT MAX(received_date) as last_date
            FROM newsletters
            WHERE sender_email = ? AND status = 'completed'
        """, (sender_email,))

        row = cursor.fetchone()
        if row and row['last_date']:
            # Convert to Gmail date format (YYYY/MM/DD)
            dt = datetime.fromisoformat(row['last_date'])
            return dt.strftime("%Y/%m/%d")

        return None

    def get_pending_newsletters(self) -> List[dict]:
        """Get all newsletters that are pending processing."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM newsletters
            WHERE status = 'pending'
            ORDER BY received_date ASC
        """)

        return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> dict:
        """Get processing statistics."""
        cursor = self.conn.cursor()

        stats = {}

        # Total count
        cursor.execute("SELECT COUNT(*) as total FROM newsletters")
        stats['total'] = cursor.fetchone()['total']

        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM newsletters
            GROUP BY status
        """)
        stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

        # Total tokens used
        cursor.execute("SELECT SUM(tokens_used) as total_tokens FROM newsletters")
        stats['total_tokens'] = cursor.fetchone()['total_tokens'] or 0

        return stats

    def _log_event(self, newsletter_id: int, event: str, details: str = None):
        """Log a processing event."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO processing_log (newsletter_id, event, details)
            VALUES (?, ?, ?)
        """, (newsletter_id, event, details))
        self.conn.commit()

    def _log_event_by_message_id(self, message_id: str, event: str, details: str = None):
        """Log event by message ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id FROM newsletters WHERE message_id = ?",
            (message_id,)
        )
        row = cursor.fetchone()
        if row:
            self._log_event(row['id'], event, details)

    def close(self):
        """Close database connection."""
        self.conn.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
