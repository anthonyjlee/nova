"""UI Event Handlers."""

import os
import json
import logging
import platform
import pyautogui
from PIL import ImageGrab
from screeninfo import get_monitors
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import networkx as nx
import matplotlib.pyplot as plt
from anthropic import Anthropic
from ..memory.neo4j_store import Neo4jMemoryStore

logger = logging.getLogger(__name__)

class System1Handler:
    """Handler for real-time system interactions."""
    
    def __init__(self, api_key: Optional[str] = "IGA3zJxd3AtXLWyVUq9fyNDev7xHD4UGbpwSWW8UejHeuUwO", port: int = 7860):
        """Initialize the handler with API key and port for remote access."""
        # API setup
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
        self.status = "Initialized"
        self.port = port
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort
        pyautogui.PAUSE = 0.1  # Short pause between actions
        
        # Multi-monitor setup
        self.screens = get_monitors()
        self.selected_screen = 0  # Default to primary screen
        self.setup_screen()
        
        # Port forwarding setup
        self.setup_port_forwarding()
        
        # Key mapping setup
        self.key_conversion = {
            "Page_Down": "pagedown",
            "Page_Up": "pageup",
            "Super_L": "win",
            "Escape": "esc"
        }
    
    def update_api_key(self, api_key: str) -> str:
        """Update the API key."""
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
        return "API key updated"
    
    def setup_port_forwarding(self):
        """Set up port forwarding for remote access."""
        try:
            import ngrok
            
            # Configure ngrok
            ngrok.set_auth_token(os.getenv("NGROK_TOKEN", ""))
            
            # Start tunnel
            public_url = ngrok.connect(self.port, "http")
            logger.info(f"Port forwarding active: {public_url}")
            self.public_url = public_url
            
        except Exception as e:
            logger.warning(f"Port forwarding setup failed: {str(e)}")
            self.public_url = None
    
    def setup_screen(self):
        """Set up screen details."""
        # Sort screens by x position
        sorted_screens = sorted(self.screens, key=lambda s: s.x)
        if self.selected_screen < 0 or self.selected_screen >= len(self.screens):
            raise IndexError("Invalid screen index.")
        
        screen = sorted_screens[self.selected_screen]
        self.screen_width = screen.width
        self.screen_height = screen.height
        self.offset_x = screen.x
        self.offset_y = screen.y
        self.bbox = (screen.x, screen.y, 
                    screen.x + screen.width, 
                    screen.y + screen.height)
    
    async def execute_command(
        self,
        command: str,
        screenshot: Optional[str] = None
    ) -> Tuple[str, str, Optional[str]]:
        """Execute a command and return results."""
        try:
            # Parse command to extract action and parameters
            cmd_data = json.loads(command)
            action = cmd_data.get("action")
            text = cmd_data.get("text")
            coordinate = cmd_data.get("coordinate")
            
            # Execute action
            if action == "type":
                if not text:
                    raise ValueError("Text required for type action")
                pyautogui.typewrite(text, interval=0.01)
                output = f"Typed: {text}"
            
            elif action == "key":
                if not text:
                    raise ValueError("Key combination required")
                keys = text.split('+')
                for key in keys:
                    key = self.key_conversion.get(key.strip(), key.strip()).lower()
                    pyautogui.keyDown(key)
                for key in reversed(keys):
                    key = self.key_conversion.get(key.strip(), key.strip()).lower()
                    pyautogui.keyUp(key)
                output = f"Pressed keys: {text}"
            
            elif action == "mouse_move":
                if not coordinate or len(coordinate) != 2:
                    raise ValueError("Coordinate required for mouse move")
                x, y = coordinate
                x += self.offset_x
                y += self.offset_y
                pyautogui.moveTo(x, y)
                output = f"Moved mouse to ({x}, {y})"
            
            elif action in ["left_click", "right_click", "double_click"]:
                if action == "left_click":
                    pyautogui.click()
                elif action == "right_click":
                    pyautogui.rightClick()
                else:
                    pyautogui.doubleClick()
                output = f"Performed {action}"
            
            elif action == "screenshot":
                # Take screenshot
                import base64
                import io
                
                screenshot = ImageGrab.grab(bbox=self.bbox)
                buffer = io.BytesIO()
                screenshot.save(buffer, format="PNG")
                screenshot_base64 = base64.b64encode(buffer.getvalue()).decode()
                
                output = "Screenshot taken"
                return output, "Success", screenshot_base64
            
            else:
                raise ValueError(f"Unknown action: {action}")
            
            self.status = "Command executed successfully"
            return output, self.status, screenshot
            
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            self.status = f"Error: {str(e)}"
            return "", self.status, None

