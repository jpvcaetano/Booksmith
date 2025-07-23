import pytest
from pydantic import ValidationError

from booksmith.models import Book, Chapter, Character


class TestBook:
    """Tests for the Book model."""

    def test_create_minimal_book(self):
        """Test creating a book with minimal required data."""
        book = Book(base_prompt="A simple story")

        assert book.base_prompt == "A simple story"
        assert book.language == "english"  # default
        assert book.writing_style == "descriptive"  # default
        assert book.genre == "fantasy"  # default
        assert book.target_audience == "young adults"  # default
        assert book.title == ""  # default
        assert book.story_summary == ""  # default
        assert book.characters == []  # default
        assert book.chapters == []  # default

    def test_create_full_book(self, sample_characters, sample_chapters):
        """Test creating a book with all fields populated."""
        book = Book(
            base_prompt="A magical adventure",
            language="spanish",
            writing_style="literary",
            genre="science fiction",
            target_audience="adults",
            title="The Great Adventure",
            story_summary="An epic tale of discovery",
            characters=sample_characters,
            chapters=sample_chapters,
        )

        assert book.base_prompt == "A magical adventure"
        assert book.language == "spanish"
        assert book.writing_style == "literary"
        assert book.genre == "science fiction"
        assert book.target_audience == "adults"
        assert book.title == "The Great Adventure"
        assert book.story_summary == "An epic tale of discovery"
        assert len(book.characters) == 2
        assert len(book.chapters) == 2
        assert book.characters[0].name == "Alice Hero"
        assert book.chapters[0].title == "The Beginning"

    def test_book_defaults(self):
        """Test that book defaults are applied correctly."""
        book = Book(base_prompt="Test")

        # Check all default values
        assert book.language == "english"
        assert book.writing_style == "descriptive"
        assert book.genre == "fantasy"
        assert book.target_audience == "young adults"
        assert book.characters == []
        assert book.chapters == []

    def test_book_missing_base_prompt(self):
        """Test that ValidationError is raised when base_prompt is missing."""
        with pytest.raises(ValidationError) as exc_info:
            Book()

        assert "base_prompt" in str(exc_info.value)

    def test_book_empty_base_prompt(self):
        """Test that empty base_prompt is accepted."""
        book = Book(base_prompt="")
        assert book.base_prompt == ""

    def test_book_with_characters(self, sample_character):
        """Test adding characters to book."""
        book = Book(base_prompt="Test")
        book.characters = [sample_character]

        assert len(book.characters) == 1
        assert book.characters[0].name == "Test Hero"

    def test_book_with_chapters(self, sample_chapter):
        """Test adding chapters to book."""
        book = Book(base_prompt="Test")
        book.chapters = [sample_chapter]

        assert len(book.chapters) == 1
        assert book.chapters[0].title == "The Beginning"

    def test_book_serialization(self, sample_book):
        """Test that book can be serialized and deserialized."""
        # Test model_dump
        book_dict = sample_book.model_dump()
        assert isinstance(book_dict, dict)
        assert book_dict["title"] == "The Magic Within"
        assert len(book_dict["characters"]) == 2

        # Test recreating from dict
        new_book = Book(**book_dict)
        assert new_book.title == sample_book.title
        assert new_book.base_prompt == sample_book.base_prompt
        assert len(new_book.characters) == len(sample_book.characters)
