import pytest
from pydantic import ValidationError

from booksmith.models import Chapter


class TestChapter:
    """Tests for the Chapter model."""

    def test_create_minimal_chapter(self):
        """Test creating a chapter with minimal data."""
        chapter = Chapter()

        assert chapter.chapter_number == 0  # default
        assert chapter.title == ""  # default
        assert chapter.summary == ""  # default
        assert chapter.key_characters == []  # default
        assert chapter.plot_points == []  # default
        assert chapter.content == ""  # default

    def test_create_full_chapter(self):
        """Test creating a chapter with all fields populated."""
        chapter = Chapter(
            chapter_number=5,
            title="The Epic Battle",
            summary="The final confrontation between good and evil",
            key_characters=["Hero", "Villain", "Mentor"],
            plot_points=["Battle begins", "Hero struggles", "Victory achieved"],
            content="The battle raged on through the night...",
        )

        assert chapter.chapter_number == 5
        assert chapter.title == "The Epic Battle"
        assert chapter.summary == "The final confrontation between good and evil"
        assert chapter.key_characters == ["Hero", "Villain", "Mentor"]
        assert chapter.plot_points == [
            "Battle begins",
            "Hero struggles",
            "Victory achieved",
        ]
        assert chapter.content == "The battle raged on through the night..."

    def test_chapter_number_types(self):
        """Test that chapter_number accepts integers."""
        chapter = Chapter(chapter_number=1)
        assert chapter.chapter_number == 1
        assert isinstance(chapter.chapter_number, int)

    def test_invalid_chapter_number_type(self):
        """Test that invalid chapter_number types raise ValidationError."""
        with pytest.raises(ValidationError):
            Chapter(chapter_number="not_a_number")

        with pytest.raises(ValidationError):
            Chapter(chapter_number=1.5)

    def test_empty_lists_default(self):
        """Test that lists default to empty."""
        chapter = Chapter()

        assert chapter.key_characters == []
        assert chapter.plot_points == []

        # Test they're independent instances
        chapter.key_characters.append("Test")
        chapter2 = Chapter()
        assert chapter2.key_characters == []

    def test_string_fields_default(self):
        """Test that string fields default to empty strings."""
        chapter = Chapter()

        assert chapter.title == ""
        assert chapter.summary == ""
        assert chapter.content == ""

    def test_chapter_serialization(self, sample_chapter):
        """Test that chapter can be serialized and deserialized."""
        # Test model_dump
        chapter_dict = sample_chapter.model_dump()
        assert isinstance(chapter_dict, dict)
        assert chapter_dict["title"] == "The Beginning"
        assert chapter_dict["chapter_number"] == 1

        # Test recreating from dict
        new_chapter = Chapter(**chapter_dict)
        assert new_chapter.title == sample_chapter.title
        assert new_chapter.chapter_number == sample_chapter.chapter_number
        assert new_chapter.key_characters == sample_chapter.key_characters

    def test_modify_lists(self):
        """Test that list fields can be modified."""
        chapter = Chapter()

        # Add characters
        chapter.key_characters.append("Hero")
        chapter.key_characters.append("Villain")
        assert len(chapter.key_characters) == 2

        # Add plot points
        chapter.plot_points.extend(["Event 1", "Event 2"])
        assert len(chapter.plot_points) == 2

    def test_chapter_with_content(self):
        """Test chapter with substantial content."""
        content = "This is a long chapter with lots of content. " * 10
        chapter = Chapter(chapter_number=1, title="Long Chapter", content=content)

        assert len(chapter.content) > 100
        assert chapter.content.startswith("This is a long chapter")
