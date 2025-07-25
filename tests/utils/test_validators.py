"""
Simple tests for the validators module.
"""

import pytest

from booksmith.models import Book, Chapter, Character
from booksmith.utils.validators import (
    STEP_DEPENDENCIES,
    DependencyValidationError,
    GenerationStep,
    validate_generation_step,
)


class TestGenerationStep:
    """Test the GenerationStep enum."""

    def test_generation_step_values(self):
        """Test that all expected steps exist."""
        assert GenerationStep.SUMMARY.value == "summary"
        assert GenerationStep.TITLE.value == "title"
        assert GenerationStep.CHARACTERS.value == "characters"
        assert GenerationStep.CHAPTER_PLAN.value == "chapter_plan"
        assert GenerationStep.CHAPTER_CONTENT.value == "chapter_content"


class TestDependencyValidationError:
    """Test the DependencyValidationError exception."""

    def test_error_creation(self):
        """Test creating the error with step and missing dependencies."""
        error = DependencyValidationError(GenerationStep.TITLE, ["story_summary"])
        assert error.step == GenerationStep.TITLE
        assert error.missing_dependencies == ["story_summary"]
        assert "Missing dependencies for title: story_summary" in str(error)

    def test_error_multiple_dependencies(self):
        """Test error with multiple missing dependencies."""
        error = DependencyValidationError(
            GenerationStep.CHAPTER_PLAN, ["story_summary", "characters"]
        )
        assert "story_summary, characters" in str(error)


class TestStepDependencies:
    """Test the STEP_DEPENDENCIES mapping."""

    def test_dependencies_mapping(self):
        """Test that all steps have expected dependencies."""
        assert STEP_DEPENDENCIES[GenerationStep.SUMMARY] == []
        assert STEP_DEPENDENCIES[GenerationStep.TITLE] == ["story_summary"]
        assert STEP_DEPENDENCIES[GenerationStep.CHARACTERS] == ["story_summary"]
        assert STEP_DEPENDENCIES[GenerationStep.CHAPTER_PLAN] == [
            "story_summary",
            "characters",
        ]
        assert STEP_DEPENDENCIES[GenerationStep.CHAPTER_CONTENT] == [
            "story_summary",
            "characters",
            "chapters",
        ]


