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

from .handlers import System2Handler

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
