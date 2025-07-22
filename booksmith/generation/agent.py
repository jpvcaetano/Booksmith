import logging
from typing import Optional
from tqdm import tqdm

from ..models import Book, Chapter
from ..backends import LLMConfig, create_llm_backend, LLMBackend
from .prompts import (
    generate_story_summary_prompt,
    generate_character_prompt,
    generate_chapter_plan_prompt,
    generate_chapter_content_prompt,
    generate_title_prompt
)
from .parsers import ResponseParser

logger = logging.getLogger(__name__)

class WritingAgent:
    """An agent that writes a book using LLM technology."""

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        """Initialize the writing agent with LLM configuration."""
        if llm_config is None:
            # Default configuration for testing
            llm_config = LLMConfig(
                backend="huggingface",
                model_name="microsoft/DialoGPT-medium",
                max_tokens=1000,
                temperature=0.7
            )
        
        self.llm_config = llm_config
        self.llm_backend: Optional[LLMBackend] = None
        self._initialize_backend()
    
    def _initialize_backend(self):
        """Initialize the LLM backend."""
        try:
            self.llm_backend = create_llm_backend(self.llm_config)
            if not self.llm_backend.is_available():
                logger.warning("LLM backend not available, falling back to placeholder mode")
                self.llm_backend = None
        except Exception as e:
            logger.error(f"Failed to initialize LLM backend: {e}")
            self.llm_backend = None
    
    def _generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the configured LLM backend."""
        if not self.llm_backend:
            logger.warning("No LLM backend available, returning placeholder")
            return f"[PLACEHOLDER: {prompt[:100]}...]"
        
        try:
            return self.llm_backend.generate(prompt, **kwargs)
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return f"[ERROR: Generation failed - {str(e)}]"

    def generate_story_summary(self, book: Book):
        """Generates a story summary for the book."""
        print("🔍 Generating story summary...")
        
        try:
            prompt = generate_story_summary_prompt(book)
            logger.debug(f"Story summary prompt: {prompt[:200]}...")
            
            response = self._generate_text(
                prompt, 
                max_tokens=600,
                temperature=0.7
            )
            
            book.story_summary = ResponseParser.parse_story_summary(response)
            print(f"✅ Story summary generated ({len(book.story_summary)} characters)")
            logger.info(f"Generated story summary: {book.story_summary[:100]}...")
            
        except Exception as e:
            logger.error(f"Story summary generation failed: {e}")
            book.story_summary = f"Error generating story summary: {str(e)}"
            print("❌ Story summary generation failed")

    def generate_characters(self, book: Book):
        """Generates characters for the book."""
        if not book.story_summary:
            raise ValueError("Story summary must be generated before characters")
        
        print("👥 Generating characters...")
        
        try:
            prompt = generate_character_prompt(book)
            logger.debug(f"Character generation prompt: {prompt[:200]}...")
            
            response = self._generate_text(
                prompt, 
                max_tokens=1200,
                temperature=0.8
            )
            
            characters = ResponseParser.parse_characters(response)
            book.characters = characters
            
            print(f"✅ Generated {len(characters)} characters:")
            for char in characters:
                print(f"  - {char.name}")
            
            logger.info(f"Generated {len(characters)} characters")
            
        except Exception as e:
            logger.error(f"Character generation failed: {e}")
            # Fallback: create a basic character
            from ..models import Character
            book.characters = [Character(
                name="Protagonist",
                background_story="A brave hero on a journey",
                appearance="Determined and strong",
                personality="Courageous and kind"
            )]
            print("❌ Character generation failed, using fallback")

    def generate_chapter_plan(self, book: Book):
        """Generates a chapter plan for the book."""
        if not book.story_summary:
            raise ValueError("Story summary must be generated before chapter plan")
        
        print("📋 Generating chapter plan...")
        
        try:
            prompt = generate_chapter_plan_prompt(book)
            logger.debug(f"Chapter plan prompt: {prompt[:200]}...")
            
            response = self._generate_text(
                prompt, 
                max_tokens=1500,
                temperature=0.7
            )
            
            chapters = ResponseParser.parse_chapter_plan(response)
            book.chapters = chapters
            
            print(f"✅ Generated plan for {len(chapters)} chapters:")
            for chapter in chapters:
                print(f"  Chapter {chapter.chapter_number}: {chapter.title}")
            
            logger.info(f"Generated plan for {len(chapters)} chapters")
            
        except Exception as e:
            logger.error(f"Chapter plan generation failed: {e}")
            # Fallback: create basic chapters
            book.chapters = [
                Chapter(
                    chapter_number=1,
                    title="The Beginning",
                    summary="The story begins",
                    content=""
                ),
                Chapter(
                    chapter_number=2,
                    title="The Journey",
                    summary="The adventure continues",
                    content=""
                ),
                Chapter(
                    chapter_number=3,
                    title="The End",
                    summary="The story concludes",
                    content=""
                )
            ]
            print("❌ Chapter plan generation failed, using fallback")

    def write_chapter_content(self, book: Book, chapter: Chapter):
        """Writes the content for a chapter."""
        if not book.story_summary:
            raise ValueError("Story summary must be available before writing chapters")
        
        print(f"✍️  Writing Chapter {chapter.chapter_number}: {chapter.title}")
        
        try:
            prompt = generate_chapter_content_prompt(book, chapter)
            logger.debug(f"Chapter content prompt: {prompt[:200]}...")
            
            response = self._generate_text(
                prompt, 
                max_tokens=2500,
                temperature=0.8
            )
            
            chapter.content = ResponseParser.parse_chapter_content(response)
            
            word_count = len(chapter.content.split())
            print(f"✅ Chapter {chapter.chapter_number} written ({word_count} words)")
            logger.info(f"Chapter {chapter.chapter_number} content generated: {word_count} words")
            
        except Exception as e:
            logger.error(f"Chapter content generation failed: {e}")
            chapter.content = f"[Chapter {chapter.chapter_number} content generation failed: {str(e)}]"
            print(f"❌ Chapter {chapter.chapter_number} generation failed")

    def generate_title(self, book: Book):
        """Generates a title for the book."""
        if not book.story_summary:
            raise ValueError("Story summary must be available before generating title")
        
        print("📚 Generating book title...")
        
        try:
            prompt = generate_title_prompt(book)
            logger.debug(f"Title generation prompt: {prompt[:200]}...")
            
            response = self._generate_text(
                prompt, 
                max_tokens=300,
                temperature=0.9
            )
            
            book.title = ResponseParser.parse_title(response)
            print(f"✅ Book title generated: '{book.title}'")
            logger.info(f"Generated title: {book.title}")
            
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            book.title = "The Generated Story"
            print("❌ Title generation failed, using fallback")

    def write_full_book(self, book: Book):
        """Writes the full book."""
        print("📖 Starting full book generation...")
        
        try:
            # Step 1: Generate story summary
            if not book.story_summary:
                self.generate_story_summary(book)
            
            # Step 2: Generate title
            if not book.title:
                self.generate_title(book)
            
            # Step 3: Generate characters
            if not book.characters:
                self.generate_characters(book)
            
            # Step 4: Generate chapter plan
            if not book.chapters:
                self.generate_chapter_plan(book)
            
            # Step 5: Write chapter content
            chapters_to_write = [ch for ch in book.chapters if not ch.content]
            if chapters_to_write:
                print(f"\n📝 Writing content for {len(chapters_to_write)} chapters...")
                
                for chapter in tqdm(chapters_to_write, desc="Writing chapters"):
                    self.write_chapter_content(book, chapter)
            
            # Summary
            total_words = sum(len(ch.content.split()) for ch in book.chapters if ch.content)
            print(f"\n🎉 Book generation complete!")
            print(f"📊 Stats:")
            print(f"   Title: {book.title}")
            print(f"   Chapters: {len(book.chapters)}")
            print(f"   Characters: {len(book.characters)}")
            print(f"   Total words: {total_words:,}")
            
            logger.info(f"Full book generated: {len(book.chapters)} chapters, {total_words} words")
            
        except Exception as e:
            logger.error(f"Full book generation failed: {e}")
            print(f"❌ Book generation failed: {str(e)}")
            raise

    def get_backend_info(self) -> dict:
        """Get information about the current LLM backend."""
        if not self.llm_backend:
            return {"status": "not_available", "backend": "none"}
        
        base_info = {
            "status": "available" if self.llm_backend.is_available() else "not_available",
            "backend": self.llm_config.backend,
            "model": self.llm_config.model_name,
            "device": self.llm_config.device
        }
        
        # Add detailed model info for HuggingFace backend
        if hasattr(self.llm_backend, 'get_model_info'):
            model_info = self.llm_backend.get_model_info()
            base_info.update(model_info)
        
        return base_info
    
    def clear_cache(self):
        """Clear model cache to free memory."""
        if self.llm_backend and hasattr(self.llm_backend, 'clear_cache'):
            self.llm_backend.clear_cache()
        
    def get_memory_usage(self) -> str:
        """Get human-readable memory usage info."""
        info = self.get_backend_info()
        if 'memory_usage_gb' in info:
            return f"{info['memory_usage_gb']:.1f} GB"
        return "Unknown" 