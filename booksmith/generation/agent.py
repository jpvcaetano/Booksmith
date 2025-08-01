import logging
import os
from typing import Any, Callable, Optional

from tqdm import tqdm

from ..models import Book, Chapter
from ..utils.validators import GenerationStep, validate_generation_step
from .openai import LLMConfig, OpenAIBackend
from .parsers import ResponseParser, StructuredResponseParser
from .prompts import (
    generate_chapter_content_prompt,
    generate_chapter_plan_prompt,
    generate_character_prompt,
    generate_story_summary_prompt,
    generate_title_prompt,
)
from .schemas import get_schema

logger = logging.getLogger(__name__)


class WritingAgent:
    """An agent that writes a book using LLM technology with robust error handling."""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize the writing agent with LLM configuration and optional progress callback."""
        if llm_config is None:
            # Default configuration for OpenAI with simple retry settings
            llm_config = LLMConfig(
                model_name="gpt-4.1",
                max_tokens=32768,
                temperature=0.7,
                api_key=os.environ.get("OPENAI_API_KEY"),
                timeout_seconds=60,
                max_retries=3,
                retry_delay=5.0,
            )

        self.llm_config = llm_config
        self.llm_backend: Optional[OpenAIBackend] = None
        self.progress_callback = progress_callback
        self._initialize_backend()

    def _initialize_backend(self):
        """Initialize the LLM backend."""
        try:
            self.llm_backend = OpenAIBackend(self.llm_config)
            if not self.llm_backend.is_available():
                logger.warning(
                    "LLM backend not available, falling back to placeholder mode"
                )
                self.llm_backend = None
        except Exception as e:
            logger.error(f"Failed to initialize LLM backend: {e}")
            self.llm_backend = None

    def _report_progress(self, message: str) -> None:
        """Report progress to callback if available."""
        logger.info(message)
        if self.progress_callback:
            self.progress_callback(message)

    def _handle_generation_error(self, operation: str, error: Exception) -> None:
        """Handle generation errors with user-friendly messages."""
        error_msg = str(error)

        # Check for specific error types and provide helpful messages
        if "timeout" in error_msg.lower():
            user_message = (
                f"⏱️ {operation} timed out. You can try again or check your connection."
            )
        elif "rate limit" in error_msg.lower():
            user_message = f"🚫 Rate limit reached during {operation}. Please wait a moment and try again."
        elif "retries" in error_msg.lower():
            user_message = (
                f"🔄 {operation} failed after multiple attempts. Please try again later."
            )
        else:
            user_message = f"❌ {operation} failed: {error_msg}"

        self._report_progress(user_message)
        logger.error(f"{operation} failed: {error}")

    def _generate_with_retry_feedback(
        self, operation: str, prompt: str, schema_name: str = None, **kwargs
    ):
        """Generate with retry feedback and error handling."""
        if not self.llm_backend:
            raise Exception("No LLM backend available")

        try:
            if schema_name:
                return self._generate_structured(prompt, schema_name, **kwargs)
            else:
                return self._generate_text(prompt, **kwargs)
        except Exception as e:
            self._handle_generation_error(operation, e)
            raise

    def _generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the configured LLM backend."""
        if not self.llm_backend:
            logger.warning("No LLM backend available, returning placeholder")
            raise Exception("No LLM backend available")

        try:
            return self.llm_backend.generate(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            raise

    def _generate_structured(self, prompt: str, schema_name: str, **kwargs):
        """Generate structured output with fallback to text generation."""
        if not self.llm_backend:
            logger.warning("No LLM backend available, returning placeholder")
            raise Exception("No LLM backend available")

        try:
            # Try structured generation if supported
            if self.llm_backend.supports_structured_output():
                schema = get_schema(schema_name)
                return self.llm_backend.generate_structured(
                    prompt, schema=schema, **kwargs
                )
            else:
                # Fallback to regular generation
                logger.info(
                    f"Backend doesn't support structured output, using regular generation"
                )
                return self.llm_backend.generate(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            raise

    def generate_story_summary(self, book: Book):
        """Generates a story summary for the book with retry support."""
        validate_generation_step(book, GenerationStep.SUMMARY)
        self._report_progress("🔍 Generating story summary...")

        try:
            prompt = generate_story_summary_prompt(book)
            logger.debug(f"Story summary prompt: {prompt[:200]}...")

            response = self._generate_with_retry_feedback(
                "Story summary generation",
                prompt,
                schema_name="story_summary",
            )

            book.story_summary = StructuredResponseParser.parse_story_summary(response)
            message = (
                f"✅ Story summary generated ({len(book.story_summary)} characters)"
            )
            self._report_progress(message)
            logger.info(f"Generated story summary: {book.story_summary[:100]}...")

        except Exception as e:
            logger.error(f"Story summary generation failed: {e}")
            raise

    def generate_characters(self, book: Book):
        """Generates characters for the book with retry support."""
        validate_generation_step(book, GenerationStep.CHARACTERS)

        self._report_progress("👥 Generating characters...")

        try:
            prompt = generate_character_prompt(book)
            logger.debug(f"Character generation prompt: {prompt[:200]}...")

            response = self._generate_with_retry_feedback(
                "Character generation",
                prompt,
                schema_name="character",
            )

            characters = StructuredResponseParser.parse_characters(response)
            book.characters = characters

            message = f"✅ Generated {len(characters)} characters"
            self._report_progress(message)
            for char in characters:
                self._report_progress(f"  - {char.name}")

            logger.info(f"Generated {len(characters)} characters")

        except Exception as e:
            logger.error(f"Character generation failed: {e}")
            raise

    def generate_chapter_plan(self, book: Book):
        """Generates a chapter plan for the book with retry support."""
        validate_generation_step(book, GenerationStep.CHAPTER_PLAN)

        self._report_progress("📋 Generating chapter plan...")

        try:
            prompt = generate_chapter_plan_prompt(book)
            logger.debug(f"Chapter plan prompt: {prompt[:200]}...")

            response = self._generate_with_retry_feedback(
                "Chapter plan generation",
                prompt,
                schema_name="chapter_plan",
            )

            chapters = StructuredResponseParser.parse_chapter_plan(response)
            book.chapters = chapters

            message = f"✅ Generated plan for {len(chapters)} chapters"
            self._report_progress(message)
            for chapter in chapters:
                self._report_progress(
                    f"  Chapter {chapter.chapter_number}: {chapter.title}"
                )

            logger.info(f"Generated plan for {len(chapters)} chapters")

        except Exception as e:
            logger.error(f"Chapter plan generation failed: {e}")
            raise

    def write_chapter_content(self, book: Book, chapter: Chapter):
        """Writes the content for a chapter with retry support."""
        validate_generation_step(
            book, GenerationStep.CHAPTER_CONTENT, chapter.chapter_number
        )

        self._report_progress(
            f"✍️  Writing Chapter {chapter.chapter_number}: {chapter.title}"
        )

        try:
            prompt = generate_chapter_content_prompt(book, chapter)
            logger.debug(f"Chapter content prompt: {prompt[:200]}...")

            response = self._generate_with_retry_feedback(
                f"Chapter {chapter.chapter_number} content generation",
                prompt,
                schema_name="chapter_content",
            )

            chapter.content = StructuredResponseParser.parse_chapter_content(response)

            word_count = len(chapter.content.split())
            message = f"✅ Chapter {chapter.chapter_number} written ({word_count} words)"
            self._report_progress(message)
            logger.info(
                f"Chapter {chapter.chapter_number} content generated: {word_count} words"
            )

        except Exception as e:
            logger.error(f"Chapter content generation failed: {e}")
            raise

    def generate_title(self, book: Book):
        """Generates a title for the book with retry support."""
        validate_generation_step(book, GenerationStep.TITLE)

        self._report_progress("📚 Generating book title...")

        try:
            prompt = generate_title_prompt(book)
            logger.debug(f"Title generation prompt: {prompt[:200]}...")

            response = self._generate_with_retry_feedback(
                "Title generation",
                prompt,
                schema_name="title",
                max_tokens=300,
                temperature=0.9,
            )

            book.title = StructuredResponseParser.parse_title(response)
            message = f"✅ Book title generated: '{book.title}'"
            self._report_progress(message)
            logger.info(f"Generated title: {book.title}")

        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            raise

    def write_full_book(self, book: Book):
        """Writes the full book with retry support and partial failure handling."""
        self._report_progress("📖 Starting full book generation...")

        failed_steps = []

        try:
            # Step 1: Generate story summary
            try:
                self.generate_story_summary(book)
            except Exception as e:
                failed_steps.append("Story Summary")
                self._report_progress(
                    f"⚠️ Story summary failed, continuing with other steps: {str(e)}"
                )

            # Step 2: Generate title
            try:
                self.generate_title(book)
            except Exception as e:
                failed_steps.append("Title")
                self._report_progress(
                    f"⚠️ Title generation failed, continuing with other steps: {str(e)}"
                )

            # Step 3: Generate characters
            try:
                self.generate_characters(book)
            except Exception as e:
                failed_steps.append("Characters")
                self._report_progress(
                    f"⚠️ Character generation failed, continuing with other steps: {str(e)}"
                )

            # Step 4: Generate chapter plan
            try:
                self.generate_chapter_plan(book)
            except Exception as e:
                failed_steps.append("Chapter Plan")
                self._report_progress(
                    f"⚠️ Chapter plan failed, continuing with other steps: {str(e)}"
                )

            # Step 5: Write chapter content
            if book.chapters:
                chapters_to_write = [ch for ch in book.chapters if not ch.content]
                self._report_progress(
                    f"📝 Writing content for {len(chapters_to_write)} chapters..."
                )

                failed_chapters = []
                for chapter in tqdm(chapters_to_write, desc="Writing chapters"):
                    try:
                        self.write_chapter_content(book, chapter)
                    except Exception as e:
                        failed_chapters.append(chapter.chapter_number)
                        self._report_progress(
                            f"⚠️ Chapter {chapter.chapter_number} failed: {str(e)}"
                        )

                if failed_chapters:
                    failed_steps.append(
                        f"Chapters: {', '.join(map(str, failed_chapters))}"
                    )

            # Summary
            completed_chapters = [ch for ch in book.chapters if ch.content]
            total_words = sum(len(ch.content.split()) for ch in completed_chapters)

            if failed_steps:
                self._report_progress(
                    f"⚠️ Book generation completed with some failures!"
                )
                self._report_progress(f"❌ Failed steps: {', '.join(failed_steps)}")
            else:
                self._report_progress(f"🎉 Book generation complete!")

            self._report_progress(f"📊 Stats:")
            self._report_progress(f"   Title: {book.title or 'Not generated'}")
            self._report_progress(
                f"   Chapters: {len(completed_chapters)}/{len(book.chapters) if book.chapters else 0}"
            )
            self._report_progress(
                f"   Characters: {len(book.characters) if book.characters else 0}"
            )
            self._report_progress(f"   Total words: {total_words:,}")

            logger.info(
                f"Full book generated: {len(completed_chapters)} chapters, {total_words} words"
            )

            if failed_steps:
                raise PartialGenerationFailure(
                    f"Some steps failed: {', '.join(failed_steps)}", failed_steps
                )

        except PartialGenerationFailure:
            raise
        except Exception as e:
            logger.error(f"Full book generation failed: {e}")
            self._report_progress(f"❌ Book generation failed: {str(e)}")
            raise

    def regenerate_chapter(self, book: Book, chapter_number: int):
        """Regenerate a specific chapter."""
        if not book.chapters:
            raise ValueError("No chapters available to regenerate")

        # Find the chapter
        chapter = None
        for ch in book.chapters:
            if ch.chapter_number == chapter_number:
                chapter = ch
                break

        if not chapter:
            raise ValueError(f"Chapter {chapter_number} not found")

        self._report_progress(
            f"🔄 Regenerating Chapter {chapter_number}: {chapter.title}"
        )

        # Clear existing content
        chapter.content = None

        # Regenerate
        self.write_chapter_content(book, chapter)

    def get_backend_info(self) -> dict:
        """Get information about the current LLM backend."""
        if not self.llm_backend:
            return {"status": "not_available", "backend": "none"}

        base_info = {
            "status": "available"
            if self.llm_backend.is_available()
            else "not_available",
            "backend": "openai",  # We only have OpenAI backend now
            "model": self.llm_config.model_name,
            "device": "cloud",  # OpenAI is cloud-based
        }

        # Add detailed model info if backend supports it
        if hasattr(self.llm_backend, "get_model_info"):
            model_info = self.llm_backend.get_model_info()
            base_info.update(model_info)

        return base_info


class PartialGenerationFailure(Exception):
    """Exception raised when book generation partially fails."""

    def __init__(self, message: str, failed_steps: list):
        super().__init__(message)
        self.failed_steps = failed_steps
