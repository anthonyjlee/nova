# Nova API Reference Guide

## Authentication

All endpoints require API key authentication using the `X-API-Key` header.

## Endpoints

### System

#### Health Check
- `GET /api/status`
- Description: Health check endpoint
- Response: 200 OK

### Memory System

1. Store Memory
   - `POST /api/memory/api/memory/store`
   - Description: Store content in memory system
   - Parameters:
     * domain (query, optional): Domain context
   - Request Body: Memory content
   - Response: Storage result

2. Search Memory
   - `GET /api/memory/api/memory/search`
   - Description: Search memory with domain filtering
   - Parameters:
     * query (query): Search query
     * domain (query, optional): Domain filter
     * memory_type (query, optional): Type filter
     * limit (query, optional): Result limit (default: 10)
   - Response: Search results

3. Cross Domain Operation
   - `POST /api/memory/api/memory/cross-domain`
   - Description: Request cross-domain memory operation
   - Request Body: Operation details
   - Response: Operation result

4. Consolidate Memory
   - `GET /api/memory/api/memory/consolidate`
   - Description: Trigger memory consolidation
   - Parameters:
     * domain (query, optional): Domain filter
   - Response: Consolidation status

5. Prune Memory
   - `DELETE /api/memory/api/memory/prune`
   - Description: Prune knowledge graph
   - Parameters:
     * domain (query, optional): Domain filter
   - Response: Pruning result

### Chat & Threads

#### Channels
1. Channel Details
   - `GET /api/channels/api/channels/{channel_id}/details`
   - Description: Get detailed information about a channel
   - Parameters:
     * channel_id (path): Channel identifier
   - Response: ChannelDetails object containing:
     ```json
     {
       "id": "string",
       "name": "string",
       "description": "string",
       "created_at": "datetime",
       "updated_at": "datetime",
       "is_public": true,
       "workspace": "string",
       "domain": "string",
       "type": "channel",
       "metadata": {}
     }
     ```

2. Channel Members
   - `GET /api/channels/api/channels/{channel_id}/members`
   - Description: Get list of members in a channel
   - Parameters:
     * channel_id (path): Channel identifier
   - Response: Array of ChannelMember objects:
     ```json
     [{
       "id": "string",
       "name": "string",
       "type": "string",
       "role": "string",
       "status": "string",
       "joined_at": "datetime",
       "metadata": {}
     }]
     ```

3. Pinned Items
   - `GET /api/channels/api/channels/{channel_id}/pinned`
   - Description: Get pinned items in a channel
   - Parameters:
     * channel_id (path): Channel identifier
   - Response: Array of PinnedItem objects:
     ```json
     [{
       "id": "string",
       "type": "string",
       "content": {},
       "pinned_by": "string",
       "pinned_at": "datetime",
       "metadata": {}
     }]
     ```

4. Channel Settings
   - `POST /api/channels/api/channels/{channel_id}/settings`
   - Description: Update channel settings
   - Parameters:
     * channel_id (path): Channel identifier
   - Request Body: ChannelSettings object:
     ```json
     {
       "notifications": true,
       "privacy": "public",
       "retention_days": null,
       "metadata": {}
     }
     ```
   - Response: Updated ChannelSettings object

#### Threads
1. List Threads
   - `GET /api/threads/api/threads`
   - Description: List all threads
   - Parameters:
     * domain (query, optional): Domain filter
   - Response: Thread list

2. Get Thread Messages
   - `GET /api/threads/api/threads/{thread_id}`
   - Description: Get messages from a thread with pagination
   - Parameters:
     * thread_id (path): Thread identifier
     * start (query, optional): Starting index (default: 0)
     * limit (query, optional): Maximum messages (default: 100)
     * domain (query, optional): Domain filter
   - Response: Thread messages

3. Post Thread Message
   - `POST /api/threads/api/threads/{thread_id}/message`
   - Description: Post a message to a thread
   - Parameters:
     * thread_id (path): Thread identifier
     * domain (query, optional): Domain context
   - Request Body: Message content
   - Response: Message details

### Agent Management

1. Get Agents
   - `GET /api/agents/api/agents/`
   - Description: Get list of all agents
   - Response: Array of AgentResponse objects:
     ```json
     [{
       "id": "string",
       "name": "string",
       "type": "agent",
       "agentType": "string",
       "status": "active",
       "capabilities": ["string"],
       "workspace": "personal",
       "metadata": {},
       "timestamp": "string"
     }]
     ```

2. Get Agent Details
   - `GET /api/agents/api/agents/{agent_id}/details`
   - Description: Get detailed information about an agent
   - Parameters:
     * agent_id (path): Agent identifier
   - Response: AgentInfo object

3. Get Agent Metrics
   - `GET /api/agents/api/agents/{agent_id}/metrics`
   - Description: Get performance metrics for an agent
   - Parameters:
     * agent_id (path): Agent identifier
   - Response: AgentMetrics object

4. Get Agent Interactions
   - `GET /api/agents/api/agents/{agent_id}/interactions`
   - Description: Get recent interactions for an agent
   - Parameters:
     * agent_id (path): Agent identifier
   - Response: Array of AgentInteraction objects

### WebSocket Endpoints

Real-time communication is handled through WebSocket connections:

