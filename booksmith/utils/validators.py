"""
Centralized validation for book generation dependencies.
"""

from enum import Enum
from typing import Dict, List
from uuid import UUID

from fastapi import HTTPException

from ..models import Book


class GenerationStep(Enum):
    """Enumeration of book generation steps."""

    SUMMARY = "summary"
    TITLE = "title"
    CHARACTERS = "characters"
    CHAPTER_PLAN = "chapter_plan"
    CHAPTER_CONTENT = "chapter_content"


class DependencyValidationError(Exception):
    """Custom exception for dependency validation failures."""

    def __init__(self, step: GenerationStep, missing_dependencies: List[str]):
        self.step = step
        self.missing_dependencies = missing_dependencies
        super().__init__(
            f"Missing dependencies for {step.value}: {', '.join(missing_dependencies)}"
        )


# Dependency mapping: each step requires these book attributes to be present and non-empty
STEP_DEPENDENCIES: Dict[GenerationStep, List[str]] = {
    GenerationStep.SUMMARY: [],  # No dependencies
    GenerationStep.TITLE: ["story_summary"],
    GenerationStep.CHARACTERS: ["story_summary"],
    GenerationStep.CHAPTER_PLAN: ["story_summary", "characters"],
    GenerationStep.CHAPTER_CONTENT: ["story_summary", "characters", "chapters"],
}


def validate_generation_step(
    book: Book, step: GenerationStep, chapter_number: int = None
) -> None:
    """
    Validate that a book has all required dependencies for a generation step.

    Args:
        book: The book object to validate
        step: The generation step to validate for
        chapter_number: For chapter content, the chapter number being generated

    Raises:
        DependencyValidationError: If dependencies are missing
        HTTPException: For HTTP-specific validation errors (404, 400)
    """
    # Get required dependencies for this step
    required_deps = STEP_DEPENDENCIES.get(step, [])
    missing_deps = []

    # Check each required dependency
    for dep in required_deps:
        value = getattr(book, dep, None)

        # Check if dependency exists and is not empty
        if not value:
            missing_deps.append(dep)
        elif isinstance(value, list) and len(value) == 0:
            missing_deps.append(dep)

    # If we have missing dependencies, raise validation error
    if missing_deps:
        raise DependencyValidationError(step, missing_deps)

    # Special validation for chapter content
    if step == GenerationStep.CHAPTER_CONTENT and chapter_number is not None:
        # Additional validations for chapter content generation
        _validate_chapter_content_specifics(book, chapter_number, missing_deps)


def _validate_chapter_content_specifics(
    book: Book, chapter_number: int, missing_deps: List[str]
) -> None:
    """
    Perform chapter-specific validations for content generation.

    Args:
        book: The book object
        chapter_number: The chapter number being generated
        missing_deps: List to append any missing dependencies to
    """
    # Check if the requested chapter exists in the plan
    target_chapter = None
    for chapter in book.chapters:
        if chapter.chapter_number == chapter_number:
            target_chapter = chapter
            break

    if not target_chapter:
        raise DependencyValidationError(
            GenerationStep.CHAPTER_CONTENT, [f"chapter_{chapter_number}_not_found"]
        )

    # Raise in case the chapter already has content
    if target_chapter.content:
        raise DependencyValidationError(
            GenerationStep.CHAPTER_CONTENT,
            [f"Chapter {chapter_number} already has content"],
        )

    # Enforce sequential order - check that all previous chapters have content
    for chapter in book.chapters:
        if chapter.chapter_number < chapter_number and not chapter.content:
            raise DependencyValidationError(
                GenerationStep.CHAPTER_CONTENT,
                [
                    f"Chapter {chapter.chapter_number} must be written before chapter {chapter_number}"
                ],
            )
