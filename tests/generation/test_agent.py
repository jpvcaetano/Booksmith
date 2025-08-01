from unittest.mock import MagicMock, Mock, patch

import pytest

from booksmith.generation.agent import PartialGenerationFailure, WritingAgent
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
            assert agent.llm_config.max_tokens == 32768
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


class TestWritingAgentRetryLogic:
    """Tests for WritingAgent retry logic and error handling."""

    def test_initialization_with_progress_callback(self, llm_config):
        """Test agent initialization with progress callback."""
        callback_messages = []

        def progress_callback(message: str):
            callback_messages.append(message)

        with patch("booksmith.generation.agent.OpenAIBackend"):
            agent = WritingAgent(llm_config, progress_callback=progress_callback)

            assert agent.progress_callback == progress_callback
            assert agent.llm_config == llm_config

    def test_report_progress_with_callback(self, llm_config):
        """Test progress reporting with callback."""
        callback_messages = []

        def progress_callback(message: str):
            callback_messages.append(message)

        with patch("booksmith.generation.agent.OpenAIBackend"):
            agent = WritingAgent(llm_config, progress_callback=progress_callback)
            agent._report_progress("Test message")

            assert "Test message" in callback_messages

    def test_report_progress_without_callback(self, llm_config):
        """Test progress reporting without callback."""
        with patch("booksmith.generation.agent.OpenAIBackend"):
            agent = WritingAgent(llm_config)
            # Should not raise an error
            agent._report_progress("Test message")

    def test_handle_generation_error_timeout(self, llm_config):
        """Test error handling for timeout errors."""
        callback_messages = []

        def progress_callback(message: str):
            callback_messages.append(message)

        with patch("booksmith.generation.agent.OpenAIBackend"):
            agent = WritingAgent(llm_config, progress_callback=progress_callback)

            error = RuntimeError("timeout occurred")
            agent._handle_generation_error("Test operation", error)

            # Should contain timeout-specific message
            timeout_messages = [msg for msg in callback_messages if "timed out" in msg]
            assert len(timeout_messages) > 0

    def test_handle_generation_error_rate_limit(self, llm_config):
        """Test error handling for rate limit errors."""
        callback_messages = []

        def progress_callback(message: str):
            callback_messages.append(message)

        with patch("booksmith.generation.agent.OpenAIBackend"):
            agent = WritingAgent(llm_config, progress_callback=progress_callback)

            error = RuntimeError("rate limit exceeded")
            agent._handle_generation_error("Test operation", error)

            # Should contain rate limit-specific message
            rate_limit_messages = [
                msg for msg in callback_messages if "Rate limit" in msg
            ]
            assert len(rate_limit_messages) > 0

    @patch("booksmith.generation.agent.OpenAIBackend")
    def test_write_full_book_with_partial_failure(
        self, mock_backend_class, minimal_book, llm_config
    ):
        """Test write_full_book handling partial failures gracefully."""
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend_class.return_value = mock_backend

        callback_messages = []

        def progress_callback(message: str):
            callback_messages.append(message)

        agent = WritingAgent(llm_config, progress_callback=progress_callback)

        # Mock methods to simulate partial failure
        with patch.object(
            agent, "generate_story_summary"
        ) as mock_summary, patch.object(
            agent, "generate_title"
        ) as mock_title, patch.object(
            agent, "generate_characters"
        ) as mock_characters, patch.object(
            agent, "generate_chapter_plan"
        ) as mock_plan:
            # Make title generation fail
            mock_title.side_effect = Exception("Title generation failed")

            # Other methods succeed
            mock_summary.return_value = None
            mock_characters.return_value = None
            mock_plan.return_value = None

            # Should raise PartialGenerationFailure
            with pytest.raises(PartialGenerationFailure) as exc_info:
                agent.write_full_book(minimal_book)

            # Check that the failure contains the right step
            assert "Title" in exc_info.value.failed_steps

    @patch("booksmith.generation.agent.OpenAIBackend")
    def test_write_full_book_with_chapter_failures(
        self, mock_backend_class, minimal_book, llm_config
    ):
        """Test write_full_book handling chapter generation failures."""
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend_class.return_value = mock_backend

        agent = WritingAgent(llm_config)

        # Set up book with chapters
        minimal_book.chapters = [
            Chapter(chapter_number=1, title="Chapter 1"),
            Chapter(chapter_number=2, title="Chapter 2"),
        ]

        # Mock methods
        with patch.object(
            agent, "generate_story_summary"
        ) as mock_summary, patch.object(
            agent, "generate_title"
        ) as mock_title, patch.object(
            agent, "generate_characters"
        ) as mock_characters, patch.object(
            agent, "generate_chapter_plan"
        ) as mock_plan, patch.object(
            agent, "write_chapter_content"
        ) as mock_chapter:
            # Make chapter 2 fail
            def chapter_side_effect(book, chapter):
                if chapter.chapter_number == 2:
                    raise Exception("Chapter 2 failed")

            mock_chapter.side_effect = chapter_side_effect

            # Should raise PartialGenerationFailure
            with pytest.raises(PartialGenerationFailure) as exc_info:
                agent.write_full_book(minimal_book)

            # Check that the failure contains chapter information
            failed_steps = exc_info.value.failed_steps
            chapter_failures = [step for step in failed_steps if "Chapters:" in step]
            assert len(chapter_failures) > 0
            assert "2" in chapter_failures[0]

    @patch("booksmith.generation.agent.OpenAIBackend")
    def test_regenerate_chapter_success(
        self, mock_backend_class, minimal_book, llm_config
    ):
        """Test regenerating a specific chapter."""
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend_class.return_value = mock_backend

        agent = WritingAgent(llm_config)

        # Set up book with chapters
        chapter = Chapter(chapter_number=1, title="Chapter 1", content="Old content")
        minimal_book.chapters = [chapter]

        with patch.object(agent, "write_chapter_content") as mock_write:
            agent.regenerate_chapter(minimal_book, 1)

            # Should clear content and call write_chapter_content
            assert chapter.content is None
            mock_write.assert_called_once_with(minimal_book, chapter)

    @patch("booksmith.generation.agent.OpenAIBackend")
    def test_regenerate_chapter_not_found(
        self, mock_backend_class, minimal_book, llm_config
    ):
        """Test regenerating a chapter that doesn't exist."""
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend_class.return_value = mock_backend

        agent = WritingAgent(llm_config)
        minimal_book.chapters = []

        with pytest.raises(ValueError, match="No chapters available"):
            agent.regenerate_chapter(minimal_book, 1)

    @patch("booksmith.generation.agent.OpenAIBackend")
    def test_regenerate_invalid_chapter_number(
        self, mock_backend_class, minimal_book, llm_config
    ):
        """Test regenerating with invalid chapter number."""
        mock_backend = Mock()
        mock_backend.is_available.return_value = True
        mock_backend_class.return_value = mock_backend

        agent = WritingAgent(llm_config)
        minimal_book.chapters = [Chapter(chapter_number=1, title="Chapter 1")]

        with pytest.raises(ValueError, match="Chapter 2 not found"):
            agent.regenerate_chapter(minimal_book, 2)

    def test_default_config_includes_retry_settings(self):
        """Test that default LLM config includes retry settings."""
        with patch("booksmith.generation.agent.OpenAIBackend"), patch.dict(
            "os.environ", {"OPENAI_API_KEY": "test-key"}
        ):
            agent = WritingAgent()

            config = agent.llm_config
            assert config.timeout_seconds == 60
            assert config.max_retries == 3
            assert config.retry_delay == 5.0


class TestPartialGenerationFailure:
    """Tests for PartialGenerationFailure exception."""

    def test_partial_generation_failure_creation(self):
        """Test creating PartialGenerationFailure with failed steps."""
        failed_steps = ["Title", "Chapters: 1, 2"]
        error = PartialGenerationFailure("Some steps failed", failed_steps)

        assert str(error) == "Some steps failed"
        assert error.failed_steps == failed_steps

    def test_partial_generation_failure_empty_steps(self):
        """Test creating PartialGenerationFailure with empty failed steps."""
        error = PartialGenerationFailure("No specific failures", [])

        assert str(error) == "No specific failures"
        assert error.failed_steps == []
