import pytest

from booksmith.generation.prompts import (
    generate_chapter_content_prompt,
    generate_chapter_plan_prompt,
    generate_character_prompt,
    generate_story_summary_prompt,
    generate_title_prompt,
)
from booksmith.models import Book, Chapter


class TestPrompts:
    """Tests for prompt generation functions."""

    def test_generate_story_summary_prompt(self, minimal_book):
        """Test story summary prompt generation."""
        prompt = generate_story_summary_prompt(minimal_book)

        # Check that key elements are present
        assert "A simple story" in prompt  # base_prompt
        assert "fantasy" in prompt  # default genre
        assert "english" in prompt  # default language
        assert "descriptive" in prompt  # default writing_style
        assert "young adults" in prompt  # default target_audience
        assert "Story Summary" in prompt
        assert "Instructions:" in prompt

    def test_generate_story_summary_prompt_custom(self):
        """Test story summary prompt with custom values."""
        book = Book(
            base_prompt="A space adventure",
            genre="science fiction",
            language="spanish",
            writing_style="minimalist",
            target_audience="adults",
        )

        prompt = generate_story_summary_prompt(book)

        assert "A space adventure" in prompt
        assert "science fiction" in prompt
        assert "spanish" in prompt
        assert "minimalist" in prompt
        assert "adults" in prompt

    def test_generate_character_prompt(self, sample_book):
        """Test character generation prompt."""
        prompt = generate_character_prompt(sample_book)

        # Check story summary is included
        assert sample_book.story_summary in prompt
        assert "fantasy" in prompt
        assert "young adults" in prompt
        assert "descriptive" in prompt
        assert "Characters:" in prompt
        assert "Character Name:" in prompt

    def test_generate_character_prompt_no_summary(self, minimal_book):
        """Test character prompt with empty story summary."""
        prompt = generate_character_prompt(minimal_book)

        # Should still generate prompt even with empty summary
        assert "fantasy" in prompt
        assert "Character Name:" in prompt

    def test_generate_chapter_plan_prompt(self, sample_book):
        """Test chapter plan generation prompt."""
        prompt = generate_chapter_plan_prompt(sample_book)

        # Check story summary and characters are included
        assert sample_book.story_summary in prompt
        assert "Alice Hero" in prompt  # character name
        assert "Bob Villain" in prompt  # character name
        assert "fantasy" in prompt
        assert "Chapter Outline:" in prompt
        assert "Chapter X:" in prompt

    def test_generate_chapter_plan_prompt_no_characters(self):
        """Test chapter plan prompt with no characters."""
        book = Book(base_prompt="Test story", story_summary="A simple tale")

        prompt = generate_chapter_plan_prompt(book)

        # Should still generate prompt
        assert "A simple tale" in prompt
        assert "Chapter Outline:" in prompt

    def test_generate_chapter_content_prompt(self, sample_book, sample_chapter):
        """Test chapter content generation prompt."""
        prompt = generate_chapter_content_prompt(sample_book, sample_chapter)

        # Check chapter details are included
        assert str(sample_chapter.chapter_number) in prompt
        assert sample_chapter.title in prompt
        assert sample_chapter.summary in prompt
        assert sample_book.story_summary in prompt
        assert "fantasy" in prompt
        assert "descriptive" in prompt
        assert "young adults" in prompt
        assert "english" in prompt

    def test_generate_chapter_content_prompt_first_chapter(self, sample_book):
        """Test chapter content prompt for first chapter."""
        first_chapter = Chapter(
            chapter_number=1, title="Beginning", summary="The start"
        )

        prompt = generate_chapter_content_prompt(sample_book, first_chapter)

        # Should indicate it's opening chapter
        assert "Opening chapter" in prompt
        assert "establish setting" in prompt

    def test_generate_chapter_content_prompt_last_chapter(self, sample_book):
        """Test chapter content prompt for final chapter."""
        final_chapter = Chapter(
            chapter_number=len(sample_book.chapters),
            title="The End",
            summary="The conclusion",
        )

        prompt = generate_chapter_content_prompt(sample_book, final_chapter)

        # Should indicate it's final chapter
        assert "Final chapter" in prompt
        assert "resolution and conclusion" in prompt

    def test_generate_title_prompt(self, sample_book):
        """Test title generation prompt."""
        prompt = generate_title_prompt(sample_book)

        # Check story summary and genre are included
        assert sample_book.story_summary in prompt
        assert "fantasy" in prompt
        assert "young adults" in prompt
        assert "Titles:" in prompt
        assert "Recommended Title:" in prompt

    def test_generate_title_prompt_no_summary(self, minimal_book):
        """Test title prompt with empty story summary."""
        prompt = generate_title_prompt(minimal_book)

        # Should still generate prompt
        assert "fantasy" in prompt
        assert "Titles:" in prompt

    def test_all_prompts_are_strings(self, sample_book, sample_chapter):
        """Test that all prompt functions return strings."""
        prompts = [
            generate_story_summary_prompt(sample_book),
            generate_character_prompt(sample_book),
            generate_chapter_plan_prompt(sample_book),
            generate_chapter_content_prompt(sample_book, sample_chapter),
            generate_title_prompt(sample_book),
        ]

        for prompt in prompts:
            assert isinstance(prompt, str)
            assert len(prompt) > 50  # Should be substantial

    def test_prompts_contain_instructions(self, sample_book, sample_chapter):
        """Test that prompts contain instruction sections."""
        prompts = [
            generate_story_summary_prompt(sample_book),
            generate_character_prompt(sample_book),
            generate_chapter_plan_prompt(sample_book),
            generate_chapter_content_prompt(sample_book, sample_chapter),
            generate_title_prompt(sample_book),
        ]

        # All prompts should contain some form of instructions
        for prompt in prompts:
            assert (
                "Instructions:" in prompt
                or "Guidelines:" in prompt
                or "Create" in prompt
                or "Generate" in prompt
            )
