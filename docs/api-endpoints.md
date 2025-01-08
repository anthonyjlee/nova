# NIA FastAPI Endpoints

## Overview

All endpoints require:
- API key authentication
- Rate limiting
- Domain access validation
- Permission checks

## Common Response Formats

### Success Response
```json
{
  "status": "success",
  "message": "string",
  "data": object
}
```

### Error Response
```json
{
  "detail": "string"
}
```

### HTTP Status Codes
- 200: Success
- 400: Bad Request (validation error)
- 404: Not Found
- 422: Unprocessable Entity (invalid data)
- 500: Internal Server Error

## API Endpoints

### Profile Management

#### User Profiles

##### Create Profile
- **POST** `/api/profiles/`
- Creates a new user profile
- Request Body:
  ```json
  {
    "profile_id": "string",
    "personality": {
      "openness": float,
      "conscientiousness": float,
      "extraversion": float,
      "agreeableness": float,
      "neuroticism": float
    },
    "learning_style": {
      "visual": float,
      "auditory": float,
      "kinesthetic": float
    },
    "communication": {
      "direct": float,
      "detailed": float,
      "formal": float
    },
    "auto_approval": {
      "auto_approve_domains": ["string"],
      "approval_thresholds": {
        "task_creation": float,
        "resource_access": float,
        "domain_crossing": float
      },
      "restricted_operations": ["string"]
    }
  }
  ```

##### Get Profile
- **GET** `/api/profiles/{profile_id}`
- Retrieves a user profile by ID

##### Update Profile
- **PUT** `/api/profiles/{profile_id}`
- Updates an existing profile
- Supports partial updates

##### Delete Profile
- **DELETE** `/api/profiles/{profile_id}`
- Deletes a user profile

##### List Profiles
- **GET** `/api/profiles/`
- Lists all user profiles
- Optional domain filter

### Agent System

#### Agent Management

##### Create Agent
- **POST** `/api/agents/create`
- Creates new agent with specified type and capabilities

##### Get Agent Capabilities
- **GET** `/api/agents/{agent_id}/capabilities`
- Lists agent capabilities

##### Get Agent Types
- **GET** `/api/agents/types`
- Lists available agent types

##### Search Agents
- **GET** `/api/agents/search`
- Search agents by capability and domain

##### Agent History
- **GET** `/api/agents/{agent_id}/history`
- Get agent interaction history

##### Agent Metrics
- **GET** `/api/agents/{agent_id}/metrics`
- Get agent performance metrics

##### Agent Status
- **GET** `/api/agents/{agent_id}/status`
- Get agent status
- **POST** `/api/agents/{agent_id}/activate`
- Activate agent
- **POST** `/api/agents/{agent_id}/deactivate`
- Deactivate agent

#### Analytics

##### Parse Query
- **POST** `/api/analytics/parse`
- Parse user query for concepts and structure

##### Flow Analytics
- **GET** `/api/analytics/flows`
- Get analytics for active flows

##### Resource Analytics
- **GET** `/api/analytics/resources`
- Get resource utilization analytics

##### WebSocket Analytics
- **WS** `/api/analytics/ws`
- Real-time analytics updates

### Memory System

#### Memory Operations

##### Store Memory
- **POST** `/api/orchestration/memory/store`
- Store memory in the system

##### Query Memory
- **POST** `/api/orchestration/memory/query`
- Query memories from the system

##### Consolidate Memory
- **POST** `/api/orchestration/memory/consolidate`
- Consolidate memories in the system

#### Graph Operations

##### Prune Graph
- **POST** `/api/graph/prune`
- Prune knowledge graph based on criteria

##### Graph Health
- **GET** `/api/graph/health`
- Check knowledge graph health

##### Optimize Graph
- **POST** `/api/graph/optimize`
- Optimize graph structure

##### Graph Statistics
- **GET** `/api/graph/statistics`
- Get knowledge graph statistics

