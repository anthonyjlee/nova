"""Test memory system with LLM integration."""

import asyncio
import sys
import logging
import json
import traceback
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Configure JSON logging
LOGS_DIR = Path("test_results/memory_llm_logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Create session-specific log file
session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
session_log = LOGS_DIR / f"session_{session_id}.json"

class JsonLogHandler(logging.Handler):
    def __init__(self, log_file):
        super().__init__()
        self.log_file = log_file
        self.logs = []
        
    def emit(self, record):
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "thread_id": record.thread,
            "process_id": record.process,
            "test_phase": getattr(record, 'test_phase', None),
            "test_result": getattr(record, 'test_result', None)
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
            
        self.logs.append(log_entry)
        self._save_logs()
        
    def _save_logs(self):
        with open(self.log_file, 'w') as f:
            json.dump({
                "session_id": session_id,
                "logs": self.logs,
                "summary": {
                    "total_tests": len([l for l in self.logs if l.get("test_result") is not None]),
                    "passed": len([l for l in self.logs if l.get("test_result") == True]),
                    "failed": len([l for l in self.logs if l.get("test_result") == False])
                }
            }, f, indent=2)

# Configure root logger to only show warnings and errors
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Disable noisy loggers
logging.getLogger('neo4j').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)

# Configure test logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add JSON handler
json_handler = JsonLogHandler(session_log)
logger.addHandler(json_handler)

from src.nia.memory.embedding import EmbeddingService
from src.nia.memory.vector_store import VectorStore
from src.nia.memory.graph_store import GraphStore
from src.nia.nova.core.llm import LMStudioLLM
from src.nia.nova.core.models import LLMAnalysisResult

