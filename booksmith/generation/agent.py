import logging
from typing import Optional

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
    """An agent that writes a book using LLM technology."""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize the writing agent with LLM configuration."""
        if llm_config is None:
            # Default configuration for OpenAI
            llm_config = LLMConfig(
                model_name="gpt-4.1", max_tokens=1000, temperature=0.7
            )

        self.llm_config = llm_config
        self.llm_backend: Optional[OpenAIBackend] = None
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
        """Generates a story summary for the book."""
        validate_generation_step(book, GenerationStep.SUMMARY)
        print("🔍 Generating story summary...")

        try:
            prompt = generate_story_summary_prompt(book)
            logger.debug(f"Story summary prompt: {prompt[:200]}...")

            response = self._generate_structured(
                prompt,
                schema_name="story_summary",
            )

            book.story_summary = StructuredResponseParser.parse_story_summary(response)
            print(f"✅ Story summary generated ({len(book.story_summary)} characters)")
            logger.info(f"Generated story summary: {book.story_summary[:100]}...")

        except Exception as e:
            logger.error(f"Story summary generation failed: {e}")
            raise

    def generate_characters(self, book: Book):
        """Generates characters for the book."""
        validate_generation_step(book, GenerationStep.CHARACTERS)

        print("👥 Generating characters...")

        try:
            prompt = generate_character_prompt(book)
            logger.debug(f"Character generation prompt: {prompt[:200]}...")

            response = self._generate_structured(
                prompt,
                schema_name="character",
            )

            characters = StructuredResponseParser.parse_characters(response)
            book.characters = characters

            print(f"✅ Generated {len(characters)} characters:")
            for char in characters:
                print(f"  - {char.name}")

            logger.info(f"Generated {len(characters)} characters")

        except Exception as e:
            logger.error(f"Character generation failed: {e}")
            raise

    def generate_chapter_plan(self, book: Book):
        """Generates a chapter plan for the book."""
        validate_generation_step(book, GenerationStep.CHAPTER_PLAN)

        print("📋 Generating chapter plan...")

        try:
            prompt = generate_chapter_plan_prompt(book)
            logger.debug(f"Chapter plan prompt: {prompt[:200]}...")

            response = self._generate_structured(
                prompt,
                schema_name="chapter_plan",
            )

            chapters = StructuredResponseParser.parse_chapter_plan(response)
            book.chapters = chapters

            print(f"✅ Generated plan for {len(chapters)} chapters:")
            for chapter in chapters:
                print(f"  Chapter {chapter.chapter_number}: {chapter.title}")

            logger.info(f"Generated plan for {len(chapters)} chapters")

        except Exception as e:
            logger.error(f"Chapter plan generation failed: {e}")
            raise

    def write_chapter_content(self, book: Book, chapter: Chapter):
        """Writes the content for a chapter."""
        validate_generation_step(
            book, GenerationStep.CHAPTER_CONTENT, chapter.chapter_number
        )

        print(f"✍️  Writing Chapter {chapter.chapter_number}: {chapter.title}")

        try:
            prompt = generate_chapter_content_prompt(book, chapter)
            logger.debug(f"Chapter content prompt: {prompt[:200]}...")

            response = self._generate_structured(
                prompt,
                schema_name="chapter_content",
            )

            chapter.content = StructuredResponseParser.parse_chapter_content(response)

            word_count = len(chapter.content.split())
            print(f"✅ Chapter {chapter.chapter_number} written ({word_count} words)")
            logger.info(
                f"Chapter {chapter.chapter_number} content generated: {word_count} words"
            )

        except Exception as e:
            logger.error(f"Chapter content generation failed: {e}")
            raise

    def generate_title(self, book: Book):
        """Generates a title for the book."""
        validate_generation_step(book, GenerationStep.TITLE)

        print("📚 Generating book title...")

        try:
            prompt = generate_title_prompt(book)
            logger.debug(f"Title generation prompt: {prompt[:200]}...")

            response = self._generate_structured(
                prompt, schema_name="title", max_tokens=300, temperature=0.9
            )

            book.title = StructuredResponseParser.parse_title(response)
            print(f"✅ Book title generated: '{book.title}'")
            logger.info(f"Generated title: {book.title}")

        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            raise

    def write_full_book(self, book: Book):
        """Writes the full book."""
        print("📖 Starting full book generation...")

        try:
            # Step 1: Generate story summary
            self.generate_story_summary(book)

            # Step 2: Generate title
            self.generate_title(book)

            # Step 3: Generate characters
            self.generate_characters(book)

            # Step 4: Generate chapter plan
            self.generate_chapter_plan(book)

            # Step 5: Write chapter content
            chapters_to_write = [ch for ch in book.chapters if not ch.content]
            print(f"\n📝 Writing content for {len(chapters_to_write)} chapters...")

            for chapter in tqdm(chapters_to_write, desc="Writing chapters"):
                self.write_chapter_content(book, chapter)

            # Summary
            total_words = sum(
                len(ch.content.split()) for ch in book.chapters if ch.content
            )
            print(f"\n🎉 Book generation complete!")
            print(f"📊 Stats:")
            print(f"   Title: {book.title}")
            print(f"   Chapters: {len(book.chapters)}")
            print(f"   Characters: {len(book.characters)}")
            print(f"   Total words: {total_words:,}")

            logger.info(
                f"Full book generated: {len(book.chapters)} chapters, {total_words} words"
            )

        except Exception as e:
            logger.error(f"Full book generation failed: {e}")
            print(f"❌ Book generation failed: {str(e)}")
            raise

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
