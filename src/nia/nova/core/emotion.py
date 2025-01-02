"""Nova's core emotion analysis functionality."""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class EmotionResult:
    """Container for emotion analysis results."""
    
    def __init__(
        self,
        emotions: List[Dict],
        intensity: float,
        confidence: float,
        metadata: Optional[Dict] = None,
        context: Optional[Dict] = None
    ):
        self.emotions = emotions
        self.intensity = intensity
        self.confidence = confidence
        self.metadata = metadata or {}
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

class EmotionAgent:
    """Core emotion analysis functionality for Nova's ecosystem."""
    
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
        
    async def analyze_emotion(
        self,
        content: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> EmotionResult:
        """Analyze emotional content with domain awareness."""
        try:
            # Add domain to metadata
            metadata = metadata or {}
            metadata["domain"] = self.domain
            
            # Analyze with LLM if available
            if self.llm:
                analysis = await self.llm.analyze(
                    {
                        "content": content,
                        "metadata": metadata
                    },
                    template="emotion_analysis",
                    max_tokens=1000
                )
            else:
                analysis = self._basic_analysis(content)
                
            # Extract and validate components
            emotions = self._extract_emotions(analysis)
            intensity = self._calculate_intensity(emotions)
            context = self._extract_context(analysis)
            
            # Calculate confidence
            confidence = self._calculate_confidence(emotions, intensity)
            
            return EmotionResult(
                emotions=emotions,
                intensity=intensity,
                confidence=confidence,
                metadata={
                    "domain": self.domain,
                    "content_type": content.get("type", "text"),
                    "source": content.get("source", "unknown")
                },
                context=context
            )
            
        except Exception as e:
            logger.error(f"Emotion analysis error: {str(e)}")
            return EmotionResult(
                emotions=[],
                intensity=0.0,
                confidence=0.0,
                metadata={"error": str(e)},
                context={"error": str(e)}
            )
            
    def _basic_analysis(self, content: Dict[str, Any]) -> Dict:
        """Basic emotion analysis without LLM."""
        emotions = []
        context = {}
        
        # Basic emotion detection from keywords
        text = str(content.get("content", "")).lower()
        
        # Basic emotion keywords and their intensities
        emotion_keywords = {
            "happy": 0.8,
            "sad": 0.7,
            "angry": 0.9,
            "afraid": 0.6,
            "surprised": 0.5,
            "disgusted": 0.8
        }
        
        # Check for emotion keywords
        for emotion, base_intensity in emotion_keywords.items():
            if emotion in text:
                emotions.append({
                    "name": emotion,
                    "type": "basic_emotion",
                    "intensity": base_intensity,
                    "confidence": 0.6
                })
                
        # Basic context extraction
        if "context" in content:
            context = content["context"]
            
        return {
            "emotions": emotions,
            "context": context
        }
        
    def _extract_emotions(self, analysis: Dict) -> List[Dict]:
        """Extract and validate emotions."""
        emotions = analysis.get("emotions", [])
        valid_emotions = []
        
        for emotion in emotions:
            if isinstance(emotion, dict) and "name" in emotion:
                valid_emotion = {
                    "name": str(emotion["name"]),
                    "type": str(emotion.get("type", "emotion")),
                    "intensity": float(emotion.get("intensity", 0.5)),
                    "confidence": float(emotion.get("confidence", 0.5))
                }
                
                # Add optional fields
                if "description" in emotion:
                    valid_emotion["description"] = str(emotion["description"])
                if "valence" in emotion:
                    valid_emotion["valence"] = float(emotion["valence"])
                if "arousal" in emotion:
                    valid_emotion["arousal"] = float(emotion["arousal"])
                if "domain_appropriateness" in emotion:
                    valid_emotion["domain_appropriateness"] = float(emotion["domain_appropriateness"])
                    
                valid_emotions.append(valid_emotion)
                
        return valid_emotions
        
    def _calculate_intensity(self, emotions: List[Dict]) -> float:
        """Calculate overall emotional intensity."""
        if not emotions:
            return 0.0
            
        # Weight intensities by confidence
        weighted_intensities = [
            e["intensity"] * e.get("confidence", 0.5)
            for e in emotions
        ]
        
        # Return average weighted intensity
        return sum(weighted_intensities) / len(weighted_intensities)
        
    def _extract_context(self, analysis: Dict) -> Dict:
        """Extract and validate emotional context."""
        context = analysis.get("context", {})
        valid_context = {}
        
        if isinstance(context, dict):
            # Extract relevant context fields
            if "triggers" in context:
                valid_context["triggers"] = [
                    str(t) for t in context["triggers"]
                    if isinstance(t, (str, int, float, bool))
                ]
                
            if "background" in context:
                valid_context["background"] = str(context["background"])
                
            if "domain_factors" in context:
                valid_context["domain_factors"] = {
                    str(k): str(v)
                    for k, v in context["domain_factors"].items()
                    if isinstance(k, str) and isinstance(v, (str, int, float, bool))
                }
                
            if "relationships" in context:
                valid_context["relationships"] = [
                    {
                        "type": str(r.get("type", "unknown")),
                        "target": str(r.get("target", "unknown")),
                        "strength": float(r.get("strength", 0.5))
                    }
                    for r in context.get("relationships", [])
                    if isinstance(r, dict)
                ]
                
        return valid_context
        
    def _calculate_confidence(
        self,
        emotions: List[Dict],
        intensity: float
    ) -> float:
        """Calculate overall emotion analysis confidence."""
        if not emotions:
            return 0.0
            
        # Base confidence from emotion confidences
        emotion_conf = sum(e.get("confidence", 0.5) for e in emotions) / len(emotions)
        
        # Adjust based on intensity (very low or very high intensity might indicate
        # higher confidence in the analysis)
        intensity_factor = abs(intensity - 0.5) * 2  # 0.0-1.0 range
        
        # Consider domain appropriateness if available
        domain_conf = 1.0
        domain_appropriate = [
            e.get("domain_appropriateness", 1.0)
            for e in emotions
            if "domain_appropriateness" in e
        ]
        if domain_appropriate:
            domain_conf = sum(domain_appropriate) / len(domain_appropriate)
            
        # Weighted combination
        return (0.5 * emotion_conf) + (0.3 * intensity_factor) + (0.2 * domain_conf)
