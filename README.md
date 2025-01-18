# NIA (Nova Intelligence Architecture)

## Project Status (2025-01-21)
- 🟢 Memory System: Two-layer architecture implemented
- 🟢 LM Studio: Integration implemented in llm.py
- 🟢 Frontend: Core components implemented
- 🟢 Validation: Schema validation and error handling complete
- 🟢 Testing: Backend tests passing with initialization coverage
- 🟢 WebSocket: LLM streaming and template-based analysis implemented
- 🟡 Next: Configure LM Studio models and test end-to-end flow

## Service Architecture

### Storage Layer
- Neo4j (Graph Database)
  * Purpose: Semantic memory storage
  * Port: 7474 (HTTP), 7687 (Bolt)
  * Status: http://localhost:7474

- Qdrant (Vector Store)
  * Purpose: Ephemeral memory & embeddings
  * Port: 6333
  * Status: http://localhost:6333/dashboard

- Redis (Cache/Queue)
  * Purpose: Caching and message queues
  * Port: 6379
  * Used by: Celery, FastAPI

### Processing Layer
- LMStudio (LLM Server)
  * Purpose: Local LLM inference
  * Port: 1234
  * Status: http://localhost:1234/v1/models
  * Features:
    - Template-based analysis
    - Streaming responses
    - Error handling
    - WebSocket integration

- Celery (Task Queue)
  * Purpose: Asynchronous task processing
  * Workers: Memory consolidation, batch operations
  * Broker: Redis
  * Note: Must be started manually:
    ```bash
    # From project root
    celery -A nia.nova.core.celery_app worker --loglevel=info
    ```

### Application Layer
- FastAPI Server
  * Purpose: Main application server
  * Port: 8000
  * Status: http://localhost:8000/docs
  * Features:
    - TinyTroupe integration
    - Domain-aware processing
    - WebSocket support with LLM streaming
    - Task orchestration
    - Template-based analysis

- Frontend (SvelteKit)
  * Purpose: Web interface
  * Port: 5173
  * Status: http://localhost:5173
  * Note: Must be started manually:
    ```bash
    # From frontend directory
    npm run dev:managed
    ```
  * Features:
    - Slack-inspired three-panel layout
    - Real-time updates via WebSocket
    - LLM streaming support
    - Domain-aware components
    - Task management
    - Search with caching
    - Dark theme support
    - Template selection
    - Connection status indicators

### Service Management
Use manage.py to start core services (Neo4j, Redis, Qdrant, FastAPI):
```bash
python scripts/manage.py start
```

Note: Frontend and Celery worker must be started manually in separate terminals due to TTY requirements.

### WebSocket Integration
- Base WebSocket client
- Graph-specific WebSocket
- LLM streaming support
- Error handling and recovery
- Connection management
- Template validation
- Message schemas

## Recent Updates (2025-01-21)

### WebSocket Improvements
- Added LLM streaming support
- Implemented template-based analysis
- Added connection status indicators
- Enhanced error handling
- Separated graph WebSocket concerns

### Frontend Components
- Created LLMChat component
- Added template selection
- Implemented streaming display
- Added error handling
- Added connection status

### Schema Validation
- Added chat-schemas.ts
- Updated WebSocket schemas
- Added LLM message validation
- Enhanced error handling
- Added template validation

### Testing Coverage
- Added WebSocket LLM tests
- Added E2E tests for streaming
- Added template validation tests
- Added error handling tests
- Added connection tests

## Next Steps
1. Configure LM Studio models
2. Add more analysis templates
3. Improve error handling
4. Add unit tests for edge cases
5. Document WebSocket patterns

[Previous content remains the same]
