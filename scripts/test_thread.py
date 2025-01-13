#!/usr/bin/env python3
"""Script to test thread creation."""

import asyncio
import logging
import json
import traceback
from datetime import datetime
from pathlib import Path
from nia.memory.vector_store import VectorStore
from nia.memory.embedding import EmbeddingService

# Configure JSON logging
LOGS_DIR = Path("test_results/thread_test_logs")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

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
            "process_id": record.process
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
                "logs": self.logs
            }, f, indent=2)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add JSON handler
json_handler = JsonLogHandler(session_log)
logger.addHandler(json_handler)

async def main():
    """Create and verify a test thread."""
    try:
        # Initialize services
        embedding_service = EmbeddingService()
        vector_store = VectorStore(embedding_service)
        
        # Connect to vector store
        logger.info("Connecting to vector store...")
        await vector_store.connect()
        
        # Create test thread
        now = datetime.now().isoformat()
        thread = {
            "id": "nova-team",
            "name": "Nova Team",
            "domain": "general",
            "messages": [],
            "createdAt": now,
            "updatedAt": now,
            "workspace": "personal",
            "participants": [],
            "metadata": {
                "type": "agent-team",
                "system": True,
                "pinned": True,
                "description": "This is where NOVA and core agents collaborate."
            }
        }
        
        # Store thread
        logger.info("Storing test thread...")
        # Prepare payload with metadata prefixes
        payload = {
            "content": thread,  # Store full thread data
            "metadata_thread_id": thread["id"],
            "metadata_type": "thread",
            "metadata_consolidated": False,
            "metadata_system": thread["metadata"]["system"],
            "metadata_pinned": thread["metadata"]["pinned"],
            "metadata_domain": thread["domain"],
            "metadata_source": "nova"
        }
        await vector_store.store_vector(
            collection_name="memories",
            payload=payload
        )
        
        # Verify storage
        logger.info("Verifying storage...")
        points = await vector_store.inspect_collection()
        
        # Look for specific thread
        logger.info("\nSearching for nova-team thread...")
        for point in points:
            if point.payload.get("metadata_thread_id") == "nova-team":
                logger.info("Found nova-team thread:")
                logger.info(f"Point ID: {point.id}")
                logger.info("Metadata:")
                for k, v in point.payload.items():
                    if k.startswith("metadata_"):
                        logger.info(f"  {k}: {v}")
                logger.info("Content:")
                logger.info(point.payload.get("content"))
                break
        else:
            logger.info("nova-team thread not found")
    except Exception as e:
        logger.error(f"Error testing thread creation: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
