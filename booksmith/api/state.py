"""
In-memory state management for book tracking.
"""

import json
import logging
import os
import uuid
from typing import Dict, Optional
from uuid import UUID

import firebase_admin
from firebase_admin import credentials, firestore

from ..models import Book

logger = logging.getLogger(__name__)


class BookStateManager:
    """Manages book states using Firestore."""

    def __init__(self):
        """Initialize the state manager with Firestore connection."""
        self._initialize_firestore()

    def _initialize_firestore(self):
        """Initialize Firebase app and Firestore client."""
        try:
            # Try to get existing app first
            firebase_admin.get_app()
        except ValueError:
            # App doesn't exist, create it
            firebase_creds = os.environ.get("FIREBASE_CREDENTIALS")
            if firebase_creds:
                # Parse credentials from environment variable (JSON string)
                cred_dict = json.loads(firebase_creds)
                cred = credentials.Certificate(cred_dict)
            else:
                # For local development, use application default credentials
                # or a service account key file
                cred_file = os.environ.get("FIREBASE_SERVICE_ACCOUNT_KEY")
                if cred_file and os.path.exists(cred_file):
                    cred = credentials.Certificate(cred_file)
                else:
                    # Use default credentials (useful for local dev with gcloud auth)
                    logger.warning("No Firebase credentials found, using default")
                    cred = credentials.ApplicationDefault()

            firebase_admin.initialize_app(cred)

        # Initialize Firestore client
        self.db = firestore.client()
        self.collection_name = "books"
        logger.info("Firestore client initialized successfully")

    def create_book(self, user_id: str, **book_data) -> tuple[UUID, Book]:
        """Create a new book and return its UUID and Book object."""
        try:
            book_id = uuid.uuid4()
            book = Book(**book_data)

            # Store in user's subcollection
            collection_path = f"users/{user_id}/books"
            doc_ref = self.db.collection(collection_path).document(str(book_id))
            doc_ref.set(book.model_dump())

            logger.info(f"Created book with ID: {book_id} for user {user_id}")
            return book_id, book
        except Exception as e:
            logger.error(f"Error creating book: {e}")
            raise

    def get_book(self, user_id: str, book_id: UUID) -> Optional[Book]:
        """Get a book by its UUID from user's collection."""
        try:
            collection_path = f"users/{user_id}/books"
            doc_ref = self.db.collection(collection_path).document(str(book_id))
            doc = doc_ref.get()

            if doc.exists:
                book_data = doc.to_dict()
                return Book.model_validate(book_data)
            else:
                return None
        except Exception as e:
            logger.error(f"Error getting book {book_id} for user {user_id}: {e}")
            raise

    def update_book(self, user_id: str, book_id: UUID, book: Book) -> bool:
        """Update an existing book in user's collection."""
        try:
            collection_path = f"users/{user_id}/books"
            doc_ref = self.db.collection(collection_path).document(str(book_id))

            # Check if document exists
            if not doc_ref.get().exists:
                return False

            # Update the document
            doc_ref.set(book.model_dump(), merge=True)
            logger.info(f"Updated book with ID: {book_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating book {book_id} for user {user_id}: {e}")
            raise

    def book_exists(self, user_id: str, book_id: UUID) -> bool:
        """Check if a book exists."""
        try:
            collection_path = f"users/{user_id}/books"
            doc_ref = self.db.collection(collection_path).document(str(book_id))
            return doc_ref.get().exists
        except Exception as e:
            logger.error(
                f"Error checking if book exists {book_id} for user {user_id}: {e}"
            )
            raise

    def list_user_books(self, user_id: str) -> Dict[UUID, Book]:
        """Get all books for a specific user."""
        try:
            books = {}
            collection_path = f"users/{user_id}/books"
            docs = self.db.collection(collection_path).stream()

            for doc in docs:
                book_id = UUID(doc.id)
                book_data = doc.to_dict()
                books[book_id] = Book.model_validate(book_data)

            return books
        except Exception as e:
            logger.error(f"Error listing books for user {user_id}: {e}")
            raise

    def delete_book(self, user_id: str, book_id: UUID) -> bool:
        """Delete a book by its UUID. Returns True if successful, False if book not found."""
        try:
            collection_path = f"users/{user_id}/books"
            doc_ref = self.db.collection(collection_path).document(str(book_id))

            # Check if document exists
            if not doc_ref.get().exists:
                return False

            # Delete the document
            doc_ref.delete()
            logger.info(f"Deleted book with ID: {book_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting book {book_id} for user {user_id}: {e}")
            raise
