"""
HuggingFace backend implementation for local models.
"""

import logging
from .base import LLMBackend

logger = logging.getLogger(__name__)

class HuggingFaceBackend(LLMBackend):
    """Local Hugging Face model backend following HF best practices."""
    
    def __init__(self, config):
        super().__init__(config)
        self.model = None
        self.tokenizer = None
        self.device = None
        self._setup_model()
    
    def _setup_model(self):
        """Initialize the Hugging Face model following best practices."""
        try:
            from transformers import (
                AutoModelForCausalLM, 
                AutoTokenizer, 
                GenerationConfig,
                BitsAndBytesConfig
            )
            import torch
            
            # Determine optimal device
            self.device = self._get_optimal_device()
            logger.info(f"Using device: {self.device}")
            
            # Load tokenizer first
            logger.info(f"Loading tokenizer for {self.config.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model_name,
                trust_remote_code=True,
                padding_side="left"  # Important for generation
            )
            
            # Set pad token if not present
            if self.tokenizer.pad_token is None:
                if self.tokenizer.eos_token is not None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                else:
                    self.tokenizer.add_special_tokens({'pad_token': '[PAD]'})
            
            # Determine optimal model loading configuration
            model_kwargs = self._get_model_kwargs()
            
            logger.info(f"Loading model {self.config.model_name}")
            logger.info(f"Model config: {model_kwargs}")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.model_name,
                **model_kwargs
            )
            
            # Move to device if not already there
            if str(self.model.device) != str(self.device):
                self.model = self.model.to(self.device)
            
            # Set to evaluation mode
            self.model.eval()
            
            # Resize token embeddings if tokenizer was modified
            if len(self.tokenizer) != self.model.config.vocab_size:
                self.model.resize_token_embeddings(len(self.tokenizer))
            
            logger.info(f"Model loaded successfully on {self.device}")
            logger.info(f"Model memory footprint: ~{self._estimate_memory_usage():.1f} GB")
            
        except Exception as e:
            logger.error(f"Failed to setup Hugging Face model: {e}")
            self.model = None
            self.tokenizer = None
    
    def _get_optimal_device(self):
        """Determine the best device for model loading."""
        import torch
        
        if self.config.device != "auto":
            return self.config.device
        
        # Auto-detect best device
        if torch.cuda.is_available():
            device = f"cuda:{torch.cuda.current_device()}"
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info(f"CUDA available with {gpu_memory:.1f}GB memory")
            return device
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("Apple Silicon MPS available")
            return "mps"
        else:
            logger.info("Using CPU")
            return "cpu"
    
    def _get_model_kwargs(self):
        """Get optimal model loading arguments based on device and memory."""
        import torch
        
        kwargs = {
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,  # HF best practice
            "device_map": None  # We'll handle device placement manually
        }
        
        # Set optimal torch_dtype based on device
        if "cuda" in str(self.device):
            # Use float16 for GPU to save memory
            kwargs["torch_dtype"] = torch.float16
            
            # Add quantization for large models if memory constrained
            try:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                if gpu_memory < 16:  # Less than 16GB VRAM
                    logger.info("Limited GPU memory detected, enabling 8-bit quantization")
                    from transformers import BitsAndBytesConfig
                    kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_8bit=True,
                        llm_int8_threshold=6.0,
                        llm_int8_has_fp16_weight=False,
                    )
            except ImportError:
                logger.warning("bitsandbytes not available, skipping quantization")
                
        elif self.device == "mps":
            # Use float32 for MPS (better compatibility)
            kwargs["torch_dtype"] = torch.float32
        else:
            # Use float32 for CPU
            kwargs["torch_dtype"] = torch.float32
        
        return kwargs
    
    def _estimate_memory_usage(self):
        """Estimate model memory usage in GB."""
        if not self.model:
            return 0
        
        param_count = sum(p.numel() for p in self.model.parameters())
        # Rough estimate: 4 bytes per parameter for float32, 2 for float16
        bytes_per_param = 2 if self.model.dtype == torch.float16 else 4
        return (param_count * bytes_per_param) / 1e9
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using the local model with optimized settings."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not available")
        
        # Get generation parameters
        max_tokens = kwargs.get('max_tokens', self.config.max_tokens)
        temperature = kwargs.get('temperature', self.config.temperature)
        top_p = kwargs.get('top_p', 0.9)
        top_k = kwargs.get('top_k', 50)
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048  # Reasonable context window
            ).to(self.device)
            
            # Prepare generation config
            generation_config = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "do_sample": temperature > 0,
                "pad_token_id": self.tokenizer.pad_token_id,
                "eos_token_id": self.tokenizer.eos_token_id,
                "use_cache": True,  # Speed optimization
                "repetition_penalty": 1.1,  # Reduce repetition
            }
            
            # Generate with no_grad for memory efficiency
            import torch
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    **generation_config
                )
            
            # Decode only the new tokens
            input_length = inputs.input_ids.shape[1]
            generated_tokens = outputs[0][input_length:]
            
            generated_text = self.tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error: Failed to generate text - {str(e)}"
    
    def generate_structured(self, prompt: str, schema: Optional[Dict[str, Any]] = None, **kwargs):
        """Generate structured output with JSON instruction prompts."""
        import json
        from typing import Dict, Any, Optional, Union
        
        if not schema or not self.config.use_json_mode:
            # Fall back to regular generation
            return self.generate(prompt, **kwargs)
        
        # Add JSON instruction to prompt for better structured output
        json_prompt = f"""{prompt}

IMPORTANT: Respond with valid JSON that matches this exact schema:
{json.dumps(schema, indent=2)}

Your response must be valid JSON only, no additional text or formatting."""
        
        try:
            response_text = self.generate(json_prompt, **kwargs)
            
            # Try to parse as JSON
            try:
                parsed_json = json.loads(response_text)
                
                # Basic validation if schema enforcement is enabled
                if self.config.enforce_schema:
                    self._validate_json_schema(parsed_json, schema)
                
                return parsed_json
                
            except json.JSONDecodeError as e:
                logger.warning(f"Generated text is not valid JSON: {e}")
                if self.config.enforce_schema:
                    # Try to extract JSON from response
                    extracted = self._extract_json_from_text(response_text)
                    if extracted:
                        return extracted
                    raise ValueError(f"Generated invalid JSON: {e}")
                return response_text
                
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            if self.config.enforce_schema:
                raise
            return f"Error: Failed to generate structured output - {str(e)}"
    
    def _validate_json_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """Basic JSON schema validation."""
        try:
            import jsonschema
            jsonschema.validate(data, schema)
        except ImportError:
            logger.warning("jsonschema not installed, skipping validation")
        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            raise ValueError(f"Response doesn't match schema: {e}")
    
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Try to extract JSON from text response."""
        import json
        import re
        
        # Look for JSON blocks in the text
        json_patterns = [
            r'```json\s*(.*?)\s*```',  # JSON code blocks
            r'```\s*(.*?)\s*```',      # Generic code blocks
            r'\{.*\}',                 # Any JSON object
            r'\[.*\]'                  # Any JSON array
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match.strip())
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def supports_structured_output(self) -> bool:
        """HuggingFace backend supports structured output via prompt engineering."""
        return True
    
    def is_available(self) -> bool:
        """Check if the model is loaded and ready."""
        return self.model is not None and self.tokenizer is not None
    
    def get_model_info(self) -> dict:
        """Get detailed model information."""
        if not self.model:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "model_name": self.config.model_name,
            "device": str(self.device),
            "dtype": str(self.model.dtype),
            "memory_usage_gb": self._estimate_memory_usage(),
            "vocab_size": len(self.tokenizer) if self.tokenizer else 0,
            "max_position_embeddings": getattr(self.model.config, 'max_position_embeddings', 'unknown')
        }
    
    def clear_cache(self):
        """Clear GPU cache to free memory."""
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU cache cleared") 