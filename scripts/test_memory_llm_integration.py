"""Test memory LLM integration."""

import asyncio
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.nova.core.llm import LMStudioLLM
from src.nia.nova.core.llm_types import LLMAnalysisResult

class MemoryTestClient:
    """Test client for memory integration."""
    
    def __init__(self, llm: LMStudioLLM):
        """Initialize test client."""
        self.llm = llm
        self.memories: Dict[str, Any] = {}
        
    async def store_memory(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store memory."""
        try:
            # Analyze content
            analysis = await self.llm.analyze(
                content={"text": content, "metadata": metadata},
                template="parsing_analysis"
            )
            
            # Store memory
            memory_id = f"mem_{len(self.memories)}"
            self.memories[memory_id] = {
                "content": content,
                "analysis": analysis,
                "metadata": metadata or {}
            }
            
            return {
                "id": memory_id,
                "status": "success",
                "message": "Memory stored successfully"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to store memory: {str(e)}"
            }

async def test_memory_llm():
    """Test memory LLM integration."""
    try:
        # Initialize LLM interface
        llm = LMStudioLLM(
            chat_model="llama-3.2-3b-instruct",  # Instruction-tuned model
            embedding_model="text-embedding-nomic-embed-text-v1.5@f16",  # Fast embedding model
            api_base="http://localhost:1234/v1"  # Default LM Studio API endpoint
        )
        
        # Initialize test client
        client = MemoryTestClient(llm)
        
        # Test content
        content = "The quick brown fox jumps over the lazy dog."
        metadata = {
            "domain": "test",
            "type": "sentence"
        }
        
        print("\nTesting memory LLM integration...")
        print(f"\nInput content: {content}")
        print(f"Metadata: {metadata}")
        
        # Store memory
        print("\nStoring memory...")
        result = await client.store_memory(content, metadata)
        print(f"\nStore Result: {json.dumps(result, indent=2)}")
        
        if result["status"] == "success":
            # Get stored memory
            memory_id = result["id"]
            memory = client.memories[memory_id]
            
            print("\nStored Memory:")
            print(f"Content: {memory['content']}")
            print(f"Analysis: {json.dumps(memory['analysis'], indent=2)}")
            print(f"Metadata: {json.dumps(memory['metadata'], indent=2)}")
            
            print("\nMemory LLM integration test completed successfully!")
        else:
            print("\nMemory LLM integration test failed!")
            
    except Exception as e:
        print(f"\nError testing memory LLM integration: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_memory_llm())
