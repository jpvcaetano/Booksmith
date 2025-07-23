import pytest

from booksmith.generation.validation import (
    PydanticValidator,
    StructuredOutputValidator,
    ValidationResult,
)
from booksmith.models import Chapter, Character


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_create_success_result(self):
        """Test creating a successful validation result."""
        result = ValidationResult(success=True, data="test_data")

        assert result.success is True
        assert result.data == "test_data"
        assert result.errors == []

    def test_create_error_result(self):
        """Test creating an error validation result."""
        errors = ["Error 1", "Error 2"]
        result = ValidationResult(success=False, errors=errors)

        assert result.success is False
        assert result.data is None
        assert result.errors == errors


class TestPydanticValidator:
    """Tests for PydanticValidator class."""

    def test_validate_characters_valid_data(self):
        """Test validating valid character data."""
        valid_data = {
            "characters": [
                {
                    "name": "Test Hero",
                    "background_story": "A brave warrior",
                    "appearance": "Tall and strong",
                    "personality": "Courageous",
                    "role": "Protagonist",
                }
            ]
        }

        result = PydanticValidator.validate_characters(valid_data)

        assert result.success is True
        assert len(result.data) == 1
        assert isinstance(result.data[0], Character)
        assert result.data[0].name == "Test Hero"

    def test_validate_characters_single_character(self):
        """Test validating single character (not in array)."""
        single_char = {
            "name": "Solo Hero",
            "background_story": "A lone warrior",
            "appearance": "Mysterious",
            "personality": "Independent",
        }

        result = PydanticValidator.validate_characters(single_char)

        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0].name == "Solo Hero"

    def test_validate_characters_invalid_data(self):
        """Test validation failure with invalid character data."""
        invalid_data = {
            "characters": [
                {"name": 123, "background_story": None}  # Invalid type  # Invalid type
            ]
        }

        result = PydanticValidator.validate_characters(invalid_data)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Character 0:" in result.errors[0]

    def test_validate_characters_missing_required_fields(self):
        """Test validation with missing fields (should use defaults)."""
        incomplete_data = {
            "characters": [
                {
                    "name": "Incomplete Hero"
                    # Missing other fields - should use defaults
                }
            ]
        }

        result = PydanticValidator.validate_characters(incomplete_data)

        assert result.success is True
        assert result.data[0].name == "Incomplete Hero"
        assert result.data[0].background_story == ""  # Default value
        assert result.data[0].appearance == ""  # Default value

    def test_validate_chapters_valid_data(self):
        """Test validating valid chapter data."""
        valid_data = {
            "chapters": [
                {
                    "chapter_number": 1,
                    "title": "The Beginning",
                    "summary": "The story starts",
                    "key_characters": ["Hero"],
                    "plot_points": ["Inciting incident"],
                    "content": "",
                }
            ]
        }

        result = PydanticValidator.validate_chapters(valid_data)

        assert result.success is True
        assert len(result.data) == 1
        assert isinstance(result.data[0], Chapter)
        assert result.data[0].chapter_number == 1
        assert result.data[0].title == "The Beginning"

    def test_validate_chapters_invalid_data(self):
        """Test validation failure with invalid chapter data."""
        invalid_data = {
            "chapters": [
                {
                    "chapter_number": "invalid",  # Should be int
                    "title": 123,  # Should be str
                }
            ]
        }

        result = PydanticValidator.validate_chapters(invalid_data)

        assert result.success is False
        assert len(result.errors) > 0
        assert "Chapter 1:" in result.errors[0]

    def test_validate_chapters_missing_fields(self):
        """Test validation with missing fields (should use defaults)."""
        data_with_defaults = {
            "chapters": [
                {
                    "title": "Chapter with defaults"
                    # Missing other fields - should use defaults
                }
            ]
        }

        result = PydanticValidator.validate_chapters(data_with_defaults)

        assert result.success is True
        assert result.data[0].title == "Chapter with defaults"
        assert result.data[0].chapter_number == 0  # Default value
        assert result.data[0].summary == ""  # Default value