class System2Handler:
    """Handler for Nova agent system."""
    
    def __init__(self):
        """Initialize the handler."""
        self.active_chat = "Nova"
        self.chat_histories: Dict[str, List[Tuple[str, str]]] = {
            "Nova": [],
            "Meta Agent": [],
            "Belief Agent": [],
            "Desire Agent": [],
            "Emotion Agent": [],
            "Reflection Agent": [],
            "Research Agent": []
        }
        self.session_info = {
            "Active Agents": ["Meta", "Belief", "Desire"],
            "Memory Status": "Connected",
            "Last Update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.debug_info = ""
    
    def switch_chat(self, chat_name: str) -> Tuple[List[Tuple[str, str]], Dict, str]:
        """Switch to a different chat."""
        self.active_chat = chat_name
        return (
            self.chat_histories[chat_name],
            self.session_info,
            f"Switched to {chat_name}"
        )
    
    async def send_message(
        self,
        message: str,
        chat_history: List[Tuple[str, str]]
    ) -> Tuple[List[Tuple[str, str]], Dict, str]:
        """Send a message in the current chat."""
        try:
            # Add user message
            chat_history.append(("user", message))
            
            # TODO: Implement agent response logic
            response = f"Received in {self.active_chat}: {message}"
            chat_history.append((self.active_chat, response))
            
            # Update session info
            self.session_info["Last Update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update debug info
            self.debug_info = f"Message processed by {self.active_chat}"
            
            # Save to history
            self.chat_histories[self.active_chat] = chat_history
            
            return chat_history, self.session_info, self.debug_info
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            self.debug_info = f"Error: {str(e)}"
            return chat_history, self.session_info, self.debug_info

class MemoryHandler:
    """Handler for memory system visualization."""
    
    def __init__(self):
        """Initialize the handler."""
        self.store = Neo4jMemoryStore()
        self.stats = {
            "Total Concepts": 0,
            "Total Relationships": 0,
            "Consolidated Memories": 0,
            "Last Consolidation": "-"
        }
    
    def create_graph_visualization(self, data: List[Dict]) -> Any:
        """Create a visualization of the memory graph."""
        G = nx.Graph()
        
        # Create nodes and edges from data
        for item in data:
            G.add_node(item["name"], **item)
            for related in item.get("related", []):
                G.add_edge(item["name"], related)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        
        # Draw nodes
        nx.draw_networkx_nodes(G, pos, node_size=1000)
        nx.draw_networkx_labels(G, pos)
        nx.draw_networkx_edges(G, pos)
        
        return plt.gcf()
    
    async def execute_query(self, query: str) -> Tuple[Any, Dict, Dict]:
        """Execute a Neo4j query and return results."""
        try:
            # Execute query
            if query.lower().startswith("match"):
                # Custom query
                # TODO: Implement custom query execution
                results = []
            else:
                # Quick filter
                results = await self.handle_quick_filter(query)
            
            # Create visualization
            graph = self.create_graph_visualization(results)
            
            # Update stats
            await self.update_stats()
            
            return graph, results, self.stats
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            return None, {"error": str(e)}, self.stats
    
    async def handle_quick_filter(self, filter_name: str) -> List[Dict]:
        """Handle quick filter selections."""
        if filter_name == "Recent Concepts":
            # Get recent concepts
            concepts = await self.store.get_concepts_by_type("recent")
            return concepts
        elif filter_name == "Consolidated Memories":
            # Get consolidated concepts
            concepts = await self.store.search_concepts("is_consolidation:true")
            return concepts
        elif filter_name == "Active Relationships":
            # Get concepts with relationships
            concepts = await self.store.get_concepts_by_type("related")
            return concepts
        elif filter_name == "System State":
            # Get system state concepts
            concepts = await self.store.get_concepts_by_type("state")
            return concepts
        return []
    
    async def update_stats(self):
        """Update memory statistics."""
        try:
            # Get total concepts
            concepts = await self.store.get_concepts_by_type("all")
            self.stats["Total Concepts"] = len(concepts)
            
            # Count relationships
            total_relationships = sum(len(c.get("related", [])) for c in concepts)
            self.stats["Total Relationships"] = total_relationships
            
            # Count consolidated memories
            consolidated = await self.store.search_concepts("is_consolidation:true")
            self.stats["Consolidated Memories"] = len(consolidated)
            
            # Update timestamp
            self.stats["Last Consolidation"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.error(f"Error updating stats: {str(e)}")
