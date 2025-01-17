"""Configuration for LLM integration settings."""

from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass

class LLMProvider(Enum):
    """Supported LLM providers."""
    LMSTUDIO = "lmstudio"
    # Add other providers as needed

class ModelType(Enum):
    """Types of LLM models."""
    CHAT = "chat"
    EMBEDDING = "embedding"

@dataclass
class LMStudioConfig:
    """Configuration for LM Studio."""
    host: str = "localhost"
    port: int = 1234
    chat_model: str = "llama-3.2-3b-instruct"
    embedding_model: str = "text-embedding-nomic-embed-text-v1.5@q8_0"
    api_base: str = "http://localhost:1234/v1"
    timeout: int = 30  # seconds

@dataclass
class LLMConfig:
    """Main LLM configuration."""
    provider: LLMProvider = LLMProvider.LMSTUDIO
    lmstudio: LMStudioConfig = LMStudioConfig()

    def get_model_config(self, model_type: ModelType) -> Dict[str, Any]:
        """Get configuration for specific model type."""
        if self.provider == LLMProvider.LMSTUDIO:
            return {
                "api_base": self.lmstudio.api_base,
                "model": (
                    self.lmstudio.chat_model 
                    if model_type == ModelType.CHAT 
                    else self.lmstudio.embedding_model
                ),
                "timeout": self.lmstudio.timeout
            }
        raise ValueError(f"Unsupported provider: {self.provider}")

    def validate_models(self) -> bool:
        """Validate that required models are available."""
        import aiohttp
        import asyncio

        async def check_models():
            async with aiohttp.ClientSession() as session:
                url = f"{self.lmstudio.api_base}/models"
                try:
                    async with session.get(url) as response:
                        if response.status != 200:
                            return False
                        data = await response.json()
                        models = [model["id"] for model in data.get("data", [])]
                        return (
                            self.lmstudio.chat_model in models and
                            self.lmstudio.embedding_model in models
                        )
                except aiohttp.ClientError:
                    return False

        return asyncio.run(check_models())

# Default configuration
default_config = LLMConfig()

def get_llm_config(provider: Optional[LLMProvider] = None) -> LLMConfig:
    """Get LLM configuration."""
    if provider:
        return LLMConfig(provider=provider)
    return default_config

def validate_llm_config(config: LLMConfig) -> bool:
    """Validate LLM configuration."""
    if not config.validate_models():
        raise ValueError(
            f"Required models not found. Please ensure LM Studio is running "
            f"and the following models are loaded:\n"
            f"- Chat model: {config.lmstudio.chat_model}\n"
            f"- Embedding model: {config.lmstudio.embedding_model}"
        )
    return True
