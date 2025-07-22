"""
OpenAI API backend implementation.
"""

import logging
from .base import LLMBackend

logger = logging.getLogger(__name__)

class OpenAIBackend(LLMBackend):
    """OpenAI API backend."""
    
    def __init__(self, config):
        super().__init__(config)
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI
            
            if not self.config.api_key:
                logger.warning("No OpenAI API key provided")
                return
            
            self.client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.api_base
            )
            
        except ImportError:
            logger.error("OpenAI package not installed. Install with: poetry install -E api")
        except Exception as e:
            logger.error(f"Failed to setup OpenAI client: {e}")
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI API."""
        if not self.client:
            raise RuntimeError("OpenAI client not available")
        
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        temperature = kwargs.get('temperature', self.config.temperature)
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"Error: Failed to generate text - {str(e)}"
    
    def is_available(self) -> bool:
        """Check if OpenAI client is ready."""
        return self.client is not None 