"""
Factory function and model recommendations for LLM backends.
"""

from .base import LLMConfig, LLMBackend
from .huggingface import HuggingFaceBackend
from .mlx import MLXBackend
from .openai import OpenAIBackend

def create_llm_backend(config: LLMConfig) -> LLMBackend:
    """Factory function to create appropriate LLM backend."""
    
    if config.backend.lower() == "huggingface":
        return HuggingFaceBackend(config)
    elif config.backend.lower() == "openai":
        return OpenAIBackend(config)
    elif config.backend.lower() == "mlx":
        return MLXBackend(config)
    else:
        raise ValueError(f"Unsupported backend: {config.backend}")

# Recommended model configurations following HF best practices
RECOMMENDED_MODELS = {
    "huggingface": {
        # Small models for testing and development
        "tiny": "microsoft/DialoGPT-small",  # ~350MB, very fast, basic quality
        "small": "microsoft/DialoGPT-medium",  # ~1GB, good for testing
        
        # Medium models - good balance of size/quality
        "medium": "microsoft/DialoGPT-large",  # ~2GB, better quality
        "instruct": "microsoft/DialoGPT-large",  # ~2GB, instruction-tuned
        
        # Large models - production quality (require HF login for some)
        "large": "meta-llama/Llama-2-7b-chat-hf",  # ~13GB, excellent quality
        "code": "codellama/CodeLlama-7b-Instruct-hf",  # ~13GB, structured output
        
        # Alternative high-quality models (no login required)
        "mistral": "mistralai/Mistral-7B-Instruct-v0.1",  # ~13GB, excellent for chat
        "openchat": "openchat/openchat-3.5-1210",  # ~7GB, good instruction following
        
        # Smaller but capable models
        "phi": "microsoft/phi-2",  # ~3GB, surprisingly capable for size
        "tinyllama": "TinyLlama/TinyLlama-1.1B-Chat-v1.0",  # ~1GB, very fast
    },
    "mlx": {
        # Apple optimized models (perfect for M4 MacBook Air 16GB)
        "tiny": "mlx-community/Llama-3.2-1B-Instruct-4bit",  # ~1GB, very fast
        "small": "mlx-community/Llama-3.2-3B-Instruct-4bit",  # ~2GB, excellent for 16GB
        "apple": "apple/DCLM-7B",  # ~4GB, Apple's own model
        "balanced": "mlx-community/Llama-3.2-8B-Instruct-4bit",  # ~4.5GB, good quality
        
        # Medium models (require more RAM but excellent quality)
        "medium": "mlx-community/Mistral-Nemo-12B-Instruct-2407-4bit",  # ~6GB, great reasoning
        "large": "mlx-community/Mistral-Small-22B-Instruct-4bit",  # ~10GB, high quality
        
        # Large models (need 128GB+ RAM)
        "huge": "mlx-community/Llama-3.3-70B-Instruct-4bit",  # ~35GB, excellent quality
        "premium": "mlx-community/Mistral-Large-123B-4bit",  # ~62GB, top tier
        
        # Specialized models
        "code": "mlx-community/CodeLlama-7B-Instruct-4bit",  # ~4GB, coding optimized
        "creative": "mlx-community/Llama-3.2-8X3B-MOE-Dark-Champion-4bit",  # ~8GB, creative writing
    },
    "openai": {
        "fast": "gpt-3.5-turbo",
        "quality": "gpt-4.1 ",
        "latest": "gpt-4-turbo-preview"
    }
}

# Model categories for easy selection
MODEL_CATEGORIES = {
    "development": ["tiny", "small", "tinyllama"],  # Fast models for testing
    "balanced": ["medium", "phi", "openchat", "apple"],      # Good balance of speed/quality  
    "production": ["large", "mistral", "code"],     # High quality for final books
    "apple_silicon": ["apple", "small", "balanced", "medium"],  # Optimized for M4 MacBook Air
} 