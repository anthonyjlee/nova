# NIA Documentation

## Core Documentation

1. **System Architecture and Implementation**
   - Two-layer memory architecture (Qdrant + Neo4j)
   - Storage patterns and implementation
   - WebSocket integration
   - Error handling

2. **Integration Patterns and User Flows**
   - Component interactions
   - Message flow patterns
   - Storage patterns
   - Error handling

3. **Schema Debug Guide**
   - Feature flags for debugging
   - Validation logging
   - WebSocket debugging
   - Debug UI panel
   - Initialization error tracking
   - Error status code handling (422)
   - Frontend/backend schema alignment

4. **API Reference Guide**
   - Endpoint specifications
   - Request/response schemas
   - WebSocket message types
   - Schema validation rules

## Additional Documentation

- Documentation Guide (navigation and usage)
- Documentation Alignment (consistency analysis)
- Development Logs (in devlog/)
- UI Component Implementation Status

## Development Process

1. Debug First
- Use feature flags for debugging
- Add comprehensive logging
- Create debug UI panels
- Fix issues early
- Track initialization sequence
- Handle initialization errors properly
- Use appropriate status codes (422)

2. Keep It Simple
- Focus on basic functionality
- Add debugging tools
- Fix validation issues
- Then add features
- Match frontend/backend schemas
- Use Zod for frontend validation
- Use Pydantic for backend validation

3. Document Changes
- Update devlogs
- Keep docs in sync
- Focus on clarity
- Remove complexity
- Document error handling
- Document initialization flow
- Keep validation rules clear

4. Testing Strategy
- Test backend initialization
- Verify error handling
- Check schema validation
- Test frontend integration
- Ensure type consistency
- Validate error responses