class TestStructuredOutputValidator:
    """Tests for StructuredOutputValidator class."""

    def test_validate_story_summary_dict(self):
        """Test validating story summary from dict."""
        response = {"story_summary": "A compelling tale of adventure and discovery."}

        result = StructuredOutputValidator.validate_and_parse(response, "story_summary")

        assert result.success is True
        assert result.data == "A compelling tale of adventure and discovery."

    def test_validate_story_summary_string(self):
        """Test validating story summary from JSON string."""
        import json

        response = json.dumps({"story_summary": "A great adventure story."})

        result = StructuredOutputValidator.validate_and_parse(response, "story_summary")

        assert result.success is True
        assert result.data == "A great adventure story."

    def test_validate_story_summary_invalid(self):
        """Test handling invalid story summary."""
        response = {"wrong_field": "content"}

        result = StructuredOutputValidator.validate_and_parse(response, "story_summary")

        assert result.success is False
        assert "Missing 'story_summary' field" in result.errors

    def test_validate_story_summary_too_short(self):
        """Test handling too short story summary."""
        response = {"story_summary": "Short"}

        result = StructuredOutputValidator.validate_and_parse(response, "story_summary")

        assert result.success is False
        assert "too short" in result.errors[0]

    def test_validate_title_recommended(self):
        """Test validating title with recommended_title field."""
        response = {
            "titles": ["Title 1", "Title 2", "Title 3"],
            "recommended_title": "Title 2",
        }

        result = StructuredOutputValidator.validate_and_parse(response, "title")

        assert result.success is True
        assert result.data == "Title 2"

    def test_validate_title_first_from_list(self):
        """Test validating title using first from titles list."""
        response = {"titles": ["First Title", "Second Title"]}

        result = StructuredOutputValidator.validate_and_parse(response, "title")

        assert result.success is True
        assert result.data == "First Title"

    def test_validate_title_invalid(self):
        """Test handling invalid title response."""
        response = {"wrong_field": "value"}

        result = StructuredOutputValidator.validate_and_parse(response, "title")

        assert result.success is False
        assert "No title found" in result.errors[0]

    def test_validate_chapter_content_dict(self):
        """Test validating chapter content from dict."""
        response = {
            "content": "This is substantial chapter content with enough text to pass validation."
        }

        result = StructuredOutputValidator.validate_and_parse(
            response, "chapter_content"
        )

        assert result.success is True
        assert "substantial chapter content" in result.data

    def test_validate_chapter_content_too_short(self):
        """Test handling too short chapter content."""
        response = {"content": "Short"}

        result = StructuredOutputValidator.validate_and_parse(
            response, "chapter_content"
        )

        assert result.success is False
        assert "too short" in result.errors[0]

    def test_validate_invalid_json_string(self):
        """Test handling invalid JSON string."""
        invalid_json = '{"invalid": json}'

        result = StructuredOutputValidator.validate_and_parse(
            invalid_json, "story_summary"
        )

        assert result.success is False
        assert "Invalid JSON" in result.errors[0]

    def test_validate_unknown_type(self):
        """Test handling unknown validation type."""
        response = {"data": "value"}

        result = StructuredOutputValidator.validate_and_parse(response, "unknown_type")

        assert result.success is False
        assert "Unknown validation type" in result.errors[0]

    def test_validate_character_integration(self, sample_characters_response):
        """Test character validation through StructuredOutputValidator."""
        result = StructuredOutputValidator.validate_and_parse(
            sample_characters_response, "character"
        )

        assert result.success is True
        assert len(result.data) == 2
        assert all(isinstance(char, Character) for char in result.data)

    def test_validate_chapter_plan_integration(self, sample_chapter_plan_response):
        """Test chapter plan validation through StructuredOutputValidator."""
        result = StructuredOutputValidator.validate_and_parse(
            sample_chapter_plan_response, "chapter_plan"
        )

        assert result.success is True
        assert len(result.data) == 2
        assert all(isinstance(chapter, Chapter) for chapter in result.data)
