"""Service for interacting with LM Studio."""

import aiohttp
import json
from typing import Dict, Any, List, Optional
from ..config.llm_config import LLMConfig, ModelType

class LMStudioService:
    """Service for interacting with LM Studio API."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LM Studio service."""
        self.config = config
        
    async def validate_connection(self) -> bool:
        """Validate connection to LM Studio."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config.lmstudio.api_base}/models"
                async with session.get(url) as response:
                    if response.status != 200:
                        return False
                    data = await response.json()
                    models = [model["id"] for model in data.get("data", [])]
                    return (
                        self.config.lmstudio.chat_model in models and
                        self.config.lmstudio.embedding_model in models
                    )
        except aiohttp.ClientError:
            return False
            
    async def get_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get chat completion from LM Studio."""
        chat_config = self.config.get_model_config(ModelType.CHAT)
        
        async with aiohttp.ClientSession() as session:
            url = f"{chat_config['api_base']}/chat/completions"
            payload = {
                "model": chat_config["model"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise ValueError(f"LM Studio API error: {error_data}")
                    
                return await response.json()
                
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from LM Studio."""
        embedding_config = self.config.get_model_config(ModelType.EMBEDDING)
        
        async with aiohttp.ClientSession() as session:
            url = f"{embedding_config['api_base']}/embeddings"
            payload = {
                "model": embedding_config["model"],
                "input": texts
            }
            
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise ValueError(f"LM Studio API error: {error_data}")
                    
                data = await response.json()
                return [item["embedding"] for item in data["data"]]
                
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Stream chat completion from LM Studio."""
        chat_config = self.config.get_model_config(ModelType.CHAT)
        
        async with aiohttp.ClientSession() as session:
            url = f"{chat_config['api_base']}/chat/completions"
            payload = {
                "model": chat_config["model"],
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_data = await response.text()
                    raise ValueError(f"LM Studio API error: {error_data}")
                    
                response_text = ""
                async for line in response.content:
                    if line:
                        try:
                            line_text = line.decode('utf-8').strip()
                            if line_text.startswith('data: '):
                                line_text = line_text[6:]  # Remove 'data: ' prefix
                            if line_text == '[DONE]':
                                break
                            
                            chunk = json.loads(line_text)
                            if chunk.get('choices') and chunk['choices'][0].get('delta', {}).get('content'):
                                response_text += chunk['choices'][0]['delta']['content']
                        except json.JSONDecodeError:
                            continue
                            
                return response_text