1. Debug Client
   - `ws://localhost:8000/debug/client_{client_id}`
   - Description: Debug endpoint for testing
   - Features:
     * Authentication required
     * Message confirmation
     * Error handling
     * Reconnection support

2. Production Client
   - `ws://localhost:8000/client_{client_id}`
   - Description: Production client endpoint
   - Features:
     * Authentication required
     * Message confirmation
     * Error handling
     * Reconnection support
     * Channel operations
     * Task updates
     * Agent status updates

### Common Parameters

Many endpoints support these optional parameters:
- max_retries (query): Maximum retry attempts (default: 5)
- retry_delay (query): Delay between retries in seconds (default: 1.0)
- name (query): System name (default: "TwoLayerMemorySystem")

### Task Orchestration

1. Create Task
   - `POST /api/tasks/api/tasks`
   - Description: Create a new task with validation
   - Request Body: TaskNode object:
     ```json
     {
       "id": "string",
       "label": "string",
       "type": "task",
       "status": "pending",
       "description": "string",
       "team_id": "string",
       "domain": "string",
       "priority": "high|medium|low",
       "assignee": "string",
       "tags": ["string"],
       "dependencies": ["string"],
       "blocked_by": ["string"],
       "sub_tasks": [{
         "id": "string",
         "description": "string",
         "completed": false
       }]
     }
     ```
   - Response: Created task

2. Transition Task State
   - `POST /api/tasks/api/tasks/{task_id}/transition`
   - Description: Transition a task to a new state
   - Parameters:
     * task_id (path): Task identifier
     * new_state (query): New task state (pending|in_progress|blocked|completed)
   - Response: Updated task state

3. Propose Task
   - `POST /api/tasks/api/tasks/propose`
   - Description: Propose a new task for approval
   - Parameters:
     * domain (query, optional): Domain context
   - Request Body: Task proposal
   - Response: Proposal result

4. Approve Task
   - `POST /api/tasks/api/tasks/{task_id}/approve`
   - Description: Approve a pending task
   - Parameters:
     * task_id (path): Task identifier
     * domain (query, optional): Domain context
   - Response: Approval result

### Knowledge Graph

1. Get Agent Graph
   - `GET /api/graph/api/graph/agents`
   - Description: Get agent graph data
   - Response: Graph visualization data

2. Get Knowledge Graph
   - `GET /api/graph/api/graph/knowledge`
   - Description: Get knowledge graph data
   - Response: Knowledge graph data

3. Get Task Graph
   - `GET /api/graph/api/graph/tasks`
   - Description: Get task graph data
   - Response: Task graph data

4. Cross Domain Access
   - `POST /api/knowledge/api/knowledge/crossDomain`
   - Description: Request access to cross-domain knowledge
   - Request Body: Access request details
   - Response: Access result

5. List Domains
   - `GET /api/knowledge/api/knowledge/domains`
   - Description: List available knowledge domains
   - Response: Domain list

6. Link Task To Concept
   - `POST /api/knowledge/api/knowledge/taskReference`
   - Description: Link a task to a concept in the knowledge graph
   - Request Body: Link details
   - Response: Link result

7. Get Knowledge Data
   - `GET /api/knowledge/api/knowledge/data`
   - Description: Get knowledge graph data
   - Response: Knowledge data

8. Get Task Related Concepts
   - `GET /api/knowledge/api/knowledge/taskConcepts/{task_id}`
   - Description: Get concepts related to a task
   - Parameters:
     * task_id (path): Task identifier
   - Response: Related concepts

### User Management

1. Submit Questionnaire
   - `POST /api/users/api/users/questionnaire`
   - Description: Submit psychometric questionnaire
   - Request Body: PsychometricQuestionnaire object:
     ```json
     {
       "big_five": {
         "openness": 0.8,
         "conscientiousness": 0.7,
         "extraversion": 0.6,
         "agreeableness": 0.9,
         "neuroticism": 0.3
       },
       "learning_style": {
         "visual": 0.8,
         "auditory": 0.6,
         "kinesthetic": 0.4
       },
       "communication": {
         "direct": 0.7,
         "detailed": 0.8,
         "formal": 0.6
       }
     }
     ```
   - Response: Submission result

2. Get Profile
   - `GET /api/users/api/users/profile/{profile_id}`
   - Description: Get user profile
   - Parameters:
     * profile_id (path): Profile identifier
   - Response: UserProfile object

3. Update Auto Approval
   - `POST /api/users/api/users/profile/{profile_id}/auto-approval`
   - Description: Update auto-approval settings
   - Parameters:
     * profile_id (path): Profile identifier
   - Request Body: AutoApprovalSettings object:
     ```json
     {
       "auto_approve_domains": ["string"],
       "approval_thresholds": {
         "domain": 0.8
       },
       "restricted_operations": ["string"]
     }
     ```
   - Response: Update result

4. Get Profile Adaptations
   - `GET /api/users/api/users/profile/{profile_id}/adaptations`
   - Description: Get profile-based adaptations
   - Parameters:
     * profile_id (path): Profile identifier
     * task_type (query, optional): Task type filter
   - Response: Adaptation settings

### Security

All endpoints are protected by API key authentication:
```json
{
  "type": "apiKey",
  "in": "header",
  "name": "X-API-Key"
}
```
