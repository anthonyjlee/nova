"""Message and command handlers for NIA chat interface."""

import logging
import json
import orjson
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

# JSON Schema for message history
MESSAGE_SCHEMA = {
    "type": "object",
    "required": ["role", "content", "timestamp"],
    "properties": {
        "role": {"type": "string", "enum": ["Human", "Assistant"]},
        "content": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"}
    }
}

# JSON Schema for agent interaction
INTERACTION_SCHEMA = {
    "type": "object",
    "required": ["role", "content", "metadata"],
    "properties": {
        "role": {"type": "string"},
        "content": {"type": "string"},
        "metadata": {
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {"type": "string"}
            }
        }
    }
}

# Define agent categories
SYNTHESIS_AGENTS = {
    'belief': 'Validates beliefs and knowledge',
    'desire': 'Manages goals and aspirations',
    'emotion': 'Processes emotional context',
    'reflection': 'Analyzes patterns and insights',
    'research': 'Adds knowledge and facts',
    'meta': 'Coordinates synthesis'
}

SYSTEM_AGENTS = {
    'parsing': 'Handles structured parsing',
    'structure': 'Manages information organization',
    'task_planner': 'Handles task planning'
}

class MessageHandlers:
    """Handlers for chat messages and commands."""
    
    def __init__(self, system2, state):
        """Initialize handlers with system2 and state."""
        self.system2 = system2
        self.state = state
    
    def _update_state(self, gradio_state: Dict[str, Any], key: str, value: Any):
        """Update both UI state and Gradio state."""
        self.state.set(key, value)
        if gradio_state is not None:
            gradio_state[key] = value
    
    def _extract_agent_type(self, content: str) -> Optional[str]:
        """Extract and validate agent type from content."""
        if content.startswith('['):
            agent_name = content.split(']')[0][1:].lower()
            if "agent" in agent_name:
                agent_type = agent_name.replace("agent", "").strip()
                if agent_type in SYNTHESIS_AGENTS:
                    return agent_type
        return None
    
    async def handle_nova_message(
        self,
        message: str,
        history: List[Dict[str, str]],
        state: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, List[Dict[str, str]], List[Dict[str, str]], List[Tuple[str, str]], List[Tuple[str, str]], List[Dict[str, str]], Dict[str, Any], str]:
        """Handle messages in Nova's main thread."""
        try:
            # Format debug output
            debug_lines = []
            debug_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Processing message: {message}")
            
            # Initialize histories if not present
            if not history:
                history = []
            
            # Initialize state if not present
            if state is None:
                state = {}
            
                # Create and validate user message
                user_message = {
                    "role": "Human",  # Use "Human" instead of "user"
                    "content": message,
                    "timestamp": datetime.now().isoformat()
                }
                validate(instance=user_message, schema=MESSAGE_SCHEMA)
                history.append(user_message)
            
            # Check if LMStudio is required but not running
            if "LMStudio is not running" in str(message):
                history.append({
                    "role": "Assistant",
                    "content": "LMStudio is required but not running. Please start LMStudio and try again.",
                    "timestamp": datetime.now().isoformat()
                })
                return (
                    "",  # Clear input
                    history,  # Update Nova chat
                    [],  # No orchestration history
                    [],  # No active agents
                    [],  # No concepts
                    None,  # No concept gallery
                    state,  # Keep state
                    "LMStudio is required but not running. Please start LMStudio and try again."
                )
            
            # Ensure orchestration history exists
            if 'orchestration_history' not in state:
                state['orchestration_history'] = []
            
            if self.system2:
                # Process through Nova
                response = await self.system2.send_message(
                    message=message,
                    chat_history=history,
                    agent="Nova (Main)"
                )
                
                # Update Nova chat with response and persist in state
                if isinstance(response, tuple) and len(response) >= 1:
                    updated_history = response[0]
                    self._update_state(state, 'nova_history', updated_history)
                else:
                    # Handle error case
                    error_msg = "Error: Invalid response format"
                    updated_history = history + [{
                        "role": "Assistant",  # Use "Assistant" instead of "assistant"
                        "content": error_msg,
                        "timestamp": datetime.now().isoformat()
                    }]
                    self._update_state(state, 'nova_history', updated_history)
                
                # Extract agent whispers and interactions for orchestration view
                agent_interactions = []
                
                # Create and validate thinking message
                thinking_message = {
                    "role": "Meta Agent",  # Use full agent name
                    "content": "Let me think about this...",
                    "metadata": {"title": "🧠 Thinking"}
                }
                validate(instance=thinking_message, schema=INTERACTION_SCHEMA)
                agent_interactions.append(thinking_message)

                # Handle response metadata
                response_metadata = response[1] if isinstance(response, tuple) and len(response) > 1 else {}
                
                # Add whispers if available
                if response_metadata and response_metadata.get("whispers"):
                    for whisper in response_metadata["whispers"]:
                        try:
                            # Extract agent type from whisper
                            if "*" in whisper and "whispers:" in whisper.lower():
                                agent_name = whisper.split("whispers:")[0].strip("*").lower()
                                if "agent" in agent_name:
                                    agent_type = agent_name.replace("agent", "").strip()
                                    if agent_type in SYNTHESIS_AGENTS:
                                        # Create agent name from type
                                        agent_name = f"{agent_type.capitalize()} Agent"
                                        whisper_interaction = {
                                            "role": agent_name,  # Use full agent name
                                            "content": whisper,
                                            "metadata": {"title": "🤫 Whisper"}
                                        }
                                        validate(instance=whisper_interaction, schema=INTERACTION_SCHEMA)
                                        agent_interactions.append(whisper_interaction)
                        except Exception as e:
                            logger.error(f"Error processing whisper: {str(e)}")
                
                # Add agent interactions
                if response_metadata and response_metadata.get("agent_interactions"):
                    for interaction in response_metadata["agent_interactions"]:
                        try:
                            content = interaction['content']
                            agent_type = self._extract_agent_type(content)
                            
                            if agent_type:
                                # Create agent name from type
                                agent_name = f"{agent_type.capitalize()} Agent"
                                agent_interaction = {
                                    "role": agent_name,  # Use full agent name
                                    "content": content.split(']', 1)[1].strip(),
                                    "metadata": {"title": f"💭 {agent_type.capitalize()}"}
                                }
                                validate(instance=agent_interaction, schema=INTERACTION_SCHEMA)
                                agent_interactions.append(agent_interaction)
                        except Exception as e:
                            logger.error(f"Error processing agent interaction: {str(e)}")
                    
                    # Add interactions to debug output
                    debug_lines.append("\nAgent Interactions:")
                    for interaction in agent_interactions:
                        debug_lines.append(f"{interaction['content']}")
                
                # Update debug output
                debug_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Nova processed message")
                if response[1] and response[1].get("concepts"):
                    debug_lines.append("\nValidated Concepts:")
                    for concept in response[1]["concepts"]:
                        debug_lines.append(f"- {concept['name']} ({concept['type']})")
                        debug_lines.append(f"  Description: {concept['description']}")
                
                # Update active agents with categories and tasks
                synthesis_active = []
                system_active = []
                tasks = []
                
                for interaction in agent_interactions:
                    role = interaction.get('role', '').replace(' Agent', '').lower()  # Strip 'Agent' suffix
                    content = interaction.get('content', {})
                    
                    # Extract tasks if present in response
                    if isinstance(content, dict) and 'tasks' in content:
                        tasks.extend(content['tasks'])
                    elif isinstance(content, str):
                        try:
                            content_dict = json.loads(content)
                            if 'tasks' in content_dict:
                                tasks.extend(content_dict['tasks'])
                        except json.JSONDecodeError:
                            pass
                    
                    if role in SYNTHESIS_AGENTS:
                        synthesis_active.append((role, SYNTHESIS_AGENTS[role]))
                    elif role in SYSTEM_AGENTS:
                        system_active.append((role, SYSTEM_AGENTS[role]))
                
                active_agents = {
                    'synthesis': list(set(agent for agent, _ in synthesis_active)),
                    'system': list(set(agent for agent, _ in system_active))
                }
                
                # Store tasks in state if present
                if tasks:
                    self._update_state(state, 'tasks', tasks)
                    logger.info(f"Stored {len(tasks)} tasks in state")
                self._update_state(state, 'active_agents', active_agents)
                
                # Update concepts
                concepts = response[1].get('concepts', []) if response[1] else []
                self._update_state(state, 'concepts', concepts)
                
                # Update orchestration history
                orchestration_history = state.get('orchestration_history', [])
                orchestration_history.extend(agent_interactions)
                self._update_state(state, 'orchestration_history', orchestration_history)
                
                # Ensure agent interactions are persisted
                self._update_state(state, 'agent_interactions', agent_interactions)
                
                # Convert response for storage
                try:
                    # Convert tuple response to list for validation
                    if isinstance(response, tuple):
                        response_list = list(response)
                    else:
                        response_list = response

                    # Create conversation entry
                    conversation_entry = {
                        'message': message,
                        'response': response_list,
                        'timestamp': datetime.now().isoformat(),
                        'context': {
                            'active_agents': active_agents,
                            'concepts': concepts,
                            'agent_interactions': agent_interactions,
                            'whispers': response[1].get('whispers', []) if response[1] else []
                        }
                    }
                except Exception as e:
                    logger.error(f"Error converting response: {str(e)}")
                    conversation_entry = {
                        'message': message,
                        'response': str(response),  # Fallback to string representation
                        'timestamp': datetime.now().isoformat(),
                        'context': {
                            'active_agents': active_agents,
                            'concepts': concepts,
                            'agent_interactions': agent_interactions,
                            'whispers': []
                        }
                    }
                
                # Ensure conversation history exists and update
                conversation_history = state.get('conversation_history', [])
                conversation_history.append(conversation_entry)
                self._update_state(state, 'conversation_history', conversation_history)
                
                # Update semantic memory
                if response[1] and response[1].get('concepts'):
                    concept_network = state.get('concept_network', {})
                    for concept in response[1]['concepts']:
                        if concept['name'] not in concept_network:
                            concept_entry = {
                                'type': concept['type'],
                                'related': concept.get('related', []),
                                'first_seen': datetime.now().isoformat(),
                                'frequency': 1
                            }
                            concept_network[concept['name']] = concept_entry
                        else:
                            concept_network[concept['name']]['frequency'] += 1
                            concept_network[concept['name']]['last_seen'] = datetime.now().isoformat()
                    self._update_state(state, 'concept_network', concept_network)
                
                # Update Neo4j state
                if response[1] and response[1].get('concepts'):
                    graph_filters = [concept['type'] for concept in response[1]['concepts']]
                    view_state = state.get('view_state', {})
                    view_state['graph_filters'] = graph_filters
                    self._update_state(state, 'view_state', view_state)
                
                # Format active agents for highlighted text - only show synthesis agents
                active_agents_text = [(agent, "active") for agent in active_agents['synthesis']]
                
                # Format concepts for highlighted text
                concepts_text = [(concept['name'], concept['type']) for concept in concepts]
                
                # No visualizations for mobile interface
                
                # Format orchestration history for chat display
                formatted_orchestration = []
                for interaction in agent_interactions:  # Use agent_interactions instead of orchestration_history
                    # Format content based on role
                    if interaction["role"] == "Meta Agent":
                        formatted_content = f"🧠 {interaction['content']}"
                    else:
                        # Extract agent type from role
                        agent_type = interaction["role"].replace(" Agent", "").lower()
                        if agent_type in SYNTHESIS_AGENTS:
                            # Format whispers differently
                            if "whispers:" in interaction["content"].lower():
                                formatted_content = f"🤫 {interaction['content']}"
                            else:
                                formatted_content = f"💭 {interaction['content']}"
                        else:
                            formatted_content = interaction['content']
                    
                    formatted_orchestration.append({
                        "role": interaction["role"],
                        "content": formatted_content
                    })

                return (
                    "",  # Clear input
                    updated_history,  # Update Nova chat
                    formatted_orchestration,  # Update orchestration view with formatted messages
                    active_agents_text,  # Update active agents
                    concepts_text,  # Update key concepts
                    None,  # No concept gallery
                    state,  # Update state
                    "\n".join(debug_lines)  # Update debug output
                )
            else:
                # Fallback if handler not available
                history.append({
                    "role": "Assistant",
                    "content": "I'm sorry, but I'm currently unable to process messages. Please try again later."
                })
                debug_lines.append("[ERROR] System2Handler not available")
                
                return (
                    "",
                    history,
                    [],
                    [],  # Empty active agents
                    [],  # Empty concepts
                    None,  # No concept gallery
                    state,  # Keep state
                    "\n".join(debug_lines)
                )
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            history.append({
                "role": "Assistant",
                "content": f"Error: {str(e)}"
            })
            debug_lines.append(f"[ERROR] {str(e)}")
            
            return (
                "",
                history,
                [],
                [],  # Empty active agents
                [],  # Empty concepts
                None,  # No concept gallery
                state,  # Keep state
                "\n".join(debug_lines)
            )
    
    async def handle_cli_command(
        self,
        command: str,
        cli_output_value: Optional[str] = ""
    ) -> Tuple[str, str]:
        """Handle CLI commands."""
        try:
            if not command:
                return "", cli_output_value
            
            command = command.lower().strip()
            output_lines = []
            
            if command == "status":
                if self.system2:
                    status = await self.system2.nova.get_status()
                    output_lines.extend([
                        "## System Status",
                        "",
                        "### Vector Store:",
                        f"- Episodic Layer: {status['vector_store'].get('episodic_count', 0)} memories",
                        f"- Semantic Layer: {status['vector_store'].get('semantic_count', 0)} memories",
                        f"- Last Consolidation: {status['vector_store'].get('last_consolidation', 'Never')}",
                        "",
                        "### Neo4j:",
                        f"- Total Concepts: {status['neo4j'].get('concept_count', 0)}",
                        f"- Relationships: {status['neo4j'].get('relationship_count', 0)}",
                        "",
                        "### Synthesis Agents:",
                        *[f"- {agent.capitalize()}: {desc}" for agent, desc in SYNTHESIS_AGENTS.items()],
                        "",
                        "### System Agents:",
                        *[f"- {agent.capitalize()}: {desc}" for agent, desc in SYSTEM_AGENTS.items()],
                        "",
                        "### Memory Consolidation:",
                        f"- Next scheduled: {status['vector_store'].get('next_consolidation', 'Unknown')}"
                    ])
                else:
                    output_lines.append("Error: System2Handler not available")
            
            elif command.startswith("search "):
                query = command[7:].strip()
                if self.system2:
                    memories = await self.system2.nova.search_memories(query)
                    output_lines.extend([
                        f"## Found {len(memories)} related memories:",
                        ""
                    ])
                    for i, memory in enumerate(memories, 1):
                        output_lines.extend([
                            f"{i}. Layer: {memory.get('layer', 'unknown')}",
                            f"   Score: {memory.get('score', 0):.3f}",
                            f"   Type: {memory.get('type', 'unknown')}",
                            f"   Content: {memory.get('content', '')}",
                            ""
                        ])
                else:
                    output_lines.append("Error: System2Handler not available")
            
            elif command == "reset":
                if self.system2:
                    output_lines.extend([
                        "Resetting system...",
                        "- Clearing episodic memories...",
                        "- Clearing semantic memories...",
                        "- Resetting concept storage...",
                        "- Resetting consolidation timer...",
                        "- Clearing agent states...",
                        "- Clearing Gradio state...",
                        "",
                        "Reset complete"
                    ])
                    # Clear Nova state
                    await self.system2.nova.cleanup()
                    
                    # Clear state while preserving preferences
                    self.state.clear()  # This preserves ui_preferences, concept_network, and saved_queries
                    
                    # Reinitialize handlers and critical state
                    self.state.set('handlers', {
                        'memory': True,
                        'system2': True,
                        'initialized_at': datetime.now().isoformat()
                    })
                    
                    # Update UI components
                    self.state.set('view_state', {
                        'active_tab': 'nova_main',
                        'open_accordions': ['Active Agents', 'Key Concepts'],
                        'graph_filters': [],
                        'last_query': None
                    })
                else:
                    output_lines.append("Error: System2Handler not available")
            
            elif command == "consolidate":
                if self.system2:
                    await self.system2.nova._consolidate_memories()
                    status = await self.system2.nova.get_status()
                    output_lines.extend([
                        "Consolidation complete:",
                        f"- Semantic memories: {status['vector_store'].get('semantic_count', 0)}",
                        f"- Concepts stored: {status['neo4j'].get('concept_count', 0)}",
                        f"- Next consolidation: {status['vector_store'].get('next_consolidation', 'Unknown')}"
                    ])
                else:
                    output_lines.append("Error: System2Handler not available")
            
            elif command == "help":
                output_lines.extend([
                    "## Available commands:",
                    "- exit: Quit the system",
                    "- status: Check detailed system status (memory layers, concepts, agents)",
                    "- search <query>: Search memories across layers with relevance scores",
                    "- reset: Reset all memory stores and system state",
                    "- consolidate: Force memory consolidation",
                    "- help: Show this help message"
                ])
            
            else:
                output_lines.append(f"Unknown command: {command}")
            
            return "", "\n".join(output_lines)
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return "", f"Error: {str(e)}"
