import json

import pytest

from booksmith.generation.parsers import ResponseParser, StructuredResponseParser
from booksmith.models import Chapter, Character


class TestResponseParser:
    """Tests for regex-based response parsing."""

    def test_parse_story_summary_basic(self):
        """Test basic story summary parsing."""
        response = "This is a comprehensive story about a hero's journey."
        result = ResponseParser.parse_story_summary(response)

        assert result == response.strip()

    def test_parse_story_summary_with_header(self):
        """Test story summary parsing with header."""
        response = """
        **Story Summary:**
        This is a comprehensive story about a hero's journey through magical lands.
        
        Additional content here.
        """
        result = ResponseParser.parse_story_summary(response)

        assert "hero's journey" in result
        assert "magical lands" in result

    def test_parse_characters_structured(self, sample_characters_text_response):
        """Test character parsing from structured text."""
        result = ResponseParser.parse_characters(sample_characters_text_response)

        assert len(result) == 2
        assert result[0].name == "Alice Hero"
        assert result[1].name == "Bob Villain"
        assert "mage" in result[0].background_story
        assert "sorcerer" in result[1].background_story

    def test_parse_characters_fallback(self):
        """Test character parsing fallback method."""
        response = """
        ALICE HERO
        A brave young mage with special powers.
        
        BOB VILLAIN
        An evil sorcerer seeking destruction.
        """
        result = ResponseParser.parse_characters(response)

        assert len(result) >= 1
        # Should create at least one character
        assert any("ALICE" in char.name for char in result)

    def test_parse_chapter_plan_structured(self, sample_chapter_plan_text_response):
        """Test chapter plan parsing from structured text."""
        result = ResponseParser.parse_chapter_plan(sample_chapter_plan_text_response)

        assert len(result) == 2
        assert result[0].chapter_number == 1
        assert result[0].title == "The Beginning"
        assert result[1].chapter_number == 2
        assert result[1].title == "The Challenge"

    def test_parse_chapter_plan_fallback(self):
        """Test chapter plan fallback parsing."""
        response = """
        # Chapter 1: The Start
        This is where everything begins.
        
        # Chapter 2: The Middle
        The plot thickens here.
        """
        result = ResponseParser.parse_chapter_plan(response)

        assert len(result) >= 1
        # Should extract chapter titles
        assert any("Start" in ch.title for ch in result)

    def test_parse_chapter_content_basic(self):
        """Test basic chapter content parsing."""
        content = "It was a dark and stormy night when the adventure began..."
        result = ResponseParser.parse_chapter_content(content)

        assert result == content.strip()

    def test_parse_chapter_content_with_header(self):
        """Test chapter content parsing with header."""
        response = """
        **Chapter Content:**
        It was a dark and stormy night when the adventure began.
        The hero walked through the forest, unaware of the dangers ahead.
        """
        result = ResponseParser.parse_chapter_content(response)

        assert "dark and stormy night" in result
        assert "forest" in result

    def test_parse_title_basic(self):
        """Test basic title parsing."""
        response = "The Great Adventure"
        result = ResponseParser.parse_title(response)

        assert result == "The Great Adventure"

    def test_parse_title_with_recommendations(self):
        """Test title parsing with recommendations."""
        response = """
        **Recommended Title:** The Magic Within
        
        Other options:
        1. The Awakening
        2. Powers Unleashed
        """
        result = ResponseParser.parse_title(response)

        assert result == "The Magic Within"

    def test_parse_title_numbered_list(self):
        """Test title parsing from numbered list."""
        response = """
        1. The Great Adventure
        2. The Hero's Journey
        3. The Final Quest
        """
        result = ResponseParser.parse_title(response)

        assert result == "The Great Adventure"

    def test_parse_empty_responses(self):
        """Test parsing empty or minimal responses."""
        # Empty story summary should return the input
        assert ResponseParser.parse_story_summary("") == ""

        # Empty characters should return empty list
        assert ResponseParser.parse_characters("") == []

        # Empty chapters should return empty list
        assert ResponseParser.parse_chapter_plan("") == []

        # Empty title should return fallback
        assert ResponseParser.parse_title("") == "Untitled Book"


