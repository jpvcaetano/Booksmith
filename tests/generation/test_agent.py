from unittest.mock import MagicMock, Mock, patch

import pytest

from booksmith.generation.agent import WritingAgent
from booksmith.generation.openai import LLMConfig
from booksmith.models import Book, Chapter, Character
from booksmith.utils.validators import DependencyValidationError


class TestWritingAgent:
    """Tests for WritingAgent class."""

    def test_initialization_default_config(self):
        """Test agent initialization with default config."""
        with patch("booksmith.generation.agent.OpenAIBackend"):
            agent = WritingAgent()

            assert agent.llm_config.model_name == "gpt-4.1"
            assert agent.llm_config.max_tokens == 1000
            assert agent.llm_config.temperature == 0.7

    def test_initialization_custom_config(self, llm_config):
        """Test agent initialization with custom config."""
        with patch("booksmith.generation.agent.OpenAIBackend"):
            agent = WritingAgent(llm_config)

            assert agent.llm_config == llm_config

    @patch("booksmith.generation.agent.OpenAIBackend")
    def test_backend_initialization_success(self, mock_backend_class, llm_config):
        """Test successful backend initialization."""
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend_class.return_value = mock_backend

        agent = WritingAgent(llm_config)

        assert agent.llm_backend == mock_backend
        mock_backend_class.assert_called_with(llm_config)

    @patch("booksmith.generation.agent.OpenAIBackend")
    def test_backend_initialization_failure(self, mock_backend_class, llm_config):
        """Test backend initialization failure."""
        mock_backend_class.side_effect = Exception("Backend failed")

        agent = WritingAgent(llm_config)

        assert agent.llm_backend is None

    @patch("booksmith.generation.agent.OpenAIBackend")
    def test_backend_not_available(self, mock_backend_class, llm_config):
        """Test backend not available."""
        mock_backend = Mock()
        mock_backend.is_available.return_value = False
        mock_backend_class.return_value = mock_backend

        agent = WritingAgent(llm_config)

        assert agent.llm_backend is None

    def test_generate_text_success(self, llm_config):
        """Test successful text generation."""
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.generate.return_value = "Generated text"
        agent.llm_backend = mock_backend

        result = agent._generate_text("Test prompt")

        assert result == "Generated text"
        mock_backend.generate.assert_called_once_with("Test prompt")

    def test_generate_text_no_backend(self, llm_config):
        """Test text generation without backend."""
        agent = WritingAgent(llm_config)
        agent.llm_backend = None

        with pytest.raises(Exception, match="No LLM backend available"):
            agent._generate_text("Test prompt")

    def test_generate_text_backend_error(self, llm_config):
        """Test text generation with backend error."""
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.generate.side_effect = Exception("Generation failed")
        agent.llm_backend = mock_backend

        with pytest.raises(Exception, match="Generation failed"):
            agent._generate_text("Test prompt")

    def test_generate_structured_success(self, llm_config):
        """Test successful structured generation."""
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.supports_structured_output.return_value = True
        mock_backend.generate_structured.return_value = {"result": "data"}
        agent.llm_backend = mock_backend

        with patch("booksmith.generation.agent.get_schema") as mock_get_schema:
            mock_get_schema.return_value = {"schema": "definition"}

            result = agent._generate_structured("Test prompt", "test_schema")

            assert result == {"result": "data"}
            mock_backend.generate_structured.assert_called_once()

    def test_generate_structured_fallback(self, llm_config):
        """Test structured generation fallback to regular generation."""
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.supports_structured_output.return_value = False
        mock_backend.generate.return_value = "Fallback text"
        agent.llm_backend = mock_backend

        result = agent._generate_structured("Test prompt", "test_schema")

        assert result == "Fallback text"
        mock_backend.generate.assert_called_once_with("Test prompt")

    def test_generate_story_summary(self, minimal_book, llm_config):
        """Test story summary generation."""
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.supports_structured_output.return_value = True
        mock_backend.generate_structured.return_value = {
            "story_summary": "A great adventure story"
        }
        agent.llm_backend = mock_backend

        with patch("booksmith.generation.agent.get_schema"):
            with patch(
                "booksmith.generation.agent.StructuredResponseParser"
            ) as mock_parser:
                mock_parser.parse_story_summary.return_value = "A great adventure story"

                agent.generate_story_summary(minimal_book)

                assert minimal_book.story_summary == "A great adventure story"

    def test_generate_story_summary_error(self, minimal_book, llm_config):
        """Test story summary generation error handling."""
        agent = WritingAgent(llm_config)
        agent.llm_backend = None

        with pytest.raises(Exception, match="No LLM backend available"):
            agent.generate_story_summary(minimal_book)

    def test_generate_characters(self, minimal_book, llm_config):
        """Test character generation."""
        minimal_book.story_summary = "A story with heroes"
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.supports_structured_output.return_value = True
        mock_characters = [
            Character(name="Hero", personality="Brave"),
            Character(name="Villain", personality="Evil"),
        ]
        agent.llm_backend = mock_backend

        with patch("booksmith.generation.agent.get_schema"):
            with patch(
                "booksmith.generation.agent.StructuredResponseParser"
            ) as mock_parser:
                mock_parser.parse_characters.return_value = mock_characters

                agent.generate_characters(minimal_book)

                assert len(minimal_book.characters) == 2
                assert minimal_book.characters[0].name == "Hero"

    def test_generate_characters_no_summary(self, minimal_book, llm_config):
        """Test character generation without story summary."""
        agent = WritingAgent(llm_config)

        with pytest.raises(
            DependencyValidationError,
            match="Missing dependencies for characters: story_summary",
        ):
            agent.generate_characters(minimal_book)

    def test_generate_characters_error(self, book_with_summary, llm_config):
        """Test character generation error handling."""
        agent = WritingAgent(llm_config)
        agent.llm_backend = None

        with pytest.raises(Exception):
            agent.generate_characters(book_with_summary)

    def test_generate_chapter_plan(self, book_with_summary_and_characters, llm_config):
        """Test chapter plan generation."""
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.supports_structured_output.return_value = True
        mock_chapters = [
            Chapter(chapter_number=1, title="Chapter 1"),
            Chapter(chapter_number=2, title="Chapter 2"),
        ]
        agent.llm_backend = mock_backend

        with patch("booksmith.generation.agent.get_schema"):
            with patch(
                "booksmith.generation.agent.StructuredResponseParser"
            ) as mock_parser:
                mock_parser.parse_chapter_plan.return_value = mock_chapters

                agent.generate_chapter_plan(book_with_summary_and_characters)

                assert len(book_with_summary_and_characters.chapters) == 2
                assert book_with_summary_and_characters.chapters[0].title == "Chapter 1"

    def test_generate_chapter_plan_no_summary(self, minimal_book, llm_config):
        """Test chapter plan generation without story summary."""
        agent = WritingAgent(llm_config)

        with pytest.raises(
            DependencyValidationError,
            match="Missing dependencies for chapter_plan: story_summary",
        ):
            agent.generate_chapter_plan(minimal_book)

    def test_generate_chapter_plan_error(
        self, book_with_summary_and_characters, llm_config
    ):
        """Test chapter plan generation error handling."""
        agent = WritingAgent(llm_config)
        agent.llm_backend = None

        with pytest.raises(Exception, match="No LLM backend available"):
            agent.generate_chapter_plan(book_with_summary_and_characters)

    def test_write_chapter_content(
        self, book_with_summary_and_characters_and_chapter_plan, llm_config
    ):
        """Test chapter content writing."""
        chapter = book_with_summary_and_characters_and_chapter_plan.chapters[0]
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.supports_structured_output.return_value = True
        agent.llm_backend = mock_backend

        with patch("booksmith.generation.agent.get_schema"):
            with patch(
                "booksmith.generation.agent.StructuredResponseParser"
            ) as mock_parser:
                mock_parser.parse_chapter_content.return_value = "Chapter content here"

                agent.write_chapter_content(
                    book_with_summary_and_characters_and_chapter_plan, chapter
                )

                assert chapter.content == "Chapter content here"

    def test_write_chapter_content_no_summary(self, minimal_book, llm_config):
        """Test chapter content writing without story summary."""
        chapter = Chapter(chapter_number=1, title="Test Chapter")
        agent = WritingAgent(llm_config)

        with pytest.raises(
            DependencyValidationError,
            match="Missing dependencies for chapter_content: story_summary",
        ):
            agent.write_chapter_content(minimal_book, chapter)

    def test_write_chapter_content_error(
        self, book_with_summary_and_characters_and_chapter_plan, llm_config
    ):
        """Test chapter content writing error handling."""
        chapter = book_with_summary_and_characters_and_chapter_plan.chapters[0]
        agent = WritingAgent(llm_config)
        agent.llm_backend = None

        with pytest.raises(Exception, match="No LLM backend available"):
            agent.write_chapter_content(
                book_with_summary_and_characters_and_chapter_plan, chapter
            )

    def test_generate_title(self, minimal_book, llm_config):
        """Test title generation."""
        minimal_book.story_summary = "A great story"
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.supports_structured_output.return_value = True
        agent.llm_backend = mock_backend

        with patch("booksmith.generation.agent.get_schema"):
            with patch(
                "booksmith.generation.agent.StructuredResponseParser"
            ) as mock_parser:
                mock_parser.parse_title.return_value = "The Great Adventure"

                agent.generate_title(minimal_book)

                assert minimal_book.title == "The Great Adventure"

    def test_generate_title_no_summary(self, minimal_book, llm_config):
        """Test title generation without story summary."""
        agent = WritingAgent(llm_config)

        with pytest.raises(
            DependencyValidationError,
            match="Missing dependencies for title: story_summary",
        ):
            agent.generate_title(minimal_book)

    def test_generate_title_error(self, book_with_summary, llm_config):
        """Test title generation error handling."""
        book_with_summary.story_summary = "A story"
        agent = WritingAgent(llm_config)
        agent.llm_backend = None

        with pytest.raises(Exception, match="No LLM backend available"):
            agent.generate_title(book_with_summary)

    def test_write_full_book(self, minimal_book, llm_config):
        """Test full book writing integration."""
        agent = WritingAgent(llm_config)

        # Mock all the individual methods
        with patch.object(agent, "generate_story_summary") as mock_summary:
            with patch.object(agent, "generate_title") as mock_title:
                with patch.object(agent, "generate_characters") as mock_chars:
                    with patch.object(agent, "generate_chapter_plan") as mock_plan:
                        with patch.object(
                            agent, "write_chapter_content"
                        ) as mock_content:
                            # Setup the book state as methods would modify it
                            def setup_book(*args):
                                minimal_book.story_summary = "A story"

                            def setup_title(*args):
                                minimal_book.title = "Test Book"

                            def setup_chars(*args):
                                minimal_book.characters = [Character(name="Hero")]

                            def setup_plan(*args):
                                minimal_book.chapters = [
                                    Chapter(chapter_number=1, title="Chapter 1")
                                ]

                            def setup_content(*args):
                                minimal_book.chapters[
                                    0
                                ].content = "Chapter content here"

                            mock_summary.side_effect = setup_book
                            mock_title.side_effect = setup_title
                            mock_chars.side_effect = setup_chars
                            mock_plan.side_effect = setup_plan
                            mock_content.side_effect = setup_content

                            agent.write_full_book(minimal_book)

                            # Verify all methods were called
                            mock_summary.assert_called_once()
                            mock_title.assert_called_once()
                            mock_chars.assert_called_once()
                            mock_plan.assert_called_once()
                            mock_content.assert_called_once()

    def test_get_backend_info(self, llm_config):
        """Test getting backend information."""
        agent = WritingAgent(llm_config)

        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        # Mock get_model_info method to return dict instead of Mock
        mock_backend.get_model_info.return_value = {"extra_info": "test"}
        agent.llm_backend = mock_backend

        info = agent.get_backend_info()

        assert info["status"] == "available"
        assert info["backend"] == "openai"
        assert info["model"] == llm_config.model_name

    def test_get_backend_info_no_backend(self, llm_config):
        """Test getting backend info when no backend available."""
        agent = WritingAgent(llm_config)
        agent.llm_backend = None

        info = agent.get_backend_info()

        assert info["status"] == "not_available"
        assert info["backend"] == "none"
