# 📚 Booksmith

AI-powered book generation library that creates complete novels from simple prompts using Large Language Models.

## ✨ Features

- **🤖 Multiple LLM Backends**: OpenAI, HuggingFace Transformers, Apple MLX
- **📖 Complete Book Generation**: Characters, plot, chapters, and EPUB output
- **🎯 Structured Output**: Reliable JSON generation with validation and fallbacks
- **📱 Jupyter Integration**: Interactive notebooks for easy experimentation
- **🍎 Apple Silicon Optimized**: Efficient MLX backend for M-series Macs
- **🌍 Multilingual**: Support for multiple languages and writing styles

## 🚀 Quick Start

### Installation

```bash
# Install with Poetry (recommended)
poetry install
```

### Basic Usage

```python
from booksmith import Book, WritingAgent, LLMConfig

# 1. Choose your backend
config = LLMConfig(
    backend="openai",  # or "huggingface", "mlx"
    model_name="gpt-4",
    api_key="your-api-key"
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
create_book_epub(book, output_dir="my_books")
```

## 🔧 Supported Backends

### OpenAI (Recommended for quality)
```python
config = LLMConfig(
    backend="openai",
    model_name="gpt-4", 
    api_key="your-key"
)
```

### Apple MLX (Recommended for M-series Macs)
```python
config = LLMConfig(
    backend="mlx",
    model_name="mlx-community/Llama-3.2-3B-Instruct-4bit"  # 2GB, perfect for 16GB RAM
)
```

### HuggingFace (Universal local models)
```python
config = LLMConfig(
    backend="huggingface", 
    model_name="microsoft/DialoGPT-medium",
    device="auto"
)
```

## 📖 Generation Process

Booksmith generates books through a structured pipeline:

1. **Story Summary** - Expands your prompt into a detailed plot
2. **Title Generation** - Creates compelling book titles  
3. **Character Development** - Generates detailed character profiles
4. **Chapter Planning** - Outlines chapter structure and plot points
5. **Content Writing** - Writes full chapter content with continuity
6. **EPUB Export** - Creates professional ebook files

## 🎮 Interactive Notebooks

Use the included Jupyter notebook for step-by-step book generation:

```bash
jupyter notebook notebooks/book_generation.ipynb
```

Perfect for experimenting with different prompts, styles, and backends.

## 🏗️ Project Structure

```
booksmith/
├── backends/          # LLM backend implementations
├── generation/        # Core generation engine and prompts
├── models/           # Data models (Book, Chapter, Character)
├── utils/            # EPUB generation utilities
└── notebooks/        # Interactive Jupyter notebooks
```

## 📋 Requirements

- Python 3.9+
- For OpenAI: API key and `openai` package
- For local models: `transformers`, `torch`
- For Apple Silicon: `mlx-lm` package
- For EPUB generation: `ebooklib`

## 🤝 Contributing

This is an open-source project. Feel free to contribute improvements, new backends, or additional features!

## 📄 License

MIT License - see LICENSE file for details.
