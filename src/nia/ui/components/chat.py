"""Main chat interface for NIA."""

import logging
import time
import os
import asyncio
from typing import Dict, Any

import gradio as gr
from neo4j import GraphDatabase

from .base import BaseUI
from .ui_components import UIComponents, TabComponents
from ..theme import create_theme
from ..handlers.message_handlers import MessageHandlers
from ..visualization.graph import GraphVisualizer

logger = logging.getLogger(__name__)

class ChatUI(BaseUI):
    # Neo4j configuration
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    """Main chat interface."""
    
    def __init__(
        self,
        neo4j_uri: str = None,
        neo4j_user: str = None,
        neo4j_password: str = None,
        state_dir: str = None
    ):
        """Initialize chat interface."""
        super().__init__(state_dir=state_dir)
        
        # Set Neo4j configuration
        self.neo4j_uri = neo4j_uri or self.NEO4J_URI
        self.neo4j_user = neo4j_user or self.NEO4J_USER
        self.neo4j_password = neo4j_password or self.NEO4J_PASSWORD
        
        # Initialize Neo4j connection
        self.neo4j_driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_user, self.neo4j_password)
        )
        
        # Initialize handlers
        self.message_handlers = MessageHandlers(self.system2, self.state)
        self.graph_visualizer = GraphVisualizer(self.system2, self.state, self.neo4j_driver)
    
    def create_chat_interface(self) -> gr.Blocks:
        """Create the chat interface."""
        with gr.Blocks() as interface:
            gr.Markdown(self.description)
            
            with gr.Tabs() as tabs:
                # Nova's main thread
                with gr.Tab("Nova (Main)", id="nova_main"):
                    main_components = TabComponents.create_main_tab(
                        self.state.state
                    )
                
                # Nova's orchestration thread
                with gr.Tab("Nova Orchestration", id="nova_orchestration"):
                    orchestration_components = TabComponents.create_orchestration_tab(
                        self.state.state
                    )
                
                # Neo4j Graph View
                with gr.Tab("Knowledge Graph", id="neo4j_view"):
                    graph_components = TabComponents.create_graph_tab()
                
                # Settings and CLI access
                with gr.Tab("Settings", id="settings"):
                    settings_components = TabComponents.create_settings_tab()
            
            # Debug output area
            debug_components = TabComponents.create_debug_section()
            
            # Initialize state
            chat_state = gr.State(self.state.state)
            
            # Add handlers
            main_components['input'].submit(
                self.message_handlers.handle_nova_message,
                inputs=[
                    main_components['input'],
                    main_components['chat'],
                    chat_state
                ],
                outputs=[
                    main_components['input'],  # Clear input
                    main_components['chat'],   # Update Nova chat
                    orchestration_components['chat'],  # Update orchestration view
                    orchestration_components['agents'],  # Update active agents
                    orchestration_components['concepts'],  # Update key concepts
                    orchestration_components['gallery'],  # Update concept visuals
                    chat_state,  # Update state
                    debug_components['output']  # Update debug output
                ]
            )
            
            main_components['send'].click(
                self.message_handlers.handle_nova_message,
                inputs=[
                    main_components['input'],
                    main_components['chat'],
                    chat_state
                ],
                outputs=[
                    main_components['input'],  # Clear input
                    main_components['chat'],   # Update Nova chat
                    orchestration_components['chat'],  # Update orchestration view
                    orchestration_components['agents'],  # Update active agents
                    orchestration_components['concepts'],  # Update key concepts
                    orchestration_components['gallery'],  # Update concept visuals
                    chat_state,  # Update state
                    debug_components['output']  # Update debug output
                ]
            )
            
            # Neo4j graph handlers
            graph_components['run'].click(
                self.graph_visualizer.handle_cypher_query,
                inputs=[graph_components['input']],
                outputs=[graph_components['view'], graph_components['info']]
            )
            
            graph_components['refresh'].click(
                self.graph_visualizer.refresh_graph_view,
                inputs=[graph_components['layout']],
                outputs=[graph_components['view']]
            )
            
            # CLI handlers
            settings_components['input'].submit(
                self.message_handlers.handle_cli_command,
                inputs=[settings_components['input']],
                outputs=[settings_components['input'], settings_components['output']]
            )
            
            settings_components['send'].click(
                self.message_handlers.handle_cli_command,
                inputs=[settings_components['input']],
                outputs=[settings_components['input'], settings_components['output']]
            )
            
        return interface
    
    def check_lmstudio(self) -> bool:
        """Check if LMStudio is running."""
        import requests
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=2.0)
            return response.status_code == 200
        except:
            return False

    async def launch(
        self,
        share: bool = True,
        server_name: str = "127.0.0.1",
        server_port: int = None,
        state_dir: str = None
    ):
        """Launch the chat interface."""
        try:
            # Create interface
            interface = self.create_chat_interface()
            time.sleep(1)  # Wait for any previous connections to close
            
            # Add warning banner if LMStudio is not running
            if not self.check_lmstudio():
                logger.warning("LMStudio is not running")
                interface.info = gr.Info(
                    value="⚠️ LMStudio is not running. Please start LMStudio to enable chat functionality.",
                    visible=True,
                    elem_id="lmstudio-warning"
                )
            
            # Launch with provided or default configuration
            interface.queue()  # Enable queuing for async operation
            
            # Launch the interface
            server = interface.launch(
                server_name=server_name,
                server_port=server_port or 7860,
                share=share,
                inbrowser=True,
                show_error=True,
                quiet=False
            )
            
            if server.is_running:
                logger.info("Chat interface launched successfully")
                
                # Keep the server running
                try:
                    while True:
                        await asyncio.sleep(1)
                except (KeyboardInterrupt, asyncio.CancelledError):
                    logger.info("Shutting down chat interface...")
                    server.close()
            else:
                raise Exception("Failed to start server")
        except Exception as e:
            logger.error(f"Error launching UI: {str(e)}")
            raise

    def __del__(self):
        """Clean up Neo4j connection."""
        if hasattr(self, 'neo4j_driver'):
            self.neo4j_driver.close()
