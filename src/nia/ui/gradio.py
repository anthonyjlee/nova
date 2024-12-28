"""Mobile UI interface for NIA chat system with WhatsApp-style interface."""

import gradio as gr
import logging
import os
import platform
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

from nia.ui.handlers import System2Handler, MemoryHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MobileUI:
    def __init__(self):
        """Initialize the mobile UI."""
        logger.info("Initializing mobile UI...")
        
        self.title = "NIA Chat"
        self.description = """
        # NIA Chat Interface
        
        **Nova (Main)**: Synthesized responses and key insights
        **Nova Orchestration**: View agent interactions and task coordination
        """
        
        # Initialize handlers
        logger.info("Initializing handlers...")
        try:
            self.memory = MemoryHandler()
            self.system2 = System2Handler()
        except Exception as e:
            logger.warning(f"Failed to initialize handlers: {e}")
            self.memory = None
            self.system2 = None
        
        # Initialize chat histories
        self.nova_history = []  # Main Nova thread
        self.orchestration_history = []  # Agent dialogue thread
        self.debug_output = []  # Terminal-style debug output
        
        logger.info("Mobile UI initialization complete")

    def create_chat_interface(self) -> gr.Blocks:
        """Create the WhatsApp-style chat interface."""
        # SVG data URLs
        user_svg = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIxOSIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzI1NjNlYiIgc3Ryb2tlLXdpZHRoPSIyIi8+PGNpcmNsZSBjeD0iMjAiIGN5PSIxNSIgcj0iNiIgZmlsbD0iIzI1NjNlYiIvPjxwYXRoIGQ9Ik04IDM1YzAtOCA2LTEzIDEyLTEzczEyIDUgMTIgMTMiIGZpbGw9IiMyNTYzZWIiLz48L3N2Zz4="
        nova_svg = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIxOSIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzEwYjk4MSIgc3Ryb2tlLXdpZHRoPSIyIi8+PGNpcmNsZSBjeD0iMjAiIGN5PSIxNSIgcj0iNiIgZmlsbD0iIzEwYjk4MSIvPjxwYXRoIGQ9Ik04IDM1YzAtOCA2LTEzIDEyLTEzczEyIDUgMTIgMTMiIGZpbGw9IiMxMGI5ODEiLz48Y2lyY2xlIGN4PSIxNyIgY3k9IjE0IiByPSIxLjUiIGZpbGw9IndoaXRlIi8+PGNpcmNsZSBjeD0iMjMiIGN5PSIxNCIgcj0iMS41IiBmaWxsPSJ3aGl0ZSIvPjwvc3ZnPg=="
        agents_svg = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48Y2lyY2xlIGN4PSIyMCIgY3k9IjIwIiByPSIxOSIgZmlsbD0id2hpdGUiIHN0cm9rZT0iIzYzNjZmMSIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0iTTEyIDI4TDIwIDEyTDI4IDI4WiIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNjM2NmYxIiBzdHJva2Utd2lkdGg9IjMiLz48L3N2Zz4="
        
        with gr.Blocks(
            title=self.title,
            theme=gr.themes.Default()
        ) as interface:
            gr.Markdown(self.description)
            
            with gr.Tabs() as tabs:
                # Nova's main thread
                with gr.Tab("Nova (Main)", id="nova_main"):
                    nova_chat = gr.Chatbot(
                        value=[],
                        height=400,
                        show_label=False,
                        type="messages",  # Use OpenAI message format
                        elem_id="nova_chat",
                        avatar_images=[
                            user_svg,
                            nova_svg
                        ]
                    )
                    
                    with gr.Row():
                        nova_input = gr.Textbox(
                            show_label=False,
                            placeholder="Message Nova...",
                            container=False
                        )
                        nova_send = gr.Button("Send")
                
                # Nova's orchestration thread
                with gr.Tab("Nova Orchestration", id="nova_orchestration"):
                    with gr.Row():
                        # Main chat area
                        with gr.Column(scale=2):
                            orchestration_chat = gr.Chatbot(
                                value=[],
                                height=400,
                                show_label=False,
                                type="messages",
                                elem_id="orchestration_chat",
                                avatar_images=[
                                    user_svg,
                                    agents_svg
                                ]
                            )
                        
                        # Side panel with agent details
                        with gr.Column(scale=1):
                            with gr.Accordion("Active Agents", open=True):
                                active_agents = gr.HighlightedText(
                                    value=[],
                                    label="Currently Active",
                                    show_label=False
                                )
                            
                            with gr.Accordion("Key Concepts", open=True):
                                key_concepts = gr.HighlightedText(
                                    value=[],
                                    label="Identified Concepts",
                                    show_label=False
                                )
                            
                            with gr.Accordion("Memory Stats", open=True):
                                memory_plot = gr.Plot(
                                    label="Memory Distribution"
                                )
                            
                            with gr.Accordion("Agent Network", open=True):
                                agent_plot = gr.Plot(
                                    label="Agent Interactions"
                                )
                            
                            with gr.Accordion("Concept Gallery", open=True):
                                concept_gallery = gr.Gallery(
                                    label="Visual Concepts",
                                    columns=2,
                                    height=200
                                )
                
                # Neo4j Graph View
                with gr.Tab("Knowledge Graph", id="neo4j_view"):
                    with gr.Row():
                        # Graph visualization
                        with gr.Column(scale=3):
                            # HTML component for Cytoscape.js
                            graph_view = gr.HTML("""
                                <div id="cy" style="width: 100%; height: 500px; border: 1px solid #ccc;"></div>
                                <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
                                <script>
                                    document.addEventListener('DOMContentLoaded', function() {
                                        var cy = cytoscape({
                                            container: document.getElementById('cy'),
                                            style: [
                                                {
                                                    selector: 'node',
                                                    style: {
                                                        'label': 'data(label)',
                                                        'background-color': '#666',
                                                        'color': '#fff'
                                                    }
                                                },
                                                {
                                                    selector: 'edge',
                                                    style: {
                                                        'label': 'data(label)',
                                                        'curve-style': 'bezier',
                                                        'target-arrow-shape': 'triangle'
                                                    }
                                                }
                                            ]
                                        });
                                        
                                        // Function to update graph data
                                        window.updateGraph = function(data) {
                                            cy.json(data);
                                            cy.layout({name: 'cose'}).run();
                                        };
                                    });
                                </script>
                            """)
                        
                        # Cypher and controls
                        with gr.Column(scale=1):
                            with gr.Accordion("Cypher Query", open=True):
                                cypher_input = gr.Textbox(
                                    placeholder="MATCH (n) RETURN n LIMIT 10",
                                    label="Cypher Query"
                                )
                                run_query = gr.Button("Run Query")
                            
                            with gr.Accordion("Graph Controls", open=True):
                                layout_select = gr.Dropdown(
                                    choices=["cose", "circle", "grid", "random"],
                                    value="cose",
                                    label="Layout"
                                )
                                refresh_graph = gr.Button("Refresh Graph")
                            
                            with gr.Accordion("Node Info", open=True):
                                node_info = gr.JSON(
                                    value={},
                                    label="Selected Node Details"
                                )
                
                # Settings and CLI access
                with gr.Tab("Settings", id="settings"):
                    gr.Markdown("## System Commands")
                    
                    # Command input
                    with gr.Row():
                        cli_input = gr.Textbox(
                            show_label=False,
                            placeholder="Enter command (e.g., status, search <query>, reset, help)",
                            container=False
                        )
                        cli_send = gr.Button("Execute")
                    
                    # Command output
                    cli_output = gr.Markdown(
                        value="*Command output will appear here*\n\n" + 
                              "Available commands:\n" +
                              "- status: Check system status\n" +
                              "- search <query>: Search memories\n" +
                              "- reset: Reset system state\n" +
                              "- help: Show this help message\n" +
                              "- consolidate: Force memory consolidation",
                        elem_id="cli_output"
                    )
            
            # Debug output area
            with gr.Accordion("Debug Output", open=True):
                debug_output = gr.Markdown(
                    value="*Debug information will appear here*",
                    elem_id="debug_output"
                )
                
                # Auto-refresh toggle for debug output
                debug_refresh = gr.Checkbox(
                    label="Auto-refresh debug output",
                    value=True
                )
            
            # Initialize state
            chat_state = gr.State({
                'active_agents': [],
                'concepts': [],
                'memory_stats': {},
                'agent_interactions': []
            })
            
            # Add handlers
            nova_input.submit(
                self.handle_nova_message,
                inputs=[nova_input, nova_chat, chat_state],
                outputs=[
                    nova_input,  # Clear input
                    nova_chat,   # Update Nova chat
                    orchestration_chat,  # Update orchestration view
                    active_agents,  # Update active agents
                    key_concepts,  # Update key concepts
                    memory_plot,  # Update memory stats
                    agent_plot,  # Update agent network
                    concept_gallery,  # Update concept visuals
                    chat_state,  # Update state
                    debug_output  # Update debug output
                ]
            )
            
            nova_send.click(
                self.handle_nova_message,
                inputs=[nova_input, nova_chat, chat_state],
                outputs=[
                    nova_input,
                    nova_chat,
                    orchestration_chat,
                    active_agents,
                    key_concepts,
                    memory_plot,
                    agent_plot,
                    concept_gallery,
                    chat_state,
                    debug_output
                ]
            )
            
            # Neo4j graph handlers
            run_query.click(
                self.handle_cypher_query,
                inputs=[cypher_input],
                outputs=[graph_view, node_info]
            )
            
            refresh_graph.click(
                self.refresh_graph_view,
                inputs=[layout_select],
                outputs=[graph_view]
            )
            
            # CLI handlers
            cli_input.submit(
                self.handle_cli_command,
                inputs=[cli_input],
                outputs=[cli_input, cli_output]
            )
            
            cli_send.click(
                self.handle_cli_command,
                inputs=[cli_input],
                outputs=[cli_input, cli_output]
            )
            
        return interface

    async def handle_cli_command(
        self,
        command: str
    ) -> Tuple[str, str]:
        """Handle CLI commands."""
        try:
            if not command:
                return "", cli_output.value
            
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
                        "### Active Agents:",
                        *[f"- {agent}" for agent in status.get('active_agents', [])],
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
                        "",
                        "Reset complete"
                    ])
                    await self.system2.nova.cleanup()
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

    async def handle_nova_message(
        self,
        message: str,
        history: List[Dict[str, str]],
        state: Dict[str, Any]
    ) -> Tuple[str, List[Dict[str, str]], List[Dict[str, str]], List[Tuple[str, str]], List[Tuple[str, str]], Any, Any, List[Dict[str, str]], Dict[str, Any], str]:
        """Handle messages in Nova's main thread."""
        try:
            # Format debug output
            debug_lines = []
            debug_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] Processing message: {message}")
            
            # Add user message to Nova chat
            history.append({
                "role": "user",
                "content": message
            })
            
            if self.system2:
                # Process through Nova
                response = await self.system2.send_message(
                    message=message,
                    chat_history=history,
                    agent="Nova (Main)"
                )
                
                # Update Nova chat with response
                updated_history = response[0]
                
                # Extract agent whispers and interactions for orchestration view
                agent_interactions = []
                
                # First add thinking message
                agent_interactions.append({
                    "role": "assistant",
                    "content": "Let me think about this...",
                    "metadata": {"title": "🧠 Thinking"}
                })
                
                # Add whispers if available
                if response[1] and response[1].get("whispers"):
                    for whisper in response[1]["whispers"]:
                        # Extract agent type from whisper (e.g., "*Emotion agent whispers: ..." -> "emotion")
                        agent_type = "assistant"
                        if "*" in whisper and "whispers:" in whisper.lower():
                            agent_name = whisper.split("whispers:")[0].strip("*").lower()
                            if "agent" in agent_name:
                                agent_type = agent_name.replace("agent", "").strip()
                        
                        agent_interactions.append({
                            "role": agent_type,
                            "content": whisper,
                            "metadata": {"title": "🤫 Whisper"}
                        })
                
                # Add agent interactions
                if response[1] and response[1].get("agent_interactions"):
                    for interaction in response[1]["agent_interactions"]:
                        # Extract agent type from content
                        agent_type = "assistant"
                        content = interaction['content']
                        
                        if content.startswith('['):
                            agent_name = content.split(']')[0][1:].lower()
                            if "agent" in agent_name:
                                agent_type = agent_name.replace("agent", "").strip()
                                content = content.split(']', 1)[1].strip()
                        
                        agent_interactions.append({
                            "role": agent_type,
                            "content": content,
                            "metadata": {"title": f"💭 {agent_type.capitalize()}"}
                        })
                    
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
                
                # Update orchestration history
                self.orchestration_history.extend(agent_interactions)
                
                # Update state with active agents and concepts
                state['active_agents'] = list(set(agent_type for interaction in agent_interactions if 'agent_type' in interaction))
                state['concepts'] = response[1].get('concepts', []) if response[1] else []
                
                # Format active agents for highlighted text
                active_agents_text = [(agent, "active") for agent in state['active_agents']]
                
                # Format concepts for highlighted text
                concepts_text = [(concept['name'], concept['type']) for concept in state['concepts']]
                
                # Generate memory stats plot
                memory_stats = await self.system2.nova.get_status()
                memory_fig = {
                    'data': [
                        {'x': ['Episodic', 'Semantic'], 
                         'y': [memory_stats['vector_store'].get('episodic_count', 0),
                              memory_stats['vector_store'].get('semantic_count', 0)],
                         'type': 'bar'}
                    ],
                    'layout': {'title': 'Memory Distribution'}
                }
                
                # Generate agent network plot
                agent_fig = {
                    'data': [
                        {'x': list(state['active_agents']),
                         'y': [1] * len(state['active_agents']),
                         'type': 'scatter',
                         'mode': 'markers+text',
                         'text': state['active_agents']}
                    ],
                    'layout': {'title': 'Active Agents'}
                }
                
                # Generate concept gallery
                concept_images = []  # In a real implementation, you might generate concept visualizations
                
                return (
                    "",  # Clear input
                    updated_history,  # Update Nova chat
                    self.orchestration_history,  # Update orchestration view
                    active_agents_text,  # Update active agents
                    concepts_text,  # Update key concepts
                    memory_fig,  # Update memory stats
                    agent_fig,  # Update agent network
                    concept_images,  # Update concept gallery
                    state,  # Update state
                    "\n".join(debug_lines)  # Update debug output
                )
            else:
                # Fallback if handler not available
                history.append({
                    "role": "assistant",
                    "content": "I'm sorry, but I'm currently unable to process messages. Please try again later."
                })
                debug_lines.append("[ERROR] System2Handler not available")
                
                return (
                    "",
                    history,
                    [],
                    [],  # Empty active agents
                    [],  # Empty concepts
                    {},  # Empty memory plot
                    {},  # Empty agent plot
                    [],  # Empty gallery
                    state,  # Keep state
                    "\n".join(debug_lines)
                )
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            history.append({
                "role": "assistant",
                "content": f"Error: {str(e)}"
            })
            debug_lines.append(f"[ERROR] {str(e)}")
            
            return (
                "",
                history,
                [],
                [],  # Empty active agents
                [],  # Empty concepts
                {},  # Empty memory plot
                {},  # Empty agent plot
                [],  # Empty gallery
                state,  # Keep state
                "\n".join(debug_lines)
            )


    async def handle_cypher_query(
        self,
        query: str
    ) -> Tuple[str, Dict]:
        """Handle Cypher query and update graph view."""
        try:
            if not query:
                return self.get_default_graph(), {}
            
            if self.system2:
                # Execute query through Neo4j store
                results = await self.system2.nova.store.execute_cypher(query)
                
                # Convert results to Cytoscape.js format
                elements = []
                
                # Process nodes
                nodes = set()
                for record in results:
                    for value in record.values():
                        if hasattr(value, 'id') and hasattr(value, 'labels'):
                            # This is a node
                            node_id = str(value.id)
                            if node_id not in nodes:
                                nodes.add(node_id)
                                elements.append({
                                    'data': {
                                        'id': node_id,
                                        'label': value.get('name', ''),
                                        'type': list(value.labels)[0],
                                        'properties': dict(value)
                                    }
                                })
                        elif hasattr(value, 'type'):
                            # This is a relationship
                            elements.append({
                                'data': {
                                    'id': f"e{value.id}",
                                    'source': str(value.start_node.id),
                                    'target': str(value.end_node.id),
                                    'label': value.type
                                }
                            })
                
                # Generate Cytoscape.js initialization code
                graph_data = {
                    'elements': elements
                }
                
                # Update graph view
                graph_js = f"""
                    <script>
                        window.updateGraph({graph_data});
                    </script>
                """
                
                return graph_js, {'query': query, 'results': len(results)}
            
            return self.get_default_graph(), {'error': 'Neo4j store not available'}
            
        except Exception as e:
            logger.error(f"Error executing Cypher query: {str(e)}")
            return self.get_default_graph(), {'error': str(e)}
    
    async def refresh_graph_view(
        self,
        layout: str = "cose"
    ) -> str:
        """Refresh the graph view with current data."""
        try:
            if self.system2:
                # Get all nodes and relationships
                query = """
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m
                """
                return await self.handle_cypher_query(query)
            
            return self.get_default_graph()
            
        except Exception as e:
            logger.error(f"Error refreshing graph: {str(e)}")
            return self.get_default_graph()
    
    def get_default_graph(self) -> str:
        """Return default empty graph view."""
        return """
            <div id="cy" style="width: 100%; height: 500px; border: 1px solid #ccc;"></div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    var cy = cytoscape({
                        container: document.getElementById('cy'),
                        elements: [],
                        style: [
                            {
                                selector: 'node',
                                style: {
                                    'label': 'data(label)',
                                    'background-color': '#666',
                                    'color': '#fff'
                                }
                            },
                            {
                                selector: 'edge',
                                style: {
                                    'label': 'data(label)',
                                    'curve-style': 'bezier',
                                    'target-arrow-shape': 'triangle'
                                }
                            }
                        ]
                    });
                });
            </script>
        """
    
    def launch(self, share: bool = True):
        """Launch the mobile UI."""
        try:
            interface = self.create_chat_interface()
            import time
            time.sleep(1)  # Wait for any previous connections to close
            interface.launch(
                server_name="127.0.0.1",
                server_port=7861,  # Use a different port
                share=False,
                inbrowser=True  # Open in browser automatically
            )
        except Exception as e:
            logger.error(f"Error launching UI: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        # Log system information
        logger.info(f"Python version: {platform.python_version()}")
        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'Not set')}")
        
        # Initialize and launch UI
        ui = MobileUI()
        ui.launch()
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        raise
