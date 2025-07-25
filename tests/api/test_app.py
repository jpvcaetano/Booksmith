"""
Integration tests for Booksmith API endpoints.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from booksmith.api.app import app, state_manager


@pytest.fixture
def client():
    """Test client fixture with clean state."""
    state_manager.clear_all()  # Reset state before each test
    return TestClient(app)


@pytest.fixture
def mock_writing_agent(sample_character, sample_chapters):
    """Mock the WritingAgent methods to return deterministic values using shared fixtures."""
    mock = MagicMock()

    def generate_story_summary(book):
        book.story_summary = "A young mage discovers her powers and faces an ancient evil threatening her world."

    def generate_title(book):
        book.title = "The Magic Within"

    def generate_characters(book):
        book.characters = [sample_character]

    def generate_chapter_plan(book):
        # Use the sample chapters but ensure they start without content
        chapters = [
            sample_chapters[0].model_copy(update={"content": ""}),
            sample_chapters[1].model_copy(update={"content": ""}),
        ]
        book.chapters = chapters

    def write_chapter_content(book, chapter):
        chapter.content = f"Generated content for {chapter.title}: {chapter.summary}"

    mock.generate_story_summary.side_effect = generate_story_summary
    mock.generate_title.side_effect = generate_title
    mock.generate_characters.side_effect = generate_characters
    mock.generate_chapter_plan.side_effect = generate_chapter_plan
    mock.write_chapter_content.side_effect = write_chapter_content

    with patch("booksmith.api.app.writing_agent", mock):
        yield mock


class TestAPIEndpoints:
    """Test class for API endpoints."""

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Booksmith API"
        assert "version" in data
        assert "endpoints" in data
        assert len(data["endpoints"]) == 6

    def test_health_check(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "backend" in data
        assert "books_in_memory" in data

    def test_generate_summary_success(self, client, mock_writing_agent):
        """Test successful story summary generation."""
        response = client.post(
            "/generate/summary",
            json={
                "base_prompt": "A magical adventure story",
                "language": "english",
                "writing_style": "descriptive",
                "genre": "fantasy",
                "target_audience": "young adults",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "story_summary" in data
        assert (
            data["story_summary"]
            == "A young mage discovers her powers and faces an ancient evil threatening her world."
        )

        # Verify the writing agent was called
        mock_writing_agent.generate_story_summary.assert_called_once()

    def test_generate_summary_minimal(self, client, mock_writing_agent):
        """Test summary generation with minimal data (using defaults)."""
        response = client.post(
            "/generate/summary", json={"base_prompt": "A simple story"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "book_id" in data
        assert "story_summary" in data

    def test_generate_title_success(self, client, mock_writing_agent):
        """Test successful title generation."""
        # First create a book with summary
        summary_response = client.post(
            "/generate/summary", json={"base_prompt": "A magical story"}
        )
        book_id = summary_response.json()["book_id"]

        # Then generate title
        response = client.post("/generate/title", json={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book_id
        assert data["title"] == "The Magic Within"

    def test_generate_title_book_not_found(self, client):
        """Test title generation with invalid book ID."""
        fake_book_id = str(uuid.uuid4())
        response = client.post("/generate/title", json={"book_id": fake_book_id})
        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]

    def test_generate_title_no_summary(self, client, mock_writing_agent):
        """Test title generation when summary doesn't exist."""
        # Create a book but don't generate summary (simulate empty book)
        book_id, book = state_manager.create_book(base_prompt="Test")

        response = client.post("/generate/title", json={"book_id": str(book_id)})
        assert response.status_code == 400
        assert (
            "Missing dependencies for title: story_summary" in response.json()["detail"]
        )

    def test_generate_characters_success(self, client, mock_writing_agent):
        """Test successful character generation."""
        # Create book with summary
        summary_response = client.post(
            "/generate/summary", json={"base_prompt": "A magical story"}
        )
        book_id = summary_response.json()["book_id"]

        # Generate characters
        response = client.post("/generate/characters", json={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book_id
        assert len(data["characters"]) == 1
        assert data["characters"][0]["name"] == "Test Hero"

    def test_generate_chapter_plan_success(self, client, mock_writing_agent):
        """Test successful chapter plan generation."""
        # Create book with summary
        summary_response = client.post(
            "/generate/summary", json={"base_prompt": "A magical story"}
        )
        book_id = summary_response.json()["book_id"]

        # Generate characters
        client.post("/generate/characters", json={"book_id": book_id})

        # Generate chapter plan
        response = client.post("/generate/chapter-plan", json={"book_id": book_id})
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book_id
        assert len(data["chapters"]) == 2
        assert data["chapters"][0]["title"] == "The Beginning"
        assert data["chapters"][1]["title"] == "The Journey"

    def test_generate_chapter_content_success(self, client, mock_writing_agent):
        """Test successful chapter content generation."""
        # Setup: Create book, summary, and chapter plan
        summary_response = client.post(
            "/generate/summary", json={"base_prompt": "A magical story"}
        )
        book_id = summary_response.json()["book_id"]

        # Generate characters
        client.post("/generate/characters", json={"book_id": book_id})

        # Generate chapter plan
        client.post("/generate/chapter-plan", json={"book_id": book_id})

        # Generate chapter 1 content
        response = client.post(
            "/generate/chapter-content", json={"book_id": book_id, "chapter_number": 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book_id
        assert data["chapter_number"] == 1
        assert data["chapter_title"] == "The Beginning"
        assert "Generated content for The Beginning" in data["content"]

    def test_generate_chapter_content_sequential_enforcement(
        self, client, mock_writing_agent
    ):
        """Test that chapters must be generated sequentially."""
        # Setup: Create book, summary, and chapter plan
        summary_response = client.post(
            "/generate/summary", json={"base_prompt": "A magical story"}
        )
        book_id = summary_response.json()["book_id"]

        # Generate characters
        client.post("/generate/characters", json={"book_id": book_id})

        # Generate chapter plan
        client.post("/generate/chapter-plan", json={"book_id": book_id})

        # Try to generate chapter 2 before chapter 1
        response = client.post(
            "/generate/chapter-content", json={"book_id": book_id, "chapter_number": 2}
        )
        assert response.status_code == 400
        assert "must be written before" in response.json()["detail"]

    def test_generate_chapter_content_already_exists(self, client, mock_writing_agent):
        """Test error when trying to regenerate existing chapter content."""
        # Setup: Create book, summary, chapter plan, and generate chapter 1
        summary_response = client.post(
            "/generate/summary", json={"base_prompt": "A magical story"}
        )
        book_id = summary_response.json()["book_id"]
        # Generate characters
        client.post("/generate/characters", json={"book_id": book_id})

        # Generate chapter plan
        client.post("/generate/chapter-plan", json={"book_id": book_id})

        # Generate chapter 1 content
        response = client.post(
            "/generate/chapter-content", json={"book_id": book_id, "chapter_number": 1}
        )

        # Try to generate chapter 1 again
        response = client.post(
            "/generate/chapter-content", json={"book_id": book_id, "chapter_number": 1}
        )
        assert response.status_code == 400
        assert "already has content" in response.json()["detail"]

    def test_get_book_success(self, client, mock_writing_agent):
        """Test successful book state retrieval."""
        # Create a complete book
        summary_response = client.post(
            "/generate/summary", json={"base_prompt": "A magical story"}
        )
        book_id = summary_response.json()["book_id"]
        client.post("/generate/title", json={"book_id": book_id})
        client.post("/generate/characters", json={"book_id": book_id})
        client.post("/generate/chapter-plan", json={"book_id": book_id})

        # Get book state
        response = client.get(f"/books/{book_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book_id
        assert data["title"] == "The Magic Within"
        assert len(data["characters"]) == 1
        assert len(data["chapters"]) == 2
        assert data["base_prompt"] == "A magical story"

    def test_get_book_not_found(self, client):
        """Test book retrieval with invalid book ID."""
        fake_book_id = str(uuid.uuid4())
        response = client.get(f"/books/{fake_book_id}")
        assert response.status_code == 404
        assert "Book not found" in response.json()["detail"]


class TestFullGenerationFlow:
    """Test the complete book generation flow."""

    def test_complete_book_generation_flow(self, client, mock_writing_agent):
        """Test the complete flow from summary to finished chapters."""
        # Step 1: Generate summary
        response = client.post(
            "/generate/summary",
            json={
                "base_prompt": "A magical adventure story",
                "genre": "fantasy",
                "target_audience": "young adults",
            },
        )
        assert response.status_code == 200
        book_id = response.json()["book_id"]

        # Step 2: Generate title
        response = client.post("/generate/title", json={"book_id": book_id})
        assert response.status_code == 200
        assert response.json()["title"] == "The Magic Within"

        # Step 3: Generate characters
        response = client.post("/generate/characters", json={"book_id": book_id})
        assert response.status_code == 200
        assert len(response.json()["characters"]) == 1

        # Step 4: Generate chapter plan
        response = client.post("/generate/chapter-plan", json={"book_id": book_id})
        assert response.status_code == 200
        chapters = response.json()["chapters"]
        assert len(chapters) == 2

        # Step 5: Generate chapter content sequentially
        for chapter_num in [1, 2]:
            response = client.post(
                "/generate/chapter-content",
                json={"book_id": book_id, "chapter_number": chapter_num},
            )
            assert response.status_code == 200
            assert response.json()["chapter_number"] == chapter_num

        # Step 6: Verify final book state
        response = client.get(f"/books/{book_id}")
        assert response.status_code == 200
        book_data = response.json()
        assert book_data["title"] == "The Magic Within"
        assert len(book_data["characters"]) == 1
        assert len(book_data["chapters"]) == 2

        # Verify all chapters have content
        for chapter in book_data["chapters"]:
            assert chapter["content"] != ""
            assert "Generated content" in chapter["content"]
