import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from booksmith.utils.epub_generator import (
    create_book_epub,
    create_book_info_text,
    create_epub_file,
    create_simple_text_export,
    format_chapter_content,
    sanitize_filename,
)


class TestSanitizeFilename:
    """Tests for filename sanitization."""

    def test_sanitize_normal_filename(self):
        """Test sanitizing a normal filename."""
        result = sanitize_filename("My Great Book")
        assert result == "My Great Book"

    def test_sanitize_invalid_characters(self):
        """Test sanitizing filename with invalid characters."""
        result = sanitize_filename('Book<>:"/\\|?*Title')
        assert result == "Book_________Title"

    def test_sanitize_long_filename(self):
        """Test sanitizing very long filename."""
        long_name = "A" * 250
        result = sanitize_filename(long_name)
        assert len(result) == 200

    def test_sanitize_with_dots_and_spaces(self):
        """Test sanitizing filename with leading/trailing dots and spaces."""
        result = sanitize_filename("  ..Book Title..  ")
        assert result == "Book Title"


class TestCreateBookEpub:
    """Tests for book EPUB creation."""

    def test_create_book_epub_success(self, sample_book, tmp_path):
        """Test successful EPUB creation."""
        with patch("booksmith.utils.epub_generator.create_epub_file") as mock_epub:
            with patch(
                "booksmith.utils.epub_generator.create_book_info_text"
            ) as mock_info:
                result_path = create_book_epub(sample_book, str(tmp_path))

                # Check folder was created
                book_folder = tmp_path / "The Magic Within"
                assert book_folder.exists()
                assert str(book_folder) == result_path

                # Check mocked functions were called
                mock_epub.assert_called_once()
                mock_info.assert_called_once()

    def test_create_book_epub_no_title(self, minimal_book, tmp_path):
        """Test EPUB creation with no title."""
        with patch("booksmith.utils.epub_generator.create_epub_file"):
            with patch("booksmith.utils.epub_generator.create_book_info_text"):
                result_path = create_book_epub(minimal_book, str(tmp_path))

                # Should use fallback name
                book_folder = tmp_path / "Untitled_Book"
                assert book_folder.exists()

    def test_create_book_epub_invalid_title(self, tmp_path):
        """Test EPUB creation with invalid characters in title."""
        from booksmith.models import Book

        book = Book(base_prompt="Test", title="Book<>Title")

        with patch("booksmith.utils.epub_generator.create_epub_file"):
            with patch("booksmith.utils.epub_generator.create_book_info_text"):
                result_path = create_book_epub(book, str(tmp_path))

                # Should sanitize title
                book_folder = tmp_path / "Book__Title"
                assert book_folder.exists()


class TestCreateEpubFile:
    """Tests for EPUB file creation."""

    def test_create_epub_file_success(self, sample_book, tmp_path):
        """Test successful EPUB file creation."""
        # Mock the entire ebooklib module
        mock_ebooklib = Mock()
        mock_epub = Mock()
        mock_ebooklib.epub = mock_epub

        # Setup mock EPUB objects
        mock_book = Mock()
        mock_epub.EpubBook.return_value = mock_book
        mock_epub.EpubHtml.return_value = Mock()
        mock_epub.EpubNav.return_value = Mock()
        mock_epub.EpubNcx.return_value = Mock()

        with patch.dict("sys.modules", {"ebooklib": mock_ebooklib}):
            epub_path = tmp_path / "test.epub"
            create_epub_file(sample_book, epub_path)

            # Verify EPUB book was configured
            mock_book.set_title.assert_called_with("The Magic Within")
            mock_book.set_language.assert_called_with("english")
            mock_book.add_author.assert_called_with("Booksmith AI")

            # Verify write was called
            mock_epub.write_epub.assert_called_once()

    def test_create_epub_file_import_error(self, sample_book, tmp_path):
        """Test EPUB creation when ebooklib is not available."""
        with patch.dict("sys.modules", {"ebooklib": None}):
            with patch("builtins.__import__", side_effect=ImportError("No module")):
                with pytest.raises(ImportError, match="ebooklib is required"):
                    epub_path = tmp_path / "test.epub"
                    create_epub_file(sample_book, epub_path)

    def test_create_epub_file_no_title(self, minimal_book, tmp_path):
        """Test EPUB creation with minimal book data."""
        # Mock the entire ebooklib module
        mock_ebooklib = Mock()
        mock_epub = Mock()
        mock_ebooklib.epub = mock_epub

        # Setup mock EPUB objects
        mock_book = Mock()
        mock_epub.EpubBook.return_value = mock_book
        mock_epub.EpubHtml.return_value = Mock()
        mock_epub.EpubNav.return_value = Mock()
        mock_epub.EpubNcx.return_value = Mock()

        with patch.dict("sys.modules", {"ebooklib": mock_ebooklib}):
            epub_path = tmp_path / "test.epub"
            create_epub_file(minimal_book, epub_path)

            # Verify defaults were used
            mock_book.set_title.assert_called_with("Untitled Book")
            mock_book.set_language.assert_called_with("english")
            mock_epub.write_epub.assert_called_once()


