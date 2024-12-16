"""
Response processor for handling LLM outputs and JSON formatting.
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class ResponseProcessor:
    """Handles processing and formatting of LLM responses."""
    
    @staticmethod
    def _safe_str(value: Any, default: str = "") -> str:
        """Safely convert value to string."""
        try:
            if value is None:
                return default
            return str(value)
        except:
            return default
    
    @staticmethod
    def _safe_list(value: Any) -> List:
        """Safely convert value to list."""
        try:
            if isinstance(value, list):
                return value
            elif isinstance(value, str):
                return [value]
            elif value is None:
                return []
            return list(value)
        except:
            return []
    
    def extract_key_points(self, text: str) -> List[str]:
        """Extract key points from natural language text."""
        key_points = []
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            sentences = para.split('. ')
            for sentence in sentences:
                # Look for sentences that seem like key points
                if any(marker in sentence.lower() for marker in 
                      ['first', 'second', 'third', 'finally', 'additionally',
                       'moreover', 'however', 'therefore', 'thus']):
                    key_points.append(sentence.strip())
        
        return key_points[:3]  # Limit to top 3 points
    
    def convert_natural_to_json(self, text: str) -> Dict:
        """Convert natural language response to JSON format."""
        paragraphs = text.split('\n\n')
        main_response = paragraphs[0] if paragraphs else text
        key_points = self.extract_key_points(text)
        
        return {
            'response': main_response,
            'key_points': key_points,
            'state_update': "Response generated from natural language",
            'memory_influence': "Converted from non-JSON response",
            'continuity_markers': []
        }
    
    def process_llm_response(self, synthesis: str) -> Dict:
        """Process LLM response and convert to standard format."""
        try:
            # Remove any non-JSON text
            json_start = synthesis.find('{')
            json_end = synthesis.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                # Try to parse as JSON
                synthesis = synthesis[json_start:json_end]
                # Clean up common formatting issues
                synthesis = synthesis.replace('\n', ' ').replace('\r', ' ')
                synthesis = synthesis.replace('```json', '').replace('```', '')
                try:
                    data = json.loads(synthesis)
                except json.JSONDecodeError:
                    # If JSON parsing fails, treat as natural language
                    data = self.convert_natural_to_json(synthesis)
            else:
                # No JSON found, treat as natural language
                data = self.convert_natural_to_json(synthesis)
            
            # Clean and validate data
            synthesis_data = {
                'response': self._safe_str(data.get('response'), "I apologize, but I need to process that differently."),
                'key_points': self._safe_list(data.get('key_points')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'memory_influence': self._safe_str(data.get('memory_influence'), "no clear memory influence"),
                'continuity_markers': self._safe_list(data.get('continuity_markers')),
                'timestamp': datetime.now().isoformat()
            }
            
            return synthesis_data
            
        except Exception as e:
            logger.error(f"Error processing LLM response: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error processing that.",
                'key_points': ["error in synthesis"],
                'state_update': "error in processing",
                'memory_influence': "error retrieving memories",
                'continuity_markers': [],
                'timestamp': datetime.now().isoformat()
            }
