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