async def test_integration():
    """Test full memory and LLM integration flow."""
    try:
        logger.info("Starting memory-LLM integration test", extra={"test_phase": "init"})
        
        # Initialize embedding service
        embedding_service = EmbeddingService()
        logger.info("Embedding service initialized", extra={"test_phase": "init", "test_result": True})
        
        # Initialize vector store
        vector_store = VectorStore(embedding_service)
        await vector_store.connect()
        logger.info("Vector store connected", extra={"test_phase": "init", "test_result": True})
        
        # Initialize graph store
        graph_store = GraphStore()
        await graph_store.connect()
        logger.info("Graph store connected", extra={"test_phase": "init", "test_result": True})
        
        # Initialize LLM interface
        llm = LMStudioLLM(
            chat_model="llama-3.2-3b-instruct",
            embedding_model="text-embedding-nomic-embed-text-v1.5@q8_0",
            api_base="http://localhost:1234/v1"
        )
        logger.info("LLM interface initialized", extra={"test_phase": "init", "test_result": True})
        
        # Test contents with variations
        contents = [
            {
                "text": "The quick brown fox jumps over the lazy dog.",
                "metadata": {
                    "domain": "test",
                    "type": "sentence",
                    "description": "Original pangram",
                    "system": False,
                    "pinned": False,
                    "consolidated": False,
                    "layer": "episodic"
                }
            },
            {
                "text": "Pack my box with five dozen liquor jugs.",
                "metadata": {
                    "domain": "test",
                    "type": "sentence",
                    "description": "Alternative pangram",
                    "system": False,
                    "pinned": False,
                    "consolidated": False,
                    "layer": "episodic"
                }
            },
            {
                "text": "The five boxing wizards jump quickly.",
                "metadata": {
                    "domain": "test",
                    "type": "sentence",
                    "description": "Another pangram variation",
                    "system": False,
                    "pinned": False,
                    "consolidated": False,
                    "layer": "episodic"
                }
            }
        ]
        
        # Store all test contents
        for content in contents:
            logger.info(f"Storing content: {json.dumps(content, indent=2)}", 
                       extra={"test_phase": "setup"})
            
            # Create and store embedding in Qdrant
            logger.info("Creating and storing embedding...", extra={"test_phase": "store_vector"})
            await vector_store.store_vector(
                content=content["text"],
                metadata=content["metadata"],
                layer=content["metadata"]["layer"]
            )
            logger.info("Embedding stored successfully", 
                       extra={"test_phase": "store_vector", "test_result": True})
        
        logger.info("All test content stored successfully", 
                   extra={"test_phase": "setup", "test_result": True})
        
        # 2. Use LLM for analysis
        logger.info("Analyzing with LLM...", extra={"test_phase": "llm_analysis"})
        parsing_result = await llm.analyze(
            content=content,
            template="parsing_analysis"
        )
        logger.info(f"Parsing result: {json.dumps(parsing_result, indent=2)}", 
                   extra={"test_phase": "llm_analysis", "test_result": True})
        
        # 3. Store concepts and relationships in Neo4j
        logger.info("Storing concepts in Neo4j...", extra={"test_phase": "store_concepts"})
        for concept in parsing_result.get("concepts", []):
            # Create concept node
            concept_query = """
            MERGE (c:Concept {name: $name})
            SET c.type = $type,
                c.description = $description,
                c.domain = $domain,
                c.created_at = datetime()
            RETURN c
            """
            await graph_store.run_query(
                concept_query,
                parameters={
                    "name": concept["name"],
                    "type": concept["type"],
                    "description": concept["description"],
                    "domain": content["metadata"]["domain"]
                }
            )
            
            # Create related concepts first
            if concept.get("related"):
                for related in concept["related"]:
                    # Create related concept
                    related_query = """
                    MERGE (c:Concept {name: $name})
                    SET c.type = 'Related',
                        c.domain = $domain,
                        c.created_at = datetime()
                    RETURN c
                    """
                    await graph_store.run_query(
                        related_query,
                        parameters={
                            "name": related,
                            "domain": content["metadata"]["domain"]
                        }
                    )
                    
                    # Create relationship
                    rel_query = """
                    MATCH (c1:Concept {name: $concept_name})
                    MATCH (c2:Concept {name: $related_name})
                    MERGE (c1)-[r:RELATES_TO]->(c2)
                    SET r.created_at = datetime()
                    """
                    await graph_store.run_query(
                        rel_query,
                        parameters={
                            "concept_name": concept["name"],
                            "related_name": related
                        }
                    )
        logger.info("Concepts and relationships stored", 
                   extra={"test_phase": "store_concepts", "test_result": True})
        
        # 4. Inspect collection contents
        logger.info("Inspecting collection...", extra={"test_phase": "inspect_collection"})
        stored_points = await vector_store.inspect_collection()
        logger.info(f"Found {len(stored_points)} stored points", 
                   extra={"test_phase": "inspect_collection", "test_result": True})
        
        # Test similarity search with a different query
        search_query = {
            "text": "A wizard quickly jumped over some boxes.",  # Similar but not exact
            "metadata": {
                "layer": "episodic"  # Only filter by layer
            }
        }
        
        # Search for similar content
        logger.info("Searching for similar content...", extra={"test_phase": "search_vectors"})
        vector_results = await vector_store.search_vectors(
            content=search_query,
            limit=5,
            score_threshold=0.5,  # Lower threshold to find similar vectors
            layer="episodic"
        )
        logger.info(f"Found {len(vector_results)} similar vectors", 
                   extra={"test_phase": "search_vectors"})
        if vector_results:
            for result in vector_results:
                logger.info(f"Similar vector found:", extra={"test_phase": "search_vectors"})
                logger.info(f"Content: {result.get('content')}", 
                          extra={"test_phase": "search_vectors"})
                logger.info(f"Layer: {result.get('layer')}", 
                          extra={"test_phase": "search_vectors"})
                logger.info(f"Metadata: {json.dumps(result.get('metadata'), indent=2)}", 
                          extra={"test_phase": "search_vectors"})
        logger.info("Vector search completed", 
                   extra={"test_phase": "search_vectors", "test_result": True})
        
        # 6. Get related concepts
        logger.info("Getting related concepts...", extra={"test_phase": "get_concepts"})
        concept_query = """
        MATCH (c:Concept)-[r:RELATES_TO]-(related)
        WHERE c.domain = $domain
        RETURN c.name as concept, collect(related.name) as related
        """
        concept_results = await graph_store.run_query(
            concept_query,
            parameters={"domain": content["metadata"]["domain"]}
        )
        logger.info(f"Found {len(concept_results) if concept_results else 0} concept relationships", 
                   extra={"test_phase": "get_concepts", "test_result": True})
        
        logger.info("Integration test completed successfully!", 
                   extra={"test_phase": "complete", "test_result": True})
        
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}", 
                    extra={"test_phase": "error", "test_result": False})
        raise

if __name__ == "__main__":
    asyncio.run(test_integration())
