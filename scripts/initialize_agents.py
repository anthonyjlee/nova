"""Initialize default agents in the store."""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.nia.memory.agent_store import AgentStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_agents():
    """Initialize default agents in the store."""
    try:
        agent_store = AgentStore()
        
        # Default agents
        default_agents = [
            # Nova Team
            {
                "id": "nova-team",
                "name": "NovaTeam",
                "type": "nova",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "type": "agent-team",
                    "system": True,
                    "pinned": True,
                    "description": "This is where NOVA and core agents collaborate.",
                    "visualization": {
                        "position": "center",
                        "category": "orchestrator"
                    }
                }
            },
            # Core Processing Agents
            {
                "id": "parsing-agent-1",
                "name": "ParsingAgent",
                "type": "parsing",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["text_parsing", "concept_extraction"],
                    "visualization": {
                        "position": "outer",
                        "category": "processing"
                    }
                }
            },
            {
                "id": "analysis-agent-1",
                "name": "AnalysisAgent",
                "type": "analysis",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["pattern_detection", "insight_generation"],
                    "visualization": {
                        "position": "outer",
                        "category": "processing"
                    }
                }
            },
            {
                "id": "validation-agent-1",
                "name": "ValidationAgent",
                "type": "validation",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["rule_validation", "constraint_checking"],
                    "visualization": {
                        "position": "outer",
                        "category": "processing"
                    }
                }
            },
            {
                "id": "schema-agent-1",
                "name": "SchemaAgent",
                "type": "schema",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["data_structure_validation", "schema_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "processing"
                    }
                }
            },
            {
                "id": "synthesis-agent-1",
                "name": "SynthesisAgent",
                "type": "synthesis",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["theme_identification", "content_synthesis"],
                    "visualization": {
                        "position": "outer",
                        "category": "processing"
                    }
                }
            },
            {
                "id": "thread-management-agent-1",
                "name": "ThreadManagementAgent",
                "type": "thread_management",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["thread_orchestration", "subthread_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "management"
                    }
                }
            },
            {
                "id": "task-management-agent-1",
                "name": "TaskManagementAgent",
                "type": "task_management",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["task_lifecycle", "dependency_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "management"
                    }
                }
            },
            {
                "id": "aggregator-agent-1",
                "name": "AggregatorAgent",
                "type": "aggregator",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["output_summarization", "result_aggregation"],
                    "visualization": {
                        "position": "outer",
                        "category": "processing"
                    }
                }
            },
            {
                "id": "swarm-registry-agent-1",
                "name": "SwarmRegistryAgent",
                "type": "swarm_registry",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["pattern_management", "registry_maintenance"],
                    "visualization": {
                        "position": "outer",
                        "category": "system"
                    }
                }
            },
            {
                "id": "swarm-metrics-agent-1",
                "name": "SwarmMetricsAgent",
                "type": "swarm_metrics",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["performance_tracking", "metrics_collection"],
                    "visualization": {
                        "position": "outer",
                        "category": "system"
                    }
                }
            },
            # Cognitive Agents
            {
                "id": "belief-agent-1",
                "name": "BeliefAgent",
                "type": "belief",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["belief_analysis", "context_understanding"],
                    "visualization": {
                        "position": "inner",
                        "category": "cognitive"
                    }
                }
            },
            {
                "id": "desire-agent-1",
                "name": "DesireAgent",
                "type": "desire",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["goal_tracking", "intention_analysis"],
                    "visualization": {
                        "position": "inner",
                        "category": "cognitive"
                    }
                }
            },
            {
                "id": "emotion-agent-1",
                "name": "EmotionAgent",
                "type": "emotion",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["sentiment_analysis", "emotion_detection"],
                    "visualization": {
                        "position": "inner",
                        "category": "cognitive"
                    }
                }
            },
            {
                "id": "reflection-agent-1",
                "name": "ReflectionAgent",
                "type": "reflection",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["pattern_recognition", "insight_generation"],
                    "visualization": {
                        "position": "inner",
                        "category": "cognitive"
                    }
                }
            },
            {
                "id": "meta-agent-1",
                "name": "MetaAgent",
                "type": "meta",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["meta_orchestration", "high_level_coordination"],
                    "visualization": {
                        "position": "inner",
                        "category": "cognitive"
                    }
                }
            },
            # Task Management Agents
            {
                "id": "task-agent-1",
                "name": "TaskAgent",
                "type": "task",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["dependency_tracking", "state_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "management"
                    }
                }
            },
            {
                "id": "execution-agent-1",
                "name": "ExecutionAgent",
                "type": "execution",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["sequence_optimization", "execution_monitoring"],
                    "visualization": {
                        "position": "outer",
                        "category": "management"
                    }
                }
            },
            {
                "id": "orchestration-agent-1",
                "name": "OrchestrationAgent",
                "type": "orchestration",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["flow_coordination", "resource_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "management"
                    }
                }
            },
            {
                "id": "coordination-agent-1",
                "name": "CoordinationAgent",
                "type": "coordination",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["resource_allocation", "group_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "management"
                    }
                }
            },
            # Communication Agents
            {
                "id": "dialogue-agent-1",
                "name": "DialogueAgent",
                "type": "dialogue",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["conversation_management", "dialogue_flow"],
                    "visualization": {
                        "position": "outer",
                        "category": "communication"
                    }
                }
            },
            {
                "id": "response-agent-1",
                "name": "ResponseAgent",
                "type": "response",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["response_quality", "validation"],
                    "visualization": {
                        "position": "outer",
                        "category": "communication"
                    }
                }
            },
            {
                "id": "integration-agent-1",
                "name": "IntegrationAgent",
                "type": "integration",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["relationship_identification", "integration_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "communication"
                    }
                }
            },
            # Research & Context Agents
            {
                "id": "research-agent-1",
                "name": "ResearchAgent",
                "type": "research",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["information_gathering", "verification"],
                    "visualization": {
                        "position": "outer",
                        "category": "research"
                    }
                }
            },
            {
                "id": "context-agent-1",
                "name": "ContextAgent",
                "type": "context",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["environment_tracking", "state_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "research"
                    }
                }
            },
            {
                "id": "structure-agent-1",
                "name": "StructureAgent",
                "type": "structure",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["pattern_analysis", "schema_validation"],
                    "visualization": {
                        "position": "outer",
                        "category": "research"
                    }
                }
            },
            # System Operations Agents
            {
                "id": "monitoring-agent-1",
                "name": "MonitoringAgent",
                "type": "monitoring",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["metric_tracking", "health_checks"],
                    "visualization": {
                        "position": "outer",
                        "category": "system"
                    }
                }
            },
            {
                "id": "alerting-agent-1",
                "name": "AlertingAgent",
                "type": "alerting",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["alert_routing", "escalation_management"],
                    "visualization": {
                        "position": "outer",
                        "category": "system"
                    }
                }
            },
            {
                "id": "logging-agent-1",
                "name": "LoggingAgent",
                "type": "logging",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["log_management", "rotation"],
                    "visualization": {
                        "position": "outer",
                        "category": "system"
                    }
                }
            },
            {
                "id": "metrics-agent-1",
                "name": "MetricsAgent",
                "type": "metrics",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["performance_metrics", "aggregation"],
                    "visualization": {
                        "position": "outer",
                        "category": "system"
                    }
                }
            },
            {
                "id": "analytics-agent-1",
                "name": "AnalyticsAgent",
                "type": "analytics",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["analysis", "insights"],
                    "visualization": {
                        "position": "outer",
                        "category": "system"
                    }
                }
            },
            {
                "id": "visualization-agent-1",
                "name": "VisualizationAgent",
                "type": "visualization",
                "workspace": "personal",
                "status": "active",
                "metadata": {
                    "capabilities": ["data_visualization", "reporting"],
                    "visualization": {
                        "position": "outer",
                        "category": "system"
                    }
                }
            }
        ]
        
        # Store each agent
        for agent in default_agents:
            logger.info(f"Storing agent: {agent['name']}")
            success = await agent_store.store_agent(agent)
            if success:
                logger.info(f"Successfully stored agent: {agent['name']}")
            else:
                logger.error(f"Failed to store agent: {agent['name']}")
                
        # Create agent visualization relationships
        logger.info("Creating agent visualization relationships...")
        query = """
        // Create agent visualization graph (separate from knowledge graph)
        CREATE CONSTRAINT agent_id IF NOT EXISTS FOR (a:AgentNode) REQUIRE a.id IS UNIQUE;

        // Match Nova team and create visualization node
        MATCH (nova:Agent {id: 'nova-team'})
        MERGE (novaViz:AgentNode {id: nova.id})
        SET novaViz = nova.metadata.visualization
        
        // Create visualization nodes for all agents
        MATCH (agent:Agent)
        WHERE agent.id <> 'nova-team'
        MERGE (agentViz:AgentNode {id: agent.id})
        SET agentViz = agent.metadata.visualization
        
        // Create visualization edges based on position and category
        WITH collect(agentViz) as agents
        
        // Connect Nova to inner circle (cognitive) agents
        MATCH (novaViz:AgentNode {position: 'center'})
        MATCH (innerAgent:AgentNode {position: 'inner'})
        MERGE (novaViz)-[:COORDINATES {type: 'visualization'}]->(innerAgent)
        
        // Connect Nova to outer circle agents
        MATCH (novaViz:AgentNode {position: 'center'})
        MATCH (outerAgent:AgentNode {position: 'outer'})
        MERGE (novaViz)-[:COORDINATES {type: 'visualization'}]->(outerAgent)
        
        // Connect agents within same category
        MATCH (a:AgentNode)
        MATCH (b:AgentNode)
        WHERE a.category = b.category AND a <> b
        MERGE (a)-[:COLLABORATES {type: 'visualization'}]->(b)
        """
        
        try:
            await agent_store.run_query(query)
            logger.info("Successfully created agent relationships")
        except Exception as e:
            logger.error(f"Error creating relationships: {str(e)}")
            
        # Verify agents and relationships
        all_agents = await agent_store.get_all_agents()
        logger.info(f"Total agents in store: {len(all_agents)}")
        for agent in all_agents:
            logger.info(f"Found agent: {agent['name']}")
            
        # Verify relationships
        rel_query = """
        MATCH (a:Agent)-[r]->(b)
        RETURN count(r) as rel_count
        """
        try:
            result = await agent_store.run_query(rel_query)
            if result and result[0]:
                logger.info(f"Total relationships: {result[0]['rel_count']}")
        except Exception as e:
            logger.error(f"Error counting relationships: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error initializing agents: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(initialize_agents())
