"""
FastAPI application for Booksmith book generation API.
"""

import logging
import os
from uuid import UUID

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

from importlib.metadata import metadata, version

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from ..generation import LLMConfig, WritingAgent
from ..models import Book
from ..utils.validators import (
    DependencyValidationError,
    GenerationStep,
    validate_generation_step,
)
from .models import (
    BookIdRequest,
    BookStateResponse,
    ErrorResponse,
    GenerateChapterContentRequest,
    GenerateChapterContentResponse,
    GenerateChapterPlanResponse,
    GenerateCharactersResponse,
    GenerateSummaryRequest,
    GenerateSummaryResponse,
    GenerateTitleResponse,
)
from .state import BookStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get project metadata
project_version = version("booksmith")
project_metadata = metadata("booksmith")
project_description = project_metadata.get("Summary", "AI-powered book generation tool")


# Create FastAPI app
app = FastAPI(
    title="Booksmith API",
    description=f"{project_description} - REST API for book generation",
    version=project_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure OpenAI backend
llm_config = LLMConfig(
    model_name="gpt-4.1",
    max_tokens=32768,
    temperature=0.7,
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# Initialize the writing agent and state manager
writing_agent = WritingAgent(llm_config)
state_manager = BookStateManager()


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500, content={"error": "Internal server error", "detail": str(exc)}
    )


@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Booksmith API",
        "version": project_version,
        "description": project_description,
        "docs": "/docs",
        "endpoints": [
            "POST /generate/summary",
            "POST /generate/title",
            "POST /generate/characters",
            "POST /generate/chapter-plan",
            "POST /generate/chapter-content",
            "GET /books/{book_id}",
        ],
    }


@app.post("/generate/summary", response_model=GenerateSummaryResponse)
async def generate_summary(request: GenerateSummaryRequest):
    """Generate a story summary and create a new book."""
    try:
        # Create a new book
        book_id, book = state_manager.create_book(
            base_prompt=request.base_prompt,
            language=request.language,
            writing_style=request.writing_style,
            genre=request.genre,
            target_audience=request.target_audience,
        )

        # Validate dependencies
        validate_generation_step(book, GenerationStep.SUMMARY)

        # Generate the story summary
        writing_agent.generate_story_summary(book)

        # Update the book in state
        state_manager.update_book(book_id, book)

        return GenerateSummaryResponse(
            book_id=book_id, story_summary=book.story_summary
        )
    except DependencyValidationError as e:
        logger.error(f"Dependency validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Summary generation failed: {str(e)}"
        )


@app.post("/generate/title", response_model=GenerateTitleResponse)
async def generate_title(request: BookIdRequest):
    """Generate a book title (requires existing summary)."""
    try:
        # Get the book
        book = state_manager.get_book(request.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Validate dependencies
        validate_generation_step(book, GenerationStep.TITLE)

        # Generate the title
        writing_agent.generate_title(book)

        # Update the book in state
        state_manager.update_book(request.book_id, book)

        return GenerateTitleResponse(book_id=request.book_id, title=book.title)

    except HTTPException:
        raise
    except DependencyValidationError as e:
        logger.error(f"Dependency validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Title generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Title generation failed: {str(e)}"
        )


@app.post("/generate/characters", response_model=GenerateCharactersResponse)
async def generate_characters(request: BookIdRequest):
    """Generate character profiles (requires existing summary)."""
    try:
        # Get the book
        book = state_manager.get_book(request.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Validate dependencies
        validate_generation_step(book, GenerationStep.CHARACTERS)

        # Generate characters
        writing_agent.generate_characters(book)

        # Update the book in state
        state_manager.update_book(request.book_id, book)

        return GenerateCharactersResponse(
            book_id=request.book_id, characters=book.characters
        )

    except HTTPException:
        raise
    except DependencyValidationError as e:
        logger.error(f"Dependency validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Character generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Character generation failed: {str(e)}"
        )


@app.post("/generate/chapter-plan", response_model=GenerateChapterPlanResponse)
async def generate_chapter_plan(request: BookIdRequest):
    """Generate chapter outline (requires existing summary)."""
    try:
        # Get the book
        book = state_manager.get_book(request.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Validate dependencies
        validate_generation_step(book, GenerationStep.CHAPTER_PLAN)

        # Generate chapter plan
        writing_agent.generate_chapter_plan(book)

        # Update the book in state
        state_manager.update_book(request.book_id, book)

        return GenerateChapterPlanResponse(
            book_id=request.book_id, chapters=book.chapters
        )

    except HTTPException:
        raise
    except DependencyValidationError as e:
        logger.error(f"Dependency validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chapter plan generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Chapter plan generation failed: {str(e)}"
        )


@app.post("/generate/chapter-content", response_model=GenerateChapterContentResponse)
async def generate_chapter_content(request: GenerateChapterContentRequest):
    """Generate chapter content (enforces sequential order)."""
    try:
        # Get the book
        book = state_manager.get_book(request.book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        # Validate dependencies
        validate_generation_step(
            book, GenerationStep.CHAPTER_CONTENT, request.chapter_number
        )

        # Find the target chapter
        target_chapter = next(
            (ch for ch in book.chapters if ch.chapter_number == request.chapter_number),
            None,
        )

        # Generate chapter content
        writing_agent.write_chapter_content(book, target_chapter)

        # Update the book in state
        state_manager.update_book(request.book_id, book)

        return GenerateChapterContentResponse(
            book_id=request.book_id,
            chapter_number=target_chapter.chapter_number,
            chapter_title=target_chapter.title,
            content=target_chapter.content,
        )

    except HTTPException:
        raise
    except DependencyValidationError as e:
        logger.error(f"Dependency validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Chapter content generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Chapter content generation failed: {str(e)}"
        )


@app.get("/books/{book_id}", response_model=BookStateResponse)
async def get_book(book_id: UUID):
    """Retrieve the complete state of a book."""
    try:
        book = state_manager.get_book(book_id)

        # Validate book exists (reusing our validator for consistency)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        return BookStateResponse.from_book(book_id, book)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Book retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Book retrieval failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    backend_info = writing_agent.get_backend_info()
    return {
        "status": "healthy",
        "backend": backend_info,
        "books_in_memory": len(state_manager.list_books()),
    }
