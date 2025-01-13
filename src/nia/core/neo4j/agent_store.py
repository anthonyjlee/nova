"""Neo4j store for agent operations."""

from typing import Dict, Any, List, Optional
import json
import logging
import asyncio
import configparser
from datetime import datetime
from pathlib import Path
from .base_store import Neo4jBaseStore

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def load_config():
    """Load Neo4j configuration from config.ini."""
    config = configparser.ConfigParser()
    config_path = Path(__file__).parent.parent.parent.parent / 'config.ini'
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return {
            "uri": "bolt://localhost:7687",
            "user": "neo4j",
            "password": "password"
        }
    
    config.read(config_path)
    return {
        "uri": config.get('NEO4J', 'uri', fallback='bolt://localhost:7687'),
        "user": config.get('NEO4J', 'user', fallback='neo4j'),
        "password": config.get('NEO4J', 'password', fallback='password')
    }

class AgentStore(Neo4jBaseStore):
    """Neo4j store for agent operations."""
    
    def __init__(self):
        """Initialize with config."""
        config = load_config()
        super().__init__(
            uri=config["uri"],
            user=config["user"],
            password=config["password"]
        )
    
    async def initialize(self):
        """Initialize agent store."""
        try:
            logger.info("Initializing agent store...")
            
            # Initialize with retries
            retry_count = 0
            max_retries = 5
            while retry_count < max_retries:
                try:
                    logger.debug(f"Attempting Neo4j connection (attempt {retry_count + 1}/{max_retries})")
                    await self.connect()
                    
                    # Verify connection with a test query
                    await self.run_query("MATCH (n:Agent) RETURN count(n) as count")
                    logger.info("Successfully connected to Neo4j")
                    break
                except Exception as e:
                    retry_count += 1
                    if retry_count == max_retries:
                        logger.error(f"Failed to initialize agent store after {max_retries} attempts: {str(e)}")
                        raise
                    logger.warning(f"Connection attempt {retry_count} failed: {str(e)}")
                    await asyncio.sleep(1)
            
            logger.info("Agent store initialized successfully")
        except Exception as e:
            logger.error(f"Error during agent store initialization: {str(e)}")
            raise RuntimeError("Agent store initialization failed") from e
        
    async def store_agent(self, agent_data: Dict[str, Any], thread_id: Optional[str] = None) -> str:
        """Store agent data in Neo4j and optionally add to thread."""
        try:
            # Log incoming agent data
            logger.info("Storing agent with data:")
            logger.info(f"Agent ID: {agent_data['id']}")
            logger.info(f"Raw agent data: {json.dumps(agent_data, indent=2)}")
            
            # Prepare parameters - avoid unnecessary JSON serialization
            metadata = {
                "type": agent_data.get("metadata_type", "agent"),
                "capabilities": agent_data.get("metadata_capabilities", []),
                "created_at": agent_data.get("metadata_created_at", datetime.now().isoformat()),
                "thread_id": thread_id  # Store thread association if provided
            }
            
            params = {
                "id": agent_data["id"],
                "name": agent_data["name"],
                "type": agent_data.get("type", "agent"),
                "workspace": agent_data.get("workspace", "personal"),
                "domain": agent_data.get("domain", "general"),
                "status": agent_data.get("status", "active"),
                "metadata": metadata  # Store directly without JSON serialization
            }

            # Determine labels
            labels = ["Agent"]
            if agent_data.get("type"):
                labels.append(agent_data["type"].capitalize())
            if agent_data.get("workspace"):
                labels.append(f"{agent_data['workspace'].capitalize()}Workspace")
            if agent_data.get("domain"):
                labels.append(f"{agent_data['domain'].capitalize()}Domain")
            
            # Store in both episodic and semantic layers
            async with self.driver.session() as session:
                async with session.begin_transaction() as tx:
                    # Store in semantic layer (Neo4j)
                    await tx.run(f"""
                        MERGE (a:{':'.join(labels)} {{id: $id}})
                        SET a.name = $name,
                            a.type = $type,
                            a.workspace = $workspace,
                            a.domain = $domain,
                            a.status = $status,
                            a.metadata = $metadata
                        RETURN a
                    """, params)

                    # If thread_id provided, create relationship to thread
                    if thread_id:
                        await tx.run("""
                        MATCH (a:Agent {id: $agent_id})
                        MATCH (t:Thread {id: $thread_id})
                        MERGE (a)-[r:PARTICIPATES_IN]->(t)
                        SET r.joined_at = datetime()
                        """, {
                            "agent_id": agent_data["id"],
                            "thread_id": thread_id
                        })

                    # Store in episodic layer if memory system available
                    try:
                        print("\n=== Storing in episodic layer ===")
                        from nia.memory.two_layer import TwoLayerMemorySystem
                        memory_system = TwoLayerMemorySystem()
                        print("Initializing memory system...")
                        await memory_system.initialize()
                        print("Memory system initialized")
                        
                        # Create memory object
                        print("\nCreating memory object...")
                        memory_id = f"agent_{agent_data['id']}"
                        print(f"Memory ID: {memory_id}")
                        
                        memory = {
                            "id": memory_id,
                            "content": json.dumps(agent_data),  # Serialize content to string
                            "type": "EPISODIC",
                            "importance": 0.8,
                            "context": {
                                "domain": agent_data.get("domain", "general"),
                                "source": "nova",
                                "type": "agent",
                                "thread_id": thread_id,
                                "workspace": agent_data.get("workspace", "personal")  # Add required workspace
                            },
                            "metadata": {
                                "type": "agent",
                                "thread_id": thread_id,
                                "consolidated": False,
                                "system": False,  # Add required system flag
                                "pinned": False,  # Add required pinned flag
                                "description": f"Agent {agent_data['name']}"  # Add required description
                            }
                        }
                        print(f"\nMemory object created:")
                        print(f"Content type: {type(memory['content'])}")
                        print(f"Content: {json.dumps(memory['content'], indent=2)}")
                        print(f"Context: {json.dumps(memory['context'], indent=2)}")
                        print(f"Metadata: {json.dumps(memory['metadata'], indent=2)}")
                        
                        print("\nStoring in episodic layer directly...")
                        await memory_system.episodic.store_memory(memory)
                        print("Memory stored successfully")
                    except Exception as e:
                        logger.warning(f"Failed to store agent in episodic layer: {str(e)}")
                        # Continue since Neo4j storage succeeded
                        
                    await tx.commit()
            
            return agent_data["id"]
        except Exception as e:
            logger.error(f"Failed to store agent: {str(e)}")
            raise

    async def update_agent(self, agent_id: str, properties: Dict[str, Any]) -> None:
        """Update agent properties."""
        try:
            # Handle metadata separately if provided
            if "metadata" in properties:
                if isinstance(properties["metadata"], dict):
                    properties["metadata"] = json.dumps(properties["metadata"])
            
            query = """
            MATCH (a:Agent {id: $id})
            SET a += $properties
            RETURN a
            """
            
            logger.info("Updating agent properties:")
            logger.info(f"Agent ID: {agent_id}")
            logger.info(f"Properties: {json.dumps(properties, indent=2)}")
            
            await self.run_query(query, {
                "id": agent_id,
                "properties": properties
            })
            
            logger.info(f"Updated agent {agent_id}")
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {str(e)}")
            raise

    async def search_agents(self, properties: Optional[Dict[str, Any]] = None, agent_type: Optional[str] = None, workspace: Optional[str] = None, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search agents by properties and labels."""
        try:
            # Build labels part of query
            labels = ["Agent"]
            if agent_type:
                labels.append(agent_type.capitalize())
            if workspace:
                labels.append(f"{workspace.capitalize()}Workspace")
            if domain:
                labels.append(f"{domain.capitalize()}Domain")
            labels_str = ':'.join(labels)
            
            # Build WHERE clause from properties
            where_clauses = []
            params = {}
            if properties:
                for key, value in properties.items():
                    where_clauses.append(f"a.{key} = ${key}")
                    params[key] = value
            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            query = f"""
            MATCH (a:{labels_str})
            {where_str}
            RETURN 
                a.id as id,
                a.name as name,
                a.type as type,
                a.workspace as workspace,
                a.domain as domain,
                a.status as status,
                a.metadata as metadata
            """
            
            logger.info("Searching agents:")
            logger.info(f"Labels: {labels_str}")
            logger.info(f"Properties: {json.dumps(properties or {}, indent=2)}")
            
            result = await self.run_query(query, params)
            
            # Format results
            agents = []
            for record in result:
                if not record.get("id"):
                    logger.warning(f"Skipping agent without id: {record}")
                    continue
                
                agent = {
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"] or "agent",
                    "workspace": record["workspace"] or "personal",
                    "domain": record["domain"] or "general",
                    "status": record["status"] or "active"
                }
                
                # Parse metadata
                metadata = record.get("metadata")
                if isinstance(metadata, str):
                    try:
                        agent["metadata"] = json.loads(metadata)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse metadata for agent {agent['id']}")
                        agent["metadata"] = {}
                else:
                    agent["metadata"] = metadata or {}
                
                agents.append(agent)
            
            logger.info(f"Found {len(agents)} matching agents")
            return agents
        except Exception as e:
            logger.error(f"Failed to search agents: {str(e)}")
            raise

    async def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents from Neo4j."""
        try:
            logger.info("Fetching all agents...")
            
            # Get all agents with their properties
            logger.debug("Fetching agent nodes...")
            agents_query = """
            MATCH (a:Agent)
            RETURN 
                a.id as id,
                a.name as name,
                a.type as type,
                a.workspace as workspace,
                a.domain as domain,
                a.status as status,
                a.metadata as metadata
            """
            agents_result = await self.run_query(agents_query)
            logger.debug(f"Found {len(agents_result)} agents")
            
            # Get agent relationships
            logger.debug("Fetching agent relationships...")
            relations_query = """
            MATCH (a:Agent)-[r]->(b:Agent)
            RETURN 
                a.id as source_id,
                b.id as target_id,
                type(r) as relation_type,
                properties(r) as properties
            """
            relations_result = await self.run_query(relations_query)
            logger.debug(f"Found {len(relations_result)} agent relationships")
            
            # Format agents
            agents = []
            for record in agents_result:
                if not record.get("id"):
                    logger.warning(f"Skipping agent without id: {record}")
                    continue
                    
                agent = {
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"] or "agent",
                    "workspace": record["workspace"] or "personal",
                    "domain": record["domain"] or "general",
                    "status": record["status"] or "active"
                }
                
                # Parse metadata
                metadata = record.get("metadata")
                if isinstance(metadata, str):
                    try:
                        agent["metadata"] = json.loads(metadata)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse metadata for agent {agent['id']}")
                        agent["metadata"] = {}
                else:
                    agent["metadata"] = metadata or {}
                
                # Add relationships
                agent["relationships"] = []
                for rel in relations_result:
                    if rel["source_id"] == agent["id"]:
                        agent["relationships"].append({
                            "target_id": rel["target_id"],
                            "type": rel["relation_type"],
                            "properties": rel["properties"] or {}
                        })
                
                agents.append(agent)
            
            logger.info(f"Successfully fetched {len(agents)} agents with relationships")
            return agents
            
        except Exception as e:
            logger.error(f"Failed to get agents: {str(e)}")
            raise

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific agent from Neo4j."""
        try:
            # Get agent with properties
            logger.debug(f"Fetching agent {agent_id}...")
            agent_query = """
            MATCH (a:Agent {id: $id})
            RETURN 
                a.id as id,
                a.name as name,
                a.type as type,
                a.workspace as workspace,
                a.domain as domain,
                a.status as status,
                a.metadata as metadata
            """
            agent_result = await self.run_query(agent_query, {"id": agent_id})
            
            if not agent_result:
                logger.warning(f"Agent {agent_id} not found")
                return None
                
            record = agent_result[0]
            if not record.get("id"):
                logger.warning(f"Invalid agent record: {record}")
                return None
                
            # Get agent relationships
            logger.debug("Fetching agent relationships...")
            relations_query = """
            MATCH (a:Agent {id: $id})-[r]->(b:Agent)
            RETURN 
                b.id as target_id,
                type(r) as relation_type,
                properties(r) as properties
            """
            relations_result = await self.run_query(relations_query, {"id": agent_id})
            
            # Format agent data
            agent = {
                "id": record["id"],
                "name": record["name"],
                "type": record["type"] or "agent",
                "workspace": record["workspace"] or "personal",
                "domain": record["domain"] or "general",
                "status": record["status"] or "active"
            }
            
            # Parse metadata
            metadata = record.get("metadata")
            if isinstance(metadata, str):
                try:
                    agent["metadata"] = json.loads(metadata)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse metadata for agent {agent_id}")
                    agent["metadata"] = {}
            else:
                agent["metadata"] = metadata or {}
            
            # Add relationships
            agent["relationships"] = []
            for rel in relations_result:
                agent["relationships"].append({
                    "target_id": rel["target_id"],
                    "type": rel["relation_type"],
                    "properties": rel["properties"] or {}
                })
            
            logger.info(f"Successfully fetched agent {agent_id} with {len(agent['relationships'])} relationships")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {str(e)}")
            raise

    VALID_RELATIONSHIP_TYPES = [
        "COORDINATES",
        "MANAGES",
        "ASSISTS",
        "COLLABORATES_WITH",
        "REPORTS_TO",
        "DELEGATES_TO",
        "DEPENDS_ON"
    ]

    async def create_agent_relationship(self, from_id: str, to_id: str, rel_type: str, properties: Optional[Dict[str, Any]] = None) -> None:
        """Create a relationship between agents."""
        try:
            # Validate relationship type
            rel_type_upper = rel_type.upper()
            if rel_type_upper not in self.VALID_RELATIONSHIP_TYPES:
                raise ValueError(f"Invalid relationship type. Must be one of: {', '.join(self.VALID_RELATIONSHIP_TYPES)}")

            # First verify both agents exist
            verify_query = """
            MATCH (a:Agent {id: $from_id})
            MATCH (b:Agent {id: $to_id})
            RETURN a, b
            """
            
            verify_result = await self.run_query(verify_query, {
                "from_id": from_id,
                "to_id": to_id
            })
            
            if not verify_result:
                raise ValueError(f"One or both agents not found: {from_id}, {to_id}")
            
            # Use transaction for atomic operation
            async with self.driver.session() as session:
                async with session.begin_transaction() as tx:
                    # First verify agents exist
                    verify_result = await tx.run("""
                        MATCH (a:Agent {id: $from_id})
                        MATCH (b:Agent {id: $to_id})
                        RETURN a, b
                    """, {"from_id": from_id, "to_id": to_id})
                    
                    if not await verify_result.fetch():
                        raise ValueError(f"One or both agents not found: {from_id}, {to_id}")
                    
                    # Create relationship
                    await tx.run("""
                        MATCH (a:Agent {id: $from_id}), (b:Agent {id: $to_id})
                        CREATE (a)-[r:$rel_type]->(b)
                        SET r = $properties
                        RETURN r
                    """, {
                        "from_id": from_id,
                        "to_id": to_id,
                        "rel_type": rel_type_upper,
                        "properties": properties or {}
                    })
                    
                    await tx.commit()
            
            logger.info("Creating agent relationship:")
            logger.info(f"From: {from_id} -> To: {to_id}")
            logger.info(f"Type: {rel_type_upper}")
            logger.info(f"Properties: {json.dumps(properties or {}, indent=2)}")
            
            logger.info(f"Created relationship from {from_id} to {to_id}")
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to create relationship: {str(e)}")
            raise

    async def delete_agent_relationship(self, from_id: str, to_id: str, rel_type: Optional[str] = None) -> None:
        """Delete relationship(s) between agents."""
        try:
            # First verify both agents exist
            verify_query = """
            MATCH (a:Agent {id: $from_id})
            MATCH (b:Agent {id: $to_id})
            RETURN a, b
            """
            
            verify_result = await self.run_query(verify_query, {
                "from_id": from_id,
                "to_id": to_id
            })
            
            if not verify_result:
                raise ValueError(f"One or both agents not found: {from_id}, {to_id}")
            
            # Delete relationship(s)
            if rel_type:
                rel_type_upper = rel_type.upper()
                if rel_type_upper not in self.VALID_RELATIONSHIP_TYPES:
                    raise ValueError(f"Invalid relationship type. Must be one of: {', '.join(self.VALID_RELATIONSHIP_TYPES)}")
                    
                query = """
                MATCH (a:Agent {id: $from_id})-[r:$rel_type]->(b:Agent {id: $to_id})
                DELETE r
                RETURN count(r) as deleted
                """
                params = {"from_id": from_id, "to_id": to_id, "rel_type": rel_type_upper}
            else:
                query = """
                MATCH (a:Agent {id: $from_id})-[r]->(b:Agent {id: $to_id})
                DELETE r
                RETURN count(r) as deleted
                """
                params = {"from_id": from_id, "to_id": to_id}
            
            logger.info("Deleting agent relationship(s):")
            logger.info(f"From: {from_id} -> To: {to_id}")
            if rel_type:
                logger.info(f"Type: {rel_type_upper}")
            
            result = await self.run_query(query, params)
            deleted_count = result[0]["deleted"] if result else 0
            logger.info(f"Deleted {deleted_count} relationship(s) from {from_id} to {to_id}")
            
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete relationship: {str(e)}")
            raise

    async def update_agent_status(self, agent_id: str, status: str) -> None:
        """Update an agent's status in Neo4j."""
        try:
            query = """
            MATCH (a:Agent {id: $id})
            SET a.status = $status
            """
            
            logger.info("Executing Neo4j query:")
            logger.info(query)
            
            await self.run_query(query, {"id": agent_id, "status": status})
            
            logger.info(f"Updated status for agent {agent_id} to {status}")
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id} status: {str(e)}")
            raise

    async def delete_agent(self, agent_id: str, thread_id: Optional[str] = None) -> None:
        """Delete an agent and optionally remove from thread."""
        try:
            async with self.driver.session() as session:
                async with session.begin_transaction() as tx:
                    if thread_id:
                        # Remove from specific thread only
                        await tx.run("""
                        MATCH (a:Agent {id: $agent_id})-[r:PARTICIPATES_IN]->(t:Thread {id: $thread_id})
                        DELETE r
                        """, {
                            "agent_id": agent_id,
                            "thread_id": thread_id
                        })
                        logger.info(f"Removed agent {agent_id} from thread {thread_id}")
                    else:
                        # Delete agent completely
                        await tx.run("""
                        MATCH (a:Agent {id: $agent_id})
                        DETACH DELETE a
                        """, {
                            "agent_id": agent_id
                        })
                        logger.info(f"Deleted agent {agent_id} and all relationships")
                        
                        # Also remove from episodic layer
                        try:
                            from nia.memory.two_layer import TwoLayerMemorySystem
                            memory_system = TwoLayerMemorySystem()
                            await memory_system.initialize()
                            
                            # Delete agent memory
                            await memory_system.episodic.store.delete_vectors([f"agent_{agent_id}"])
                        except Exception as e:
                            logger.warning(f"Failed to delete agent from episodic layer: {str(e)}")
                    
                    await tx.commit()
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {str(e)}")
            raise

    async def get_thread_agents(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all agents participating in a thread."""
        try:
            query = """
            MATCH (a:Agent)-[r:PARTICIPATES_IN]->(t:Thread {id: $thread_id})
            RETURN 
                a.id as id,
                a.name as name,
                a.type as type,
                a.workspace as workspace,
                a.domain as domain,
                a.status as status,
                a.metadata as metadata,
                r.joined_at as joined_at
            """
            
            result = await self.run_query(query, {"thread_id": thread_id})
            
            agents = []
            for record in result:
                if not record.get("id"):
                    continue
                    
                agent = {
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"] or "agent",
                    "workspace": record["workspace"] or "personal",
                    "domain": record["domain"] or "general",
                    "status": record["status"] or "active",
                    "joined_at": record["joined_at"]
                }
                
                # Parse metadata
                metadata = record.get("metadata")
                if isinstance(metadata, str):
                    try:
                        agent["metadata"] = json.loads(metadata)
                    except json.JSONDecodeError:
                        agent["metadata"] = {}
                else:
                    agent["metadata"] = metadata or {}
                
                agents.append(agent)
            
            return agents
        except Exception as e:
            logger.error(f"Failed to get agents for thread {thread_id}: {str(e)}")
            raise

    async def add_agent_to_thread(self, agent_id: str, thread_id: str) -> None:
        """Add an agent to a thread."""
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})
            MATCH (t:Thread {id: $thread_id})
            MERGE (a)-[r:PARTICIPATES_IN]->(t)
            SET r.joined_at = datetime()
            """
            
            await self.run_query(query, {
                "agent_id": agent_id,
                "thread_id": thread_id
            })
            
            logger.info(f"Added agent {agent_id} to thread {thread_id}")
        except Exception as e:
            logger.error(f"Failed to add agent {agent_id} to thread {thread_id}: {str(e)}")
            raise

    async def remove_agent_from_thread(self, agent_id: str, thread_id: str) -> None:
        """Remove an agent from a thread."""
        try:
            query = """
            MATCH (a:Agent {id: $agent_id})-[r:PARTICIPATES_IN]->(t:Thread {id: $thread_id})
            DELETE r
            """
            
            await self.run_query(query, {
                "agent_id": agent_id,
                "thread_id": thread_id
            })
            
            logger.info(f"Removed agent {agent_id} from thread {thread_id}")
        except Exception as e:
            logger.error(f"Failed to remove agent {agent_id} from thread {thread_id}: {str(e)}")
            raise