class TestValidateGenerationStep:
    """Test the main validation function."""

    def test_summary_no_dependencies(self, minimal_book):
        """Test that summary generation has no dependencies."""
        # Should not raise any error
        validate_generation_step(minimal_book, GenerationStep.SUMMARY)

    def test_title_with_summary_success(self, minimal_book):
        """Test title generation with summary present."""
        minimal_book.story_summary = "A great story about adventures"
        validate_generation_step(minimal_book, GenerationStep.TITLE)

    def test_title_without_summary_fails(self, minimal_book):
        """Test title generation without summary fails."""
        with pytest.raises(DependencyValidationError) as exc_info:
            validate_generation_step(minimal_book, GenerationStep.TITLE)

        error = exc_info.value
        assert error.step == GenerationStep.TITLE
        assert "story_summary" in error.missing_dependencies

    def test_characters_with_summary_success(self, minimal_book):
        """Test character generation with summary present."""
        minimal_book.story_summary = "A story with interesting characters"
        validate_generation_step(minimal_book, GenerationStep.CHARACTERS)

    def test_characters_without_summary_fails(self, minimal_book):
        """Test character generation without summary fails."""
        with pytest.raises(DependencyValidationError) as exc_info:
            validate_generation_step(minimal_book, GenerationStep.CHARACTERS)

        assert exc_info.value.step == GenerationStep.CHARACTERS
        assert "story_summary" in exc_info.value.missing_dependencies

    def test_chapter_plan_with_dependencies_success(
        self, minimal_book, sample_character
    ):
        """Test chapter plan generation with all dependencies."""
        minimal_book.story_summary = "A story"
        minimal_book.characters = [sample_character]
        validate_generation_step(minimal_book, GenerationStep.CHAPTER_PLAN)

    def test_chapter_plan_missing_summary_fails(self, minimal_book, sample_character):
        """Test chapter plan generation without summary."""
        minimal_book.characters = [sample_character]

        with pytest.raises(DependencyValidationError) as exc_info:
            validate_generation_step(minimal_book, GenerationStep.CHAPTER_PLAN)

        assert "story_summary" in exc_info.value.missing_dependencies

    def test_chapter_plan_missing_characters_fails(self, minimal_book):
        """Test chapter plan generation without characters."""
        minimal_book.story_summary = "A story"

        with pytest.raises(DependencyValidationError) as exc_info:
            validate_generation_step(minimal_book, GenerationStep.CHAPTER_PLAN)

        assert "characters" in exc_info.value.missing_dependencies

    def test_chapter_plan_empty_characters_fails(self, minimal_book):
        """Test chapter plan generation with empty characters list."""
        minimal_book.story_summary = "A story"
        minimal_book.characters = []  # Empty list should fail

        with pytest.raises(DependencyValidationError) as exc_info:
            validate_generation_step(minimal_book, GenerationStep.CHAPTER_PLAN)

        assert "characters" in exc_info.value.missing_dependencies

    def test_chapter_content_with_dependencies_success(
        self, book_with_summary_and_characters_and_chapter_plan
    ):
        """Test chapter content generation with all dependencies."""
        chapter = book_with_summary_and_characters_and_chapter_plan.chapters[0]

        validate_generation_step(
            book_with_summary_and_characters_and_chapter_plan,
            GenerationStep.CHAPTER_CONTENT,
            chapter_number=1,
        )

    def test_chapter_content_missing_dependencies_fails(self, minimal_book):
        """Test chapter content generation without required dependencies."""
        # Create a chapter so it passes the chapter existence check first
        minimal_book.chapters = [Chapter(chapter_number=1, title="Chapter 1")]

        with pytest.raises(DependencyValidationError) as exc_info:
            validate_generation_step(
                minimal_book, GenerationStep.CHAPTER_CONTENT, chapter_number=1
            )

        error = exc_info.value
        assert "story_summary" in error.missing_dependencies
        assert "characters" in error.missing_dependencies

    def test_chapter_content_nonexistent_chapter_fails(
        self, minimal_book, sample_character
    ):
        """Test chapter content generation for non-existent chapter."""
        minimal_book.story_summary = "A story"
        minimal_book.characters = [sample_character]
        minimal_book.chapters = [Chapter(chapter_number=1, title="Chapter 1")]

        with pytest.raises(DependencyValidationError) as exc_info:
            validate_generation_step(
                minimal_book, GenerationStep.CHAPTER_CONTENT, chapter_number=2
            )

        assert "chapter_2_not_found" in exc_info.value.missing_dependencies

    def test_chapter_content_sequential_order_enforced(
        self, minimal_book, sample_character
    ):
        """Test that chapters must be written in sequential order."""
        minimal_book.story_summary = "A story"
        minimal_book.characters = [sample_character]
        minimal_book.chapters = [
            Chapter(chapter_number=1, title="Chapter 1", content=""),  # No content
            Chapter(
                chapter_number=2, title="Chapter 2", content=""
            ),  # Trying to write this
        ]

        with pytest.raises(DependencyValidationError) as exc_info:
            validate_generation_step(
                minimal_book, GenerationStep.CHAPTER_CONTENT, chapter_number=2
            )

        # Should fail because chapter 1 doesn't have content yet
        assert (
            "Chapter 1 must be written before chapter 2"
            in exc_info.value.missing_dependencies
        )

    def test_chapter_content_sequential_order_success(
        self, minimal_book, sample_character
    ):
        """Test sequential chapter writing works when previous chapters have content."""
        minimal_book.story_summary = "A story"
        minimal_book.characters = [sample_character]
        minimal_book.chapters = [
            Chapter(
                chapter_number=1, title="Chapter 1", content="Chapter 1 content"
            ),  # Has content
            Chapter(
                chapter_number=2, title="Chapter 2", content=""
            ),  # Can write this now
        ]

        # Should not raise error
        validate_generation_step(
            minimal_book, GenerationStep.CHAPTER_CONTENT, chapter_number=2
        )

    def test_empty_string_dependencies_fail(self, minimal_book):
        """Test that empty string dependencies are treated as missing."""
        minimal_book.story_summary = ""  # Empty string should fail

        with pytest.raises(DependencyValidationError):
            validate_generation_step(minimal_book, GenerationStep.TITLE)
