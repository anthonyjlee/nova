"""Nova's core dialogue analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class DialogueResult:
    """Container for dialogue analysis results."""
    
    def __init__(
        self,
        utterances: List[Dict],
        confidence: float,
        metadata: Optional[Dict] = None,
        context: Optional[Dict] = None
    ):
        self.utterances = utterances
        self.confidence = confidence
        self.metadata = metadata or {}
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

class DialogueAgent:
    """Core dialogue analysis functionality for Nova's ecosystem."""
    
    def __init__(
        self,
        llm=None,
        store=None,
        vector_store=None,
        domain: Optional[str] = None
    ):
        self.llm = llm
        self.store = store
        self.vector_store = vector_store
        self.domain = domain or "professional"  # Default to professional domain
        
    async def analyze_dialogue(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> DialogueResult:
        """Analyze dialogue with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Get conversation history if vector store available
            conversation_history = []
            if self.vector_store:
                conversation_history = await self._get_conversation_history(content)
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata,
                        "conversation_history": conversation_history
                    },
                    template="dialogue_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(content, conversation_history)
                
            # Extract and validate components
            utterances = self._extract_utterances(analysis)
            context = self._extract_context(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(utterances, context)
            
            return DialogueResult(
                utterances=utterances,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown")
                },
                context=context
            )
            
        except Exception as e:
            logger.error(f"Dialogue analysis error: {str(e)}")
            return DialogueResult(
                utterances=[],
                confidence=0.0,
                metadata={"error": str(e)},
                context={"error": str(e)}
            )
            
    async def _get_conversation_history(self, content: Dict[str, Any]) -> List[Dict]:
        """Get conversation history from vector store."""
        try:
            if "conversation_id" in content:
                results = await self.vector_store.search(
                    content["conversation_id"],
                    limit=10,
                    metadata_filter={
                        "domain": self.domain,
                        "type": "dialogue"
                    }
                )
                return results
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
        return []
            
    def _basic_analysis(
        self,
        content: Dict[str, Any],
        conversation_history: List[Dict]
    ) -> Dict:
        """Basic dialogue analysis without LLM."""
        utterances = []
        context = {}
        
        # Basic utterance extraction from text
        text = str(content.get("content", "")).lower()
        
        # Basic utterance indicators and their confidences
        utterance_indicators = {
            "says": 0.8,
            "asks": 0.8,
            "replies": 0.7,
            "responds": 0.7,
            "questions": 0.7,
            "states": 0.7,
            "mentions": 0.6,
            "suggests": 0.6
        }
        
        # Check for utterance indicators
        for indicator, base_confidence in utterance_indicators.items():
            if indicator in text:
                # Extract the utterance statement
                start_idx = text.find(indicator) + len(indicator)
                end_idx = text.find(".", start_idx)
                if end_idx == -1:
                    end_idx = len(text)
                    
                utterance_statement = text[start_idx:end_idx].strip()
                if utterance_statement:
                    utterances.append({
                        "statement": utterance_statement,
                        "type": "inferred_utterance",
                        "confidence": base_confidence,
                        "source": "text_analysis"
                    })
                    
        # Add conversation history as context
        if conversation_history:
            context["conversation_history"] = [
                {
                    "content": m.get("content", {}).get("content", ""),
                    "timestamp": m.get("timestamp", ""),
                    "speaker": m.get("speaker", "unknown")
                }
                for m in conversation_history
            ]
                
        return {
            "utterances": utterances,
            "context": context
        }
        
    def _extract_utterances(self, analysis: Dict) -> List[Dict]:
        """Extract and validate utterances."""
        utterances = analysis.get("utterances", [])
        valid_utterances = []
        
        for utterance in utterances:
            if isinstance(utterance, dict) and "statement" in utterance:
                valid_utterance = {
                    "statement": str(utterance["statement"]),
                    "type": str(utterance.get("type", "utterance")),
                    "confidence": float(utterance.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in utterance:
                    valid_utterance["description"] = str(utterance["description"])
                if "source" in utterance:
                    valid_utterance["source"] = str(utterance["source"])
                if "domain_relevance" in utterance:
                    valid_utterance["domain_relevance"] = float(utterance["domain_relevance"])
                if "sentiment" in utterance:
                    valid_utterance["sentiment"] = float(utterance["sentiment"])
                if "intent" in utterance:
                    valid_utterance["intent"] = str(utterance["intent"])
                if "speaker" in utterance:
                    valid_utterance["speaker"] = str(utterance["speaker"])
                    
                valid_utterances.append(valid_utterance)
                
        return valid_utterances
        
    def _extract_context(self, analysis: Dict) -> Dict:
        """Extract and validate context."""
        context = analysis.get("context", {})
        valid_context = {}
        
        if isinstance(context, dict):
            # Extract relevant context fields
            if "conversation_history" in context:
                valid_context["conversation_history"] = [
                    {
                        "content": str(m.get("content", "")),
                        "timestamp": str(m.get("timestamp", "")),
                        "speaker": str(m.get("speaker", "unknown"))
                    }
                    for m in context["conversation_history"]
                    if isinstance(m, dict)
                ]
                
            if "participants" in context:
                valid_context["participants"] = [
                    str(p) for p in context["participants"]
                    if isinstance(p, str)
                ]
                
            if "topics" in context:
                valid_context["topics"] = [
                    str(t) for t in context["topics"]
                    if isinstance(t, str)
                ]
                
            if "domain_factors" in context:
                valid_context["domain_factors"] = {
                    str(k): str(v)
                    for k, v in context["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
            if "flow_factors" in context:
                valid_context["flow_factors"] = [
                    {
                        "factor": str(f.get("factor", "")),
                        "weight": float(f.get("weight", 0.5))
                    }
                    for f in context.get("flow_factors", [])
                    if isinstance(f, dict)
                ]
                
        return valid_context
        
    def _calculate_confidence(
        self,
        utterances: List[Dict],
        context: Dict
    ) -> float:
        """Calculate overall dialogue analysis confidence."""
        if not utterances:
            return 0.0
            
        # Base confidence from utterance confidences
        utterance_conf = sum(u.get("confidence", 0.5) for u in utterances) / len(utterances)
        
        # Context confidence factors
        context_conf = 0.0
        context_weight = 0.0
        
        # Conversation history boosts confidence
        if "conversation_history" in context:
            hist_count = len(context["conversation_history"])
            hist_conf = min(1.0, hist_count * 0.2)  # Cap at 1.0
            context_conf += hist_conf
            context_weight += 1
            
        # Participants boost confidence
        if "participants" in context:
            part_count = len(context["participants"])
            part_conf = min(1.0, part_count * 0.15)  # Cap at 1.0
            context_conf += part_conf
            context_weight += 1
            
        # Topics boost confidence
        if "topics" in context:
            topic_count = len(context["topics"])
            topic_conf = min(1.0, topic_count * 0.1)  # Cap at 1.0
            context_conf += topic_conf
            context_weight += 1
            
        # Domain factors influence confidence
        if "domain_factors" in context:
            domain_conf = min(1.0, len(context["domain_factors"]) * 0.1)
            context_conf += domain_conf
            context_weight += 1
            
        # Flow factors boost confidence
        if "flow_factors" in context:
            flow_conf = min(1.0, len(context["flow_factors"]) * 0.15)
            context_conf += flow_conf
            context_weight += 1
            
        # Calculate final context confidence
        if context_weight > 0:
            context_conf = context_conf / context_weight
            
            # Weighted combination of utterance and context confidence
            return (0.6 * utterance_conf) + (0.4 * context_conf)
        else:
            return utterance_conf
