"""
Validation utilities for structured LLM outputs using Pydantic models.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel, ValidationError

from ..models import Book, Chapter, Character

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class ValidationResult:
    """Result of validation."""

    def __init__(
        self,
        success: bool,
        data: Any = None,
        errors: List[str] = None,
    ):
        self.success = success
        self.data = data
        self.errors = errors or []


class PydanticValidator:
    """Validator that uses Pydantic models for structured data validation."""

    @staticmethod
    def validate_characters(
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> ValidationResult:
        """Validate character data against Character model."""
        try:
            # Handle both single character and character list formats
            if isinstance(data, dict):
                if "characters" in data:
                    char_list = data["characters"]
                else:
                    # Assume it's a single character
                    char_list = [data]
            else:
                char_list = data

            validated_characters = []
            errors = []

            for i, char_data in enumerate(char_list):
                try:
                    character = Character.model_validate(char_data)
                    validated_characters.append(character)
                except ValidationError as e:
                    errors.append(f"Character {i}: {str(e)}")
                    logger.error(f"Failed to validate character {i}: {e}")

            if errors:
                return ValidationResult(success=False, errors=errors)

            return ValidationResult(success=True, data=validated_characters)

        except Exception as e:
            return ValidationResult(
                success=False, errors=[f"Validation failed: {str(e)}"]
            )

    @staticmethod
    def validate_chapters(
        data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> ValidationResult:
        """Validate chapter data against Chapter model."""
        try:
            # Handle both single chapter and chapter list formats
            if isinstance(data, dict):
                if "chapters" in data:
                    chapter_list = data["chapters"]
                else:
                    chapter_list = [data]
            else:
                chapter_list = data

            validated_chapters = []
            errors = []

            for i, chapter_data in enumerate(chapter_list):
                try:
                    chapter = Chapter.model_validate(chapter_data)
                    validated_chapters.append(chapter)
                except ValidationError as e:
                    errors.append(f"Chapter {i + 1}: {str(e)}")
                    logger.error(f"Failed to validate chapter {i + 1}: {e}")

            if errors:
                return ValidationResult(success=False, errors=errors)

            return ValidationResult(success=True, data=validated_chapters)

        except Exception as e:
            return ValidationResult(
                success=False, errors=[f"Validation failed: {str(e)}"]
            )


class StructuredOutputValidator:
    """High-level validator that combines JSON schema and Pydantic validation."""

    @staticmethod
    def validate_and_parse(
        response: Union[str, Dict[str, Any]], expected_type: str
    ) -> ValidationResult:
        """Validate and parse response based on expected type."""

        # First, ensure we have a dict
        if isinstance(response, str):
            try:
                response = json.loads(response)
            except json.JSONDecodeError as e:
                return ValidationResult(
                    success=False, errors=[f"Invalid JSON: {str(e)}"]
                )

        # Validate based on type
        if expected_type == "character":
            return PydanticValidator.validate_characters(response)
        elif expected_type == "chapter_plan":
            return PydanticValidator.validate_chapters(response)
        elif expected_type == "story_summary":
            if isinstance(response, dict) and "story_summary" in response:
                summary = response["story_summary"]
                if isinstance(summary, str) and len(summary.strip()) > 10:
                    return ValidationResult(success=True, data=summary.strip())
                else:
                    return ValidationResult(
                        success=False, errors=["Story summary too short or invalid"]
                    )
            else:
                return ValidationResult(
                    success=False, errors=["Missing 'story_summary' field"]
                )
        elif expected_type == "title":
            if isinstance(response, dict):
                if "recommended_title" in response:
                    title = response["recommended_title"]
                elif "titles" in response and response["titles"]:
                    title = response["titles"][0]
                else:
                    return ValidationResult(
                        success=False, errors=["No title found in response"]
                    )

                if isinstance(title, str) and len(title.strip()) > 3:
                    return ValidationResult(success=True, data=title.strip())
                else:
                    return ValidationResult(
                        success=False, errors=["Title too short or invalid"]
                    )
            else:
                return ValidationResult(
                    success=False, errors=["Invalid title response format"]
                )
        elif expected_type == "chapter_content":
            if isinstance(response, dict) and "content" in response:
                content = response["content"]
                if isinstance(content, str) and len(content.strip()) > 50:
                    return ValidationResult(success=True, data=content.strip())
                else:
                    return ValidationResult(
                        success=False, errors=["Chapter content too short"]
                    )
            else:
                return ValidationResult(
                    success=False, errors=["Missing 'content' field"]
                )
        else:
            return ValidationResult(
                success=False, errors=[f"Unknown validation type: {expected_type}"]
            )