class TestStructuredResponseParser:
    """Tests for structured JSON response parsing with fallback."""

    def test_parse_story_summary_json(self, sample_story_summary_response):
        """Test structured story summary parsing."""
        result = StructuredResponseParser.parse_story_summary(
            sample_story_summary_response
        )

        assert "Alice" in result
        assert "magical powers" in result

    def test_parse_story_summary_fallback(self):
        """Test story summary fallback to regex parsing."""
        text_response = "A simple story about a hero."
        result = StructuredResponseParser.parse_story_summary(text_response)

        assert result == text_response

    def test_parse_characters_json(self, sample_characters_response):
        """Test structured character parsing."""
        result = StructuredResponseParser.parse_characters(sample_characters_response)

        assert len(result) == 2
        assert isinstance(result[0], Character)
        assert result[0].name == "Alice Hero"
        assert result[1].name == "Bob Villain"

    def test_parse_characters_fallback(self, sample_characters_text_response):
        """Test character parsing fallback to regex."""
        result = StructuredResponseParser.parse_characters(
            sample_characters_text_response
        )

        assert len(result) == 2
        assert result[0].name == "Alice Hero"

    def test_parse_chapter_plan_json(self, sample_chapter_plan_response):
        """Test structured chapter plan parsing."""
        result = StructuredResponseParser.parse_chapter_plan(
            sample_chapter_plan_response
        )

        assert len(result) == 2
        assert isinstance(result[0], Chapter)
        assert result[0].chapter_number == 1
        assert result[0].title == "The Beginning"
        assert "Alice Hero" in result[0].key_characters
        assert "Discovery of powers" in result[0].plot_points

    def test_parse_chapter_plan_fallback(self, sample_chapter_plan_text_response):
        """Test chapter plan fallback to regex parsing."""
        result = StructuredResponseParser.parse_chapter_plan(
            sample_chapter_plan_text_response
        )

        assert len(result) == 2
        assert result[0].title == "The Beginning"

    def test_parse_chapter_content_json(self, sample_chapter_content_response):
        """Test structured chapter content parsing."""
        result = StructuredResponseParser.parse_chapter_content(
            sample_chapter_content_response
        )

        assert "dark and stormy night" in result
        assert "magical abilities" in result

    def test_parse_chapter_content_enhanced_json(self):
        """Test chapter content with enhanced metadata."""
        response = {
            "content": "The chapter content here... "
            * 20,  # Make content longer to pass validation
            "continuity_notes": "Connects to previous chapter",
            "character_development": "Hero grows stronger",
        }

        result = StructuredResponseParser.parse_chapter_content(response)
        assert "The chapter content here..." in result

    def test_parse_title_json(self, sample_title_response):
        """Test structured title parsing."""
        result = StructuredResponseParser.parse_title(sample_title_response)

        assert result == "The Magic Within"

    def test_parse_title_json_titles_only(self):
        """Test title parsing when only titles array exists."""
        response = {"titles": ["First Title", "Second Title", "Third Title"]}

        result = StructuredResponseParser.parse_title(response)
        assert result == "First Title"

    def test_parse_invalid_json_responses(self):
        """Test handling of invalid JSON responses."""
        invalid_json = '{"invalid": json format'

        # Should fall back to regex parsing
        story_result = StructuredResponseParser.parse_story_summary(invalid_json)
        assert isinstance(story_result, str)

        char_result = StructuredResponseParser.parse_characters(invalid_json)
        assert isinstance(char_result, list)

    def test_parse_malformed_structured_responses(self):
        """Test handling of malformed structured responses."""
        # Missing required fields
        malformed = {"wrong_field": "value"}

        story_result = StructuredResponseParser.parse_story_summary(malformed)
        assert isinstance(story_result, str)

        char_result = StructuredResponseParser.parse_characters(malformed)
        assert isinstance(char_result, list)
