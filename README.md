# 📚 Booksmith

AI-powered book generation library that creates complete novels from simple prompts using Large Language Models.

## ✨ Features

- **🤖 OpenAI Integration**: Professional-quality generation using GPT models
- **📖 Complete Book Generation**: Characters, plot, chapters, and EPUB output
- **🎯 Structured Output**: Reliable JSON generation with validation and fallbacks
- **📱 Jupyter Integration**: Interactive notebooks for easy experimentation
- **🌍 Multilingual**: Support for multiple languages and writing styles
- **📚 EPUB Export**: Professional ebook generation with proper chapter structure

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd Booksmith

# Install with Poetry (recommended)
poetry install
```

### Basic Usage

```python
import os
from booksmith import Book, WritingAgent, LLMConfig

# 1. Configure OpenAI backend
config = LLMConfig(
    model_name="gpt-4", 
    max_tokens=4000,
    temperature=0.7,
    api_key=os.environ.get("OPENAI_API_KEY")  # Set your API key
)

# 2. Initialize agent
agent = WritingAgent(config)

# 3. Create book from prompt
book = Book(
    base_prompt="A young wizard discovers a hidden library that contains books about the future",
    genre="fantasy",
    language="english",
    target_audience="young adults"
)

# 4. Generate complete book
agent.write_full_book(book)

# 5. Export to EPUB
from booksmith.utils.epub_generator import create_book_epub
book_folder = create_book_epub(book, output_dir="my_books")
print(f"Book saved to: {book_folder}")
```

## 🔧 Supported Backend

### OpenAI (Currently Supported)
```python
config = LLMConfig(
    model_name="gpt-4",  # or "gpt-3.5-turbo", "gpt-4-turbo", etc.
    max_tokens=4000,
    temperature=0.7,
    api_key="your-api-key"
)
```

**Requirements**: 
- OpenAI API key
- `openai` package (included in dependencies)

## 📖 Generation Process

Booksmith generates books through a structured pipeline:

1. **Story Summary** - Expands your prompt into a detailed plot (300-500 words)
2. **Title Generation** - Creates compelling book titles with multiple options
3. **Character Development** - Generates detailed character profiles with personalities, backgrounds, and appearances
4. **Chapter Planning** - Outlines chapter structure with summaries, key characters, and plot points
5. **Content Writing** - Writes full chapter content with narrative continuity
6. **EPUB Export** - Creates professional ebook files with proper structure

## 🎮 Interactive Notebooks

Use the included Jupyter notebook for step-by-step book generation:

```bash
# Start Jupyter
jupyter notebook notebooks/book_generation.ipynb
```

The notebook provides:
- Step-by-step generation process
- Real-time progress tracking
- Portuguese and English examples
- EPUB generation and export

## 🏗️ Project Structure

```
Booksmith/
├── booksmith/
│   ├── generation/        # Core generation engine and OpenAI backend
│   │   ├── agent.py      # Main WritingAgent class
│   │   ├── openai.py     # OpenAI backend implementation
│   │   ├── prompts.py    # Template system for prompts
│   │   ├── schemas.py    # JSON schemas for structured output
│   │   └── validation.py # Response validation and parsing
│   ├── models/           # Data models (Book, Chapter, Character)
│   │   ├── book.py
│   │   ├── chapter.py
│   │   └── character.py
│   └── utils/            # EPUB generation utilities
│       └── epub_generator.py
├── notebooks/            # Interactive Jupyter notebooks
│   └── book_generation.ipynb
├── pyproject.toml        # Project dependencies
└── README.md
```

## 📋 Requirements

- **Python 3.9+**
- **OpenAI API key** (required for generation)
- Dependencies automatically installed via Poetry:
  - `openai` - OpenAI API client
  - `pydantic` - Data validation
  - `ebooklib` - EPUB generation
  - `python-dotenv` - Environment variable management
  - `jupyter` - Interactive notebooks (dev dependency)

## 🔧 Environment Setup

1. Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

2. The library will automatically load your API key from the environment.

## 📚 Example Output

The library generates:
- **EPUB files** - Professional ebook format with proper chapter navigation
- **Book info text files** - Summary of characters, plot, and chapter structure
- **Pickle files** - Serialized Book objects for reloading and modification

## 🌟 Advanced Features

### Structured Output
- Uses OpenAI's JSON mode for reliable structured generation
- Automatic fallback to regex parsing if JSON fails
- Schema validation with auto-correction

### Multilingual Support
- Supports generation in multiple languages
- Portuguese examples included in notebook
- Customizable writing styles and genres

### Chapter Continuity
- Each chapter receives context from previous chapters
- Story arc awareness for better narrative flow
- Character consistency across chapters

## 🤝 Contributing

This project is under active development. Contributions are welcome!

Areas for future development:
- Additional LLM backends (HuggingFace, local models)
- Enhanced customization options
- Better error handling and recovery

## 📄 License

MIT License - see LICENSE file for details.
