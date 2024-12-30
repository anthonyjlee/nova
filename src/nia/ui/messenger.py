"""Native desktop messenger interface for multi-agent communication."""

import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QTextEdit, QPushButton, QLabel, QSplitter,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont

from .handlers.handlers import System2Handler

class AgentChatWindow(QMainWindow):
    """Main chat window with WhatsApp-style interface."""
    
    def __init__(self):
        super().__init__()
        self.handler = System2Handler()
        self.init_ui()
        
    def init_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle('NIA Messenger')
        self.setMinimumSize(800, 600)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - Chat list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Chat list
        self.chat_list = QListWidget()
        self.chat_list.addItems([
            "Nova (Group)",
            "Meta Agent",
            "Belief Agent",
            "Desire Agent",
            "Emotion Agent",
            "Reflection Agent",
            "Research Agent",
            "Task Agent"
        ])
        left_layout.addWidget(self.chat_list)
        
        # Add left panel to splitter
        splitter.addWidget(left_panel)
        
        # Right panel - Chat area
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        right_layout.addWidget(self.chat_history)
        
        # Message input area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        
        self.message_input = QTextEdit()
        self.message_input.setMaximumHeight(100)
        input_layout.addWidget(self.message_input)
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        
        right_layout.addWidget(input_widget)
        
        # Add right panel to splitter
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([200, 600])
        
        self.show()
    
    def send_message(self):
        """Send message to selected agent."""
        message = self.message_input.toPlainText().strip()
        if not message:
            return
            
        # Get selected agent
        selected = self.chat_list.currentItem()
        if not selected:
            return
            
        agent = selected.text()
        
        # Format message
        formatted = f"You -> {agent}: {message}\n"
        self.chat_history.append(formatted)
        
        # Clear input
        self.message_input.clear()
        
        # Process through handler
        response = self.handler.process_message(message, agent)
        
        # Format response
        formatted = f"{agent} -> You: {response}\n"
        self.chat_history.append(formatted)

def main():
    """Run the messenger interface."""
    app = QApplication(sys.argv)
    window = AgentChatWindow()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
