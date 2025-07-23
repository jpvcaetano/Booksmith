import pytest
from pydantic import ValidationError

from booksmith.models import Character


class TestCharacter:
    """Tests for the Character model."""

    def test_create_minimal_character(self):
        """Test creating a character with minimal data."""
        character = Character()

        assert character.name == ""  # default
        assert character.background_story == ""  # default
        assert character.appearance == ""  # default
        assert character.personality == ""  # default
        assert character.role == ""  # default

    def test_create_full_character(self):
        """Test creating a character with all fields populated."""
        character = Character(
            name="Aragorn",
            background_story="A ranger from the North, heir to the throne of Gondor.",
            appearance="Tall and lean with dark hair and grey eyes.",
            personality="Noble, brave, and reluctant to accept his destiny.",
            role="Protagonist and future king",
        )

        assert character.name == "Aragorn"
        assert (
            character.background_story
            == "A ranger from the North, heir to the throne of Gondor."
        )
        assert character.appearance == "Tall and lean with dark hair and grey eyes."
        assert (
            character.personality
            == "Noble, brave, and reluctant to accept his destiny."
        )
        assert character.role == "Protagonist and future king"

    def test_character_defaults(self):
        """Test that all character fields default to empty strings."""
        character = Character()

        # All fields should be empty strings by default
        assert character.name == ""
        assert character.background_story == ""
        assert character.appearance == ""
        assert character.personality == ""
        assert character.role == ""

    def test_character_with_partial_data(self):
        """Test creating character with only some fields."""
        character = Character(
            name="Mystery Person", personality="Enigmatic and secretive"
        )

        assert character.name == "Mystery Person"
        assert character.personality == "Enigmatic and secretive"
        assert character.background_story == ""  # default
        assert character.appearance == ""  # default
        assert character.role == ""  # default

    def test_character_string_types(self):
        """Test that all fields accept string values."""
        character = Character(
            name="Test Name",
            background_story="Test Background",
            appearance="Test Appearance",
            personality="Test Personality",
            role="Test Role",
        )

        # All should be strings
        assert isinstance(character.name, str)
        assert isinstance(character.background_story, str)
        assert isinstance(character.appearance, str)
        assert isinstance(character.personality, str)
        assert isinstance(character.role, str)

    def test_character_serialization(self, sample_character):
        """Test that character can be serialized and deserialized."""
        # Test model_dump
        char_dict = sample_character.model_dump()
        assert isinstance(char_dict, dict)
        assert char_dict["name"] == "Test Hero"
        assert char_dict["personality"] == "Courageous, kind-hearted, and determined."

        # Test recreating from dict
        new_character = Character(**char_dict)
        assert new_character.name == sample_character.name
        assert new_character.background_story == sample_character.background_story
        assert new_character.appearance == sample_character.appearance
        assert new_character.personality == sample_character.personality
        assert new_character.role == sample_character.role

    def test_empty_strings_are_valid(self):
        """Test that empty strings are valid for all fields."""
        character = Character(
            name="", background_story="", appearance="", personality="", role=""
        )

        # Should not raise any validation errors
        assert character.name == ""
        assert character.background_story == ""

    def test_long_text_fields(self):
        """Test that fields can handle longer text."""
        long_text = "This is a very long description. " * 20

        character = Character(
            name="Long Description Character",
            background_story=long_text,
            appearance=long_text,
            personality=long_text,
            role=long_text,
        )

        assert len(character.background_story) > 100
        assert character.background_story.startswith("This is a very long")

    def test_invalid_field_types(self):
        """Test that invalid field types raise ValidationError."""
        with pytest.raises(ValidationError):
            Character(name=123)  # name should be string

        with pytest.raises(ValidationError):
            Character(background_story=["not", "a", "string"])

        with pytest.raises(ValidationError):
            Character(personality=None)
