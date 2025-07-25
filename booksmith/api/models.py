"""
Pydantic models for API requests and responses.
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models import Book, Chapter, Character


# Request Models
class BookIdRequest(BaseModel):
    """Base request model for operations that require a book ID."""

    book_id: UUID = Field(..., description="The UUID of the book")


class GenerateSummaryRequest(BaseModel):
    """Request model for generating story summary.

    Uses the same field names and defaults as the Book model for consistency.
    """

    base_prompt: str = Field(..., description="The initial story prompt")
    language: str = Field(default="english", description="Language for the book")
    writing_style: str = Field(default="descriptive", description="Writing style")
    genre: str = Field(default="fantasy", description="Book genre")
    target_audience: str = Field(default="young adults", description="Target audience")


class GenerateChapterContentRequest(BookIdRequest):
    """Request model for generating chapter content."""

    chapter_number: int = Field(
        ..., ge=1, description="Chapter number to generate (must be sequential)"
    )


# Response Models
class GenerateSummaryResponse(BookIdRequest):
    """Response model for story summary generation."""

    story_summary: str = Field(..., description="The generated story summary")


class GenerateTitleResponse(BookIdRequest):
    """Response model for title generation."""

    title: str = Field(..., description="The generated book title")


class GenerateCharactersResponse(BookIdRequest):
    """Response model for character generation."""

    characters: List[Character] = Field(..., description="The generated characters")


class GenerateChapterPlanResponse(BookIdRequest):
    """Response model for chapter plan generation."""

    chapters: List[Chapter] = Field(..., description="The generated chapter plan")


class GenerateChapterContentResponse(BookIdRequest):
    """Response model for chapter content generation."""

    chapter_number: int
    chapter_title: str
    content: str = Field(..., description="The generated chapter content")


class BookStateResponse(Book, BookIdRequest):
    """Response model for book state retrieval.

    Inherits all fields from Book and adds book_id for API context.
    """

    @classmethod
    def from_book(cls, book_id: UUID, book: Book) -> "BookStateResponse":
        """Create response from Book model."""
        return cls(book_id=book_id, **book.model_dump())


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