##### Graph Backup
- **POST** `/api/graph/backup`
- Create graph backup

### User Management

#### Profile Operations

##### Submit Questionnaire
- **POST** `/api/users/profile/questionnaire`
- Submit user psychometric questionnaire

##### Get Profile
- **GET** `/api/users/profile`
- Get user profile data

##### Update Preferences
- **PUT** `/api/users/profile/preferences`
- Update user preferences

##### Get Learning Style
- **GET** `/api/users/profile/learning-style`
- Get user learning style

##### Auto-Approval Settings
- **PUT** `/api/users/profile/auto-approval`
- Update auto-approval settings

### Resource Management

#### Resource Operations

##### Allocate Resources
- **POST** `/api/orchestration/resources/allocate`
- Allocate resources based on analytics predictions

### Chat System

#### Thread Management

##### Create Thread
- **POST** `/api/chat/threads`
- Creates a new chat thread

##### Get Thread
- **GET** `/api/chat/threads/{thread_id}`
- Get thread details and messages

##### Add Message
- **POST** `/api/chat/threads/{thread_id}/messages`
- Add message to thread

##### Get Thread Agents
- **GET** `/api/chat/threads/{thread_id}/agents`
- Get agents participating in thread

##### Search Thread
- **POST** `/api/chat/threads/{thread_id}/search`
- Search thread messages

##### Thread WebSocket
- **WS** `/api/chat/threads/{thread_id}/ws`
- Real-time thread updates

### Graph Visualization

#### Node Operations

##### Get Nodes
- **GET** `/api/graph/viz/nodes`
- Get graph nodes for visualization
- Query Parameters:
  * domain (optional): Filter by domain
  * node_type (optional): Filter by node type
  * limit (default: 100, max: 1000)

##### Get Node Details
- **GET** `/api/graph/viz/nodes/{node_id}`
- Get detailed node information

##### Get Node Neighbors
- **GET** `/api/graph/viz/nodes/{node_id}/neighbors`
- Get node's neighboring nodes
- Query Parameters:
  * edge_type (optional): Filter by edge type
  * direction (in/out/both)
  * limit (default: 100, max: 1000)

#### Edge Operations

##### Get Edges
- **GET** `/api/graph/viz/edges`
- Get graph edges for visualization
- Query Parameters:
  * source_id (optional): Filter by source node
  * target_id (optional): Filter by target node
  * edge_type (optional): Filter by edge type
  * limit (default: 100, max: 1000)

#### Graph Operations

##### Search Graph
- **POST** `/api/graph/viz/search`
- Search nodes and edges in graph

##### Get Task Graph
- **GET** `/api/graph/viz/tasks`
- Get task dependency graph
- Query Parameters:
  * task_id (optional): Filter by task
  * status (optional): Filter by status
  * limit (default: 100, max: 1000)

##### Get Graph Layout
- **GET** `/api/graph/viz/layout`
- Get graph layout positions
- Query Parameters:
  * algorithm (force/circular/hierarchical/grid)

##### Get Visualization Stats
- **GET** `/api/graph/viz/stats`
- Get graph visualization statistics

##### Filter Graph
- **POST** `/api/graph/viz/filter`
- Filter graph by multiple criteria

### Task and Thread Management

#### Thread Tasks

##### Create Emergent Task
- **POST** `/api/chat/threads/{thread_id}/tasks`
- Create task from thread context
- Request Body:
  ```json
  {
    "description": "string",
    "output_type": "string",  // code, media, new_skill, document, api_call
    "domain": "string"
  }
  ```

##### Update Task Status
- **POST** `/api/chat/threads/{thread_id}/tasks/{task_id}/status`
- Update task status
- Request Body:
  ```json
  {
    "status": "string",  // pending, in_progress, completed, failed
    "output_data": "object"  // Optional task output
  }
  ```

##### Get Thread Tasks
- **GET** `/api/chat/threads/{thread_id}/tasks`
- Get tasks for thread
- Query Parameters:
  * status: Filter by status
  * output_type: Filter by output type

