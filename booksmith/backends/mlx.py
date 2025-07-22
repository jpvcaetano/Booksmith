"""
MLX backend implementation for Apple Silicon optimization.
"""

import logging
from .base import LLMBackend

logger = logging.getLogger(__name__)

class MLXBackend(LLMBackend):
    """Apple MLX backend optimized for Apple Silicon."""
    
    def __init__(self, config):
        super().__init__(config)
        self.model = None
        self.tokenizer = None
        self._setup_model()
    
    def _setup_model(self):
        """Initialize the MLX model."""
        try:
            from mlx_lm import load
            import platform
            
            # Check if we're on Apple Silicon
            if platform.machine() != 'arm64':
                logger.warning("MLX backend works best on Apple Silicon (M1/M2/M3/M4)")
            
            logger.info(f"Loading MLX model: {self.config.model_name}")
            logger.info("MLX backend will automatically optimize for Apple Silicon")
            
            # Load model using MLX - automatically optimized
            self.model, self.tokenizer = load(self.config.model_name)
            
            logger.info(f"MLX model loaded successfully")
            logger.info(f"Model will use unified memory efficiently on Apple Silicon")
            
        except ImportError:
            logger.error("MLX-LM not installed. Install with: pip install mlx-lm")
            self.model = None
            self.tokenizer = None
        except Exception as e:
            logger.error(f"Failed to setup MLX model: {e}")
            self.model = None
            self.tokenizer = None
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using MLX optimized inference."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("MLX model not available")
        
        # Get generation parameters
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        temperature = kwargs.get('temperature', self.config.temperature)
        top_p = kwargs.get('top_p', 0.9)
        
        try:
            from mlx_lm import generate
            
            # MLX generate function with optimized parameters
            response = generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                temp=temperature,
                top_p=top_p,
                verbose=False  # Reduce output noise
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"MLX generation failed: {e}")
            return f"Error: Failed to generate text - {str(e)}"
    
    def is_available(self) -> bool:
        """Check if MLX model is loaded and ready."""
        return self.model is not None and self.tokenizer is not None
    
    def get_model_info(self) -> dict:
        """Get MLX model information."""
        if not self.model:
            return {"status": "not_loaded"}
        
        import platform
        return {
            "status": "loaded",
            "model_name": self.config.model_name,
            "backend": "mlx",
            "platform": platform.machine(),
            "optimized_for": "Apple Silicon" if platform.machine() == 'arm64' else "Generic",
            "memory_efficient": True,
            "gpu_acceleration": "Metal" if platform.machine() == 'arm64' else "None"
        }
    
    def estimate_memory_usage(self) -> float:
        """Estimate memory usage for MLX models (they're automatically optimized)."""
        if not self.model:
            return 0.0
        
        # MLX models are typically quantized and optimized
        # This is a rough estimate - actual usage will be lower due to MLX optimizations
        model_name = self.config.model_name.lower()
        
        if "3b" in model_name:
            return 2.0  # ~2GB for 3B models
        elif "7b" in model_name or "dclm" in model_name:
            return 4.0  # ~4GB for 7B models  
        elif "8b" in model_name:
            return 4.5  # ~4.5GB for 8B models
        elif "12b" in model_name or "nemo" in model_name:
            return 6.0  # ~6GB for 12B models
        elif "22b" in model_name or "small" in model_name:
            return 10.0  # ~10GB for 22B models
        elif "70b" in model_name:
            return 35.0  # ~35GB for 70B models
        else:
            return 5.0  # Default estimate 