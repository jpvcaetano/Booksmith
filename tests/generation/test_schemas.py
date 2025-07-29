import pytest

from booksmith.generation.schemas import (
    SCHEMAS,
    get_schema,
    get_schema_prompt_instruction,
)


class TestSchemas:
    """Tests for JSON schema functionality."""

    def test_get_schema_valid_names(self):
        """Test getting schemas by valid names."""
        # Test all available schemas
        schema_names = [
            "character",
            "chapter_plan",
            "story_summary",
            "title",
            "chapter_content",
        ]

        for name in schema_names:
            schema = get_schema(name)
            assert isinstance(schema, dict)
            assert "type" in schema
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema

    def test_get_schema_invalid_name(self):
        """Test getting schema with invalid name."""
        with pytest.raises(ValueError) as exc_info:
            get_schema("nonexistent_schema")

        assert "Unknown schema" in str(exc_info.value)
        assert "nonexistent_schema" in str(exc_info.value)

    def test_character_schema_structure(self):
        """Test character schema has expected structure."""
        schema = get_schema("character")

        # Should have characters array
        assert "characters" in schema["properties"]
        characters_schema = schema["properties"]["characters"]
        assert characters_schema["type"] == "array"

        # Check character item schema
        item_schema = characters_schema["items"]
        required_fields = ["name", "background_story", "appearance", "personality"]

        for field in required_fields:
            assert field in item_schema["properties"]
            assert item_schema["properties"][field]["type"] == "string"

        assert set(item_schema["required"]) >= set(required_fields)

    def test_chapter_plan_schema_structure(self):
        """Test chapter plan schema has expected structure."""
        schema = get_schema("chapter_plan")

        # Should have chapters array
        assert "chapters" in schema["properties"]
        chapters_schema = schema["properties"]["chapters"]
        assert chapters_schema["type"] == "array"

        # Check chapter item schema
        item_schema = chapters_schema["items"]
        required_fields = [
            "chapter_number",
            "title",
            "summary",
            "key_characters",
            "plot_points",
        ]

        for field in required_fields:
            assert field in item_schema["properties"]

        # Chapter number should be integer
        assert item_schema["properties"]["chapter_number"]["type"] == "integer"
        assert item_schema["properties"]["chapter_number"]["minimum"] == 1

        # Lists should be arrays
        assert item_schema["properties"]["key_characters"]["type"] == "array"
        assert item_schema["properties"]["plot_points"]["type"] == "array"

    def test_story_summary_schema_structure(self):
        """Test story summary schema has expected structure."""
        schema = get_schema("story_summary")

        assert "story_summary" in schema["properties"]
        summary_schema = schema["properties"]["story_summary"]

        assert summary_schema["type"] == "string"

    def test_title_schema_structure(self):
        """Test title schema has expected structure."""
        schema = get_schema("title")

        # Should have titles array and recommended_title
        assert "titles" in schema["properties"]
        assert "recommended_title" in schema["properties"]

        titles_schema = schema["properties"]["titles"]
        assert titles_schema["type"] == "array"

        recommended_schema = schema["properties"]["recommended_title"]
        assert recommended_schema["type"] == "string"

    def test_chapter_content_schema_structure(self):
        """Test chapter content schema has expected structure."""
        schema = get_schema("chapter_content")

        # Should have content as required field
        assert "content" in schema["properties"]
        assert "content" in schema["required"]

        content_schema = schema["properties"]["content"]
        assert content_schema["type"] == "string"

        # Optional fields should exist but not be required
        assert "continuity_notes" in schema["properties"]
        assert "character_development" in schema["properties"]
        assert "continuity_notes" not in schema["required"]
        assert "character_development" not in schema["required"]

    def test_all_schemas_valid_json_schema(self):
        """Test that all schemas are valid JSON schema format."""
        for schema_name in SCHEMAS.keys():
            schema = get_schema(schema_name)

            # Basic JSON schema validation
            assert isinstance(schema, dict)
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema
            assert "additionalProperties" in schema
            assert schema["additionalProperties"] is False  # Strict schema

    def test_get_schema_prompt_instruction(self):
        """Test schema prompt instruction generation."""
        instruction = get_schema_prompt_instruction("character")

        assert isinstance(instruction, str)
        assert "JSON" in instruction
        assert "schema" in instruction
        assert "valid JSON only" in instruction

        # Should contain the actual schema
        character_schema = get_schema("character")
        # The instruction should be substantial
        assert len(instruction) > 100

    def test_get_schema_prompt_instruction_all_schemas(self):
        """Test prompt instruction for all schema types."""
        for schema_name in SCHEMAS.keys():
            instruction = get_schema_prompt_instruction(schema_name)

            assert isinstance(instruction, str)
            assert "JSON" in instruction
            assert len(instruction) > 50

    def test_schemas_constant_available(self):
        """Test that SCHEMAS constant contains expected schemas."""
        expected_schemas = [
            "character",
            "chapter_plan",
            "story_summary",
            "title",
            "chapter_content",
        ]

        for schema_name in expected_schemas:
            assert schema_name in SCHEMAS

        # Should have exactly these schemas (no extra ones)
        assert set(SCHEMAS.keys()) == set(expected_schemas)

    def test_schema_constraints(self):
        """Test specific schema constraints and limits."""
        # Character schema constraints
        char_schema = get_schema("character")
        char_items = char_schema["properties"]["characters"]

        # Chapter plan constraints
        chapter_schema = get_schema("chapter_plan")
        chapter_items = chapter_schema["properties"]["chapters"]

        # Title constraints
        title_schema = get_schema("title")
        title_items = title_schema["properties"]["titles"]

    def test_string_field_constraints(self):
        """Test string field length constraints."""
        # Story summary should have length constraints
        summary_schema = get_schema("story_summary")
        summary_field = summary_schema["properties"]["story_summary"]

        # Chapter content should have length constraints
        content_schema = get_schema("chapter_content")
        content_field = content_schema["properties"]["content"]
