"""Test LM Studio integration."""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.nova.core.llm import LMStudioLLM
from src.nia.nova.core.models import LLMAnalysisResult

async def test_llm():
    """Test LM Studio integration."""
    try:
        # Initialize LLM interface
        llm = LMStudioLLM(
            chat_model="llama-3.2-3b-instruct",  # Instruction-tuned model
            embedding_model="text-embedding-nomic-embed-text-v1.5@f16",  # Fast embedding model
            api_base="http://localhost:1234/v1"  # Default LM Studio API endpoint
        )
        
        # Test content
        content = {
            "text": "The quick brown fox jumps over the lazy dog.",
            "metadata": {
                "domain": "test",
                "type": "sentence"
            }
        }
        
        print("\nTesting LM Studio integration...")
        print(f"\nInput content: {content}")
        
        # Test parsing analysis
        print("\nTesting parsing analysis...")
        parsing_result = await llm.analyze(
            content=content,
            template="parsing_analysis"
        )
        print("\nParsing Result:")
        print(f"Response: {parsing_result.get('response')}")
        print(f"Concepts: {parsing_result.get('concepts')}")
        print(f"Key Points: {parsing_result.get('key_points')}")
        
        # Test analytics processing
        print("\nTesting analytics processing...")
        analytics_result = await llm.analyze(
            content=content,
            template="analytics_processing"
        )
        print("\nAnalytics Result:")
        print(f"Response: {analytics_result.get('response')}")
        print(f"Confidence: {analytics_result.get('confidence')}")
        
        print("\nLM Studio integration test completed successfully!")
        
    except Exception as e:
        print(f"\nError testing LM Studio integration: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_llm())
