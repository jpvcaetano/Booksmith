import sys
import os
import pickle
import gzip
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.getcwd()))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import Booksmith modules
from booksmith import (
    Book, Character, Chapter,
    LLMConfig,
    WritingAgent
)

# Import EPUB generator
from booksmith.utils.epub_generator import create_book_epub

print("✅ Modules imported successfully")

# Configure OpenAI backend
config = LLMConfig(
    model_name="gpt-4.1", 
    max_tokens=32768, 
    temperature=0.7, 
    api_key=os.environ.get("OPENAI_API_KEY")
)

# Initialize agent
agent = WritingAgent(config)

print(f"✅ Agent initialized with OpenAI backend")
print(f"📦 Model: {config.model_name}")
print(f"💾 Memory usage: {agent.get_memory_usage()}")

# Create book with your prompt and preferences
book = Book(
    base_prompt="A Clara Costa é enfermeira nos cuidados intensivos num hospital e o João Caetano é Engenheiro de IA. A Clara é elegante e magra, com um cabelo e uns olhos lindos castanhos. O João é mais bem constituido, tem cabelo e olhos castanhos escuros. Eles estão noivos e moram juntos num pequeno apartamento em Moscavide. Gostam muito de ir a Tavira, é o happy place deles. Os dois iam para lá com as respectivas familias desde pequenos sem nunca se teram encontrado lá. Os dois são o maximo felizes quando lá estão juntos. O João gosta também muito de hikes e contacto com a natureza mas a Clara perfere ficar mais por casa ou ir à praia. Os dois são muito amigos estando sempre na galhofa. A historia é passada maioritariamente em Tavira",
    genre="Literary Fiction",
    writing_style="Sophia de Mello Breyner Andresen writing style",
    target_audience="Children and Young Readers",
    language="portuguese from Portugal"
)

print("📚 Book initialized")
print(f"Genre: {book.genre}")
print(f"Style: {book.writing_style}")
print(f"Language: {book.language}")

# Generate story summary
agent.generate_story_summary(book)

print("✅ Story summary generated")
print(f"📝 Summary ({len(book.story_summary)} chars):")
print("-" * 50)
print(book.story_summary)
print("-" * 50)
