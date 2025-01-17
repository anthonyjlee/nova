# NIA Documentation

## Core Documentation

1. **System Architecture and Implementation**
   - Two-layer memory architecture (Qdrant + Neo4j)
   - Storage patterns and implementation
   - WebSocket integration with LLM streaming
   - Error handling and recovery
   - Template-based LLM analysis

2. **Integration Patterns and User Flows**
   - Component interactions
   - Message flow patterns
   - Storage patterns
   - Error handling
   - LLM streaming patterns

3. **Schema Debug Guide**
   - Feature flags for debugging
   - Validation logging
   - WebSocket debugging
   - Debug UI panel
   - Initialization error tracking
   - Error status code handling (422)
   - Frontend/backend schema alignment
   - LLM template validation

4. **API Reference Guide**
   - Endpoint specifications
   - Request/response schemas
   - WebSocket message types
   - Schema validation rules
   - LLM streaming formats

## Additional Documentation

- Documentation Guide (navigation and usage)
- Documentation Alignment (consistency analysis)
- Development Logs (in devlog/)
- UI Component Implementation Status
- WebSocket Guide (message formats and patterns)

## Development Process

1. Debug First
- Use feature flags for debugging
- Add comprehensive logging
- Create debug UI panels
- Fix issues early
- Track initialization sequence
- Handle initialization errors properly
- Use appropriate status codes (422)
- Monitor LLM streaming

2. Keep It Simple
- Focus on basic functionality
- Add debugging tools
- Fix validation issues
- Then add features
- Match frontend/backend schemas
- Use Zod for frontend validation
- Use Pydantic for backend validation
- Separate WebSocket concerns

3. Document Changes
- Update devlogs
- Keep docs in sync
- Focus on clarity
- Remove complexity
- Document error handling
- Document initialization flow
- Keep validation rules clear
- Document WebSocket patterns

4. Testing Strategy
- Test backend initialization
- Verify error handling
- Check schema validation
- Test frontend integration
- Ensure type consistency
- Validate error responses
- Test LLM streaming
- Verify WebSocket stability

## Component Architecture

1. WebSocket Integration
- Base WebSocket client
- Graph-specific WebSocket
- LLM streaming support
- Error handling and recovery
- Connection management

2. Schema Validation
- Shared validation rules
- Frontend Zod schemas
- Backend Pydantic models
- WebSocket message formats
- LLM template schemas

3. UI Components
- Chat interface
- LLM streaming display
- Error handling
- Connection status
- Template selection

4. Testing Coverage
- Unit tests
- Integration tests
- E2E tests
- WebSocket tests
- LLM streaming tests