#### Thread Management

##### Update Thread Status
- **POST** `/api/chat/threads/{thread_id}/status`
- Update thread status
- Request Body:
  ```json
  {
    "status": "string"  // active/archived
  }
  ```

##### Get Thread Summary
- **GET** `/api/chat/threads/{thread_id}/summary`
- Get thread summary from aggregator

##### Update Log Visibility
- **POST** `/api/chat/threads/{thread_id}/logs`
- Update thread log visibility
- Request Body:
  ```json
  {
    "show_partial_logs": "boolean",
    "show_agent_thoughts": "boolean"
  }
  ```

##### Link Thread to Graph
- **POST** `/api/chat/threads/{thread_id}/link`
- Link thread to graph nodes
- Request Body:
  ```json
  {
    "node_ids": ["string"],
    "link_type": "string"
  }
  ```

### Task Visualization

#### Task Graph

##### Get Task Graph
- **GET** `/graph/tasks`
- Get task dependency graph

##### Get Task Outputs
- **GET** `/graph/tasks/{task_id}/outputs`
- Get task output visualization

##### Get Task Statistics
- **GET** `/graph/tasks/statistics`
- Get task statistics visualization

##### Get Task Layout
- **GET** `/graph/tasks/layout`
- Get task graph layout
- Query Parameters:
  * layout: Layout algorithm (hierarchical/force/etc)

##### Search Task Graph
- **GET** `/graph/search`
- Search task graph
- Query Parameters:
  * query: Search query
  * types: Optional list of node types

##### Filter Task Graph
- **GET** `/graph/filter`
- Filter task graph
- Query Parameters:
  * status: Filter by task status

### Task Output Management

#### Output Operations

##### Store Task Output
- **POST** `/api/tasks/{task_id}/outputs`
- Store task output with type-specific handling
- Request Body:
  ```json
  {
    "output_type": "string", // code/media/skill/document/api_result
    "content": object,
    "metadata": {
      "domain": "string",
      "importance": float,
      "tags": ["string"]
    }
  }
  ```

##### Get Task Output
- **GET** `/api/tasks/{task_id}/outputs/{output_id}`
- Get specific task output

##### List Task Outputs
- **GET** `/api/tasks/{task_id}/outputs`
- List all outputs for a task
- Query Parameters:
  * output_type (optional): Filter by type
  * domain (optional): Filter by domain

##### Update Output Status
- **PUT** `/api/tasks/{task_id}/outputs/{output_id}/status`
- Update output status (pending/complete/failed)

#### Real-time Updates

##### Graph WebSocket
- **WS** `/api/graph/viz/ws`
- Real-time graph updates including:
  * New nodes/edges
  * Layout changes
  * Task status updates
  * Output visualization updates

##### Memory WebSocket
- **WS** `/api/memory/ws`
- Real-time memory updates including:
  * New memories
  * Memory consolidation
  * Cross-domain operations
  * Cleanup events

### Memory Integration

#### Cross-Domain Operations

##### Request Domain Access
- **POST** `/api/memory/domains/access`
- Request access to cross-domain operations
- Request Body:
  ```json
  {
    "source_domain": "string",
    "target_domain": "string",
    "operation": "string",
    "justification": "string"
  }
  ```

##### Get Domain Access Status
- **GET** `/api/memory/domains/access/{request_id}`
- Check status of domain access request

#### Memory Cleanup

##### Archive Memories
- **POST** `/api/memory/archive`
- Archive old or unused memories
- Request Body:
  ```json
  {
    "domain": "string",
    "criteria": {
      "age_days": integer,
      "importance_threshold": float,
      "access_count_threshold": integer
    }
  }
  ```

##### Get Archive Status
- **GET** `/api/memory/archive/{archive_id}`
- Check status of archive operation

##### Restore from Archive
- **POST** `/api/memory/archive/{archive_id}/restore`
- Restore archived memories
