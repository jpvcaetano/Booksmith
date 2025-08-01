# 📚 Booksmith

AI-powered book generation library that creates complete novels from simple prompts using OpenAI's GPT models.

![Booksmith Front Page](images/front_page.png)

## Features

- **Complete Book Generation**: Characters, plot, chapters, and EPUB output
- **OpenAI Integration**: High-quality generation using GPT models with automatic retry logic
- **REST API**: FastAPI-based web service for remote book generation
- **Structured Output**: Reliable JSON generation with validation
- **EPUB Export**: Professional ebook files with proper chapter structure
- **Jupyter Integration**: Interactive notebooks for experimentation
- **Robust Error Handling**: Automatic retries with timeout protection and progress feedback

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

# Configure OpenAI with retry settings
config = LLMConfig(
    model_name="gpt-4",
    api_key=os.environ.get("OPENAI_API_KEY"),
    timeout_seconds=60,  # Request timeout
    max_retries=3,       # Retry attempts
    retry_delay=5.0      # Delay between retries
)

# Create agent and book
agent = WritingAgent(config)
book = Book(
    base_prompt="A young wizard discovers a hidden library that contains books about the future",
    genre="fantasy",
    language="english"
)

# Generate complete book with progress feedback
def progress_callback(message: str):
    print(f"📝 {message}")

agent = WritingAgent(config, progress_callback=progress_callback)
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
- Internet connection for API calls

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

### Error Handling

The generation process includes robust error handling:
- **Automatic Retries**: Failed API calls are retried up to 3 times
- **Timeout Protection**: 60-second timeout prevents hanging requests
- **Partial Success**: Generation continues even if some steps fail
- **Progress Feedback**: Real-time updates during long operations
- **Manual Retry**: Individual chapters can be regenerated if needed

## Interactive Notebooks

```bash
jupyter notebook notebooks/book_generation.ipynb
```

## Project Structure

```
booksmith/
├── generation/     # Core generation engine with retry logic
├── models/         # Book, Chapter, Character models  
├── utils/          # EPUB generation
└── web/           # Streamlit web interface
```

## License

MIT License
