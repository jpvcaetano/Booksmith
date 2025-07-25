"""
In-memory state management for book tracking.
"""

import uuid
from typing import Dict, Optional
from uuid import UUID

from ..models import Book


class BookStateManager:
    """Manages book states in memory using UUIDs."""

    def __init__(self):
        """Initialize the state manager with an empty book store."""
        self._books: Dict[UUID, Book] = {}

    def create_book(self, **book_data) -> tuple[UUID, Book]:
        """Create a new book and return its UUID and Book object."""
        book_id = uuid.uuid4()
        book = Book(**book_data)
        self._books[book_id] = book
        return book_id, book

    def get_book(self, book_id: UUID) -> Optional[Book]:
        """Get a book by its UUID."""
        return self._books.get(book_id)

    def update_book(self, book_id: UUID, book: Book) -> bool:
        """Update an existing book. Returns True if successful, False if book not found."""
        if book_id not in self._books:
            return False
        self._books[book_id] = book
        return True

    def book_exists(self, book_id: UUID) -> bool:
        """Check if a book exists."""
        return book_id in self._books

    def list_books(self) -> Dict[UUID, Book]:
        """Get all books (for debugging/admin purposes)."""
        return self._books.copy()

    def clear_all(self) -> None:
        """Clear all books (for testing purposes)."""
        self._books.clear()