class TestFormatChapterContent:
    """Tests for chapter content formatting."""

    def test_format_single_paragraph(self):
        """Test formatting single paragraph."""
        content = "This is a single paragraph of text."
        result = format_chapter_content(content)

        assert result == "<p>This is a single paragraph of text.</p>"

    def test_format_multiple_paragraphs(self):
        """Test formatting multiple paragraphs."""
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = format_chapter_content(content)

        assert "<p>First paragraph.</p>" in result
        assert "<p>Second paragraph.</p>" in result
        assert "<p>Third paragraph.</p>" in result

    def test_format_with_line_breaks(self):
        """Test formatting content with line breaks within paragraphs."""
        content = "First line\nSecond line\n\nNew paragraph"
        result = format_chapter_content(content)

        assert "<p>First line Second line</p>" in result
        assert "<p>New paragraph</p>" in result

    def test_format_empty_content(self):
        """Test formatting empty content."""
        result = format_chapter_content("")
        assert result == ""

    def test_format_whitespace_only(self):
        """Test formatting content with only whitespace."""
        result = format_chapter_content("   \n\n   ")
        assert result == ""


class TestCreateBookInfoText:
    """Tests for book info text file creation."""

    def test_create_book_info_complete(self, sample_book, tmp_path):
        """Test creating book info with complete book data."""
        info_path = tmp_path / "book_info.txt"
        create_book_info_text(sample_book, info_path)

        assert info_path.exists()

        # Read and verify content
        content = info_path.read_text(encoding="utf-8")
        assert "The Magic Within" in content
        assert "fantasy" in content
        assert "Alice Hero" in content
        assert "Bob Villain" in content
        assert "Chapter 1: The Beginning" in content

    def test_create_book_info_minimal(self, minimal_book, tmp_path):
        """Test creating book info with minimal book data."""
        info_path = tmp_path / "book_info.txt"
        create_book_info_text(minimal_book, info_path)

        assert info_path.exists()

        content = info_path.read_text(encoding="utf-8")
        assert "Untitled Book" in content
        assert "fantasy" in content  # default genre

    def test_create_book_info_no_characters(self, tmp_path):
        """Test creating book info with no characters."""
        from booksmith.models import Book

        book = Book(base_prompt="Test", title="Test Book")

        info_path = tmp_path / "book_info.txt"
        create_book_info_text(book, info_path)

        content = info_path.read_text(encoding="utf-8")
        assert "Test Book" in content
        # Should not have characters section
        assert "CHARACTERS" not in content


class TestCreateSimpleTextExport:
    """Tests for simple text export functionality."""

    def test_create_text_export_success(self, sample_book, tmp_path):
        """Test successful text export creation."""
        result_path = create_simple_text_export(sample_book, str(tmp_path))

        # Check folder was created
        book_folder = tmp_path / "The Magic Within"
        assert book_folder.exists()
        assert str(book_folder) == result_path

        # Check text file was created
        text_file = book_folder / "The Magic Within.txt"
        assert text_file.exists()

        # Check content
        content = text_file.read_text(encoding="utf-8")
        assert "The Magic Within" in content
        assert "Chapter 1: The Beginning" in content
        assert "Chapter 1 content here..." in content

    def test_create_text_export_no_title(self, minimal_book, tmp_path):
        """Test text export with no title."""
        result_path = create_simple_text_export(minimal_book, str(tmp_path))

        # Should use fallback name
        book_folder = tmp_path / "Untitled_Book"
        assert book_folder.exists()

        text_file = book_folder / "untitled_book.txt"
        assert text_file.exists()

    def test_create_text_export_chapters_with_no_content(self, tmp_path):
        """Test text export with chapters that have no content."""
        from booksmith.models import Book, Chapter

        book = Book(
            base_prompt="Test",
            title="Test Book",
            chapters=[
                Chapter(chapter_number=1, title="Empty Chapter", content=""),
                Chapter(
                    chapter_number=2, title="Full Chapter", content="This has content"
                ),
            ],
        )

        result_path = create_simple_text_export(book, str(tmp_path))

        text_file = Path(result_path) / "Test Book.txt"
        content = text_file.read_text(encoding="utf-8")

        # Should only include chapters with content
        assert "Empty Chapter" not in content
        assert "Full Chapter" in content
        assert "This has content" in content

    def test_create_text_export_with_info_file(self, sample_book, tmp_path):
        """Test that text export also creates info file."""
        result_path = create_simple_text_export(sample_book, str(tmp_path))

        # Check both files exist
        book_folder = Path(result_path)
        text_file = book_folder / "The Magic Within.txt"
        info_file = book_folder / "book_info.txt"

        assert text_file.exists()
        assert info_file.exists()

        # Check info file has expected content
        info_content = info_file.read_text(encoding="utf-8")
        assert "Alice Hero" in info_content
        assert "CHARACTERS" in info_content
