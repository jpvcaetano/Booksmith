# 📚 Booksmith

AI-powered book generation library that creates complete novels from simple prompts using OpenAI's GPT models.

## Features

- **Complete Book Generation**: Characters, plot, chapters, and EPUB output
- **OpenAI Integration**: High-quality generation using GPT models
- **REST API**: FastAPI-based web service for remote book generation
- **Structured Output**: Reliable JSON generation with validation
- **EPUB Export**: Professional ebook files with proper chapter structure
- **Jupyter Integration**: Interactive notebooks for experimentation

## Quick Start

### Installation

```bash
git clone <repository-url>
cd Booksmith
poetry install
```

### Basic Usage

```python
import os
from booksmith import Book, WritingAgent, LLMConfig

# Configure OpenAI
config = LLMConfig(
    model_name="gpt-4",
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Create agent and book
agent = WritingAgent(config)
book = Book(
    base_prompt="A young wizard discovers a hidden library that contains books about the future",
    genre="fantasy",
    language="english"
)

# Generate complete book
agent.write_full_book(book)

# Export to EPUB
from booksmith.utils.epub_generator import create_book_epub
create_book_epub(book, output_dir="my_books")
```

## REST API

Booksmith also provides a REST API for web applications and remote book generation:

```bash
# Start the API server
python run_api.py
```

The API will be available at `http://localhost:8000` with:
- **Interactive docs**: `/docs` (Swagger UI)
- **Alternative docs**: `/redoc` (ReDoc)

### API Endpoints

- `POST /generate/summary` - Generate story summary from prompt
- `POST /generate/title` - Generate book titles
- `POST /generate/characters` - Generate character profiles  
- `POST /generate/chapter-plan` - Generate chapter outlines
- `POST /generate/chapter-content` - Generate chapter content
- `GET /books/{book_id}` - Retrieve book state
- `GET /health` - Health check

## Requirements

- Python 3.13+
- OpenAI API key

## Environment Setup

Create a `.env` file:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Generation Process

1. **Story Summary** - Expands prompt into detailed plot
2. **Title Generation** - Creates compelling book titles  
3. **Character Development** - Generates character profiles
4. **Chapter Planning** - Outlines chapter structure
5. **Content Writing** - Writes full chapters with continuity
6. **EPUB Export** - Creates professional ebook files

## Interactive Notebooks

```bash
jupyter notebook notebooks/book_generation.ipynb
```

## Project Structure

```
booksmith/
├── generation/     # Core generation engine
├── models/         # Book, Chapter, Character models  
└── utils/          # EPUB generation
```

## License

MIT License
