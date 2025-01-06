"""TinyTroupe dialogue agent implementation with enhanced interaction capabilities."""

import logging
from typing import Dict, Any, Optional, List, Set
from datetime import datetime

from ...nova.core.dialogue import DialogueAgent as NovaDialogueAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class DialogueAgent(TinyTroupeAgent, NovaDialogueAgent):
    """Dialogue agent with enhanced interaction capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize dialogue agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaDialogueAgent first
        NovaDialogueAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=self.domain
        )
        
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="dialogue"
        )
        
        # Initialize dialogue-specific attributes
        self._initialize_dialogue_attributes()
        
        # Initialize interaction state
        self.active_conversations: Dict[str, Dict] = {}
        self.participating_agents: Dict[str, Set[str]] = {}
        self.interaction_states: Dict[str, Dict] = {}
        self.flow_controllers: Dict[str, Dict] = {}
        
    def _initialize_dialogue_attributes(self):
        """Initialize dialogue-specific attributes."""
        attributes = {
            "occupation": "Dialogue Coordinator",
            "desires": [
                "Understand conversation flow",
                "Track dialogue context",
                "Ensure coherent exchanges",
                "Maintain domain boundaries",
                "Coordinate multi-agent interactions",
                "Optimize conversation flow",
                "Manage interaction states"
            ],
            "emotions": {
                "baseline": "attentive",
                "towards_analysis": "engaged",
                "towards_domain": "mindful",
                "towards_coordination": "focused",
                "towards_interaction": "responsive"
            },
            "capabilities": [
                "dialogue_analysis",
                "context_tracking",
                "domain_validation",
                "flow_assessment",
                "interaction_coordination",
                "state_management",
                "flow_optimization"
            ]
        }
        self.define(**attributes)
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced interaction awareness."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Update interaction state
        conversation_id = content.get("conversation_id")
        if conversation_id:
            await self._update_interaction_state(conversation_id, content)
        
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on dialogue analysis
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analysis
                if concept.get("type") == "utterance":
                    self.emotions.update({
                        "analysis_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on dialogue needs
                if concept.get("type") == "dialogue_need":
                    self.desires.append(f"Address {concept['name']}")
                    
                # Update emotions based on domain relevance
                if "domain_relevance" in concept:
                    relevance = float(concept["domain_relevance"])
                    if relevance > 0.8:
                        self.emotions.update({
                            "domain_state": "highly_relevant"
                        })
                    elif relevance < 0.3:
                        self.emotions.update({
                            "domain_state": "low_relevance"
                        })
                    
                # Update interaction state based on flow
                if concept.get("type") == "flow_state":
                    await self._update_flow_state(conversation_id, concept)
                    
        return response
        
    async def analyze_and_store(
        self,
        content: Dict[str, Any],
        target_domain: Optional[str] = None
    ):
        """Analyze dialogue and store results with enhanced interaction awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Analyze dialogue
        result = await self.analyze_dialogue(
            content,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store dialogue analysis
        await self.store_memory(
            content={
                "type": "dialogue_analysis",
                "content": content,
                "analysis": {
                    "utterances": result.utterances,
                    "confidence": result.confidence,
                    "context": result.context,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "dialogue",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analysis
        if result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence dialogue analysis achieved in {self.domain} domain",
                domain=self.domain
            )
        elif result.confidence < 0.3:
            await self.record_reflection(
                f"Low confidence dialogue analysis - may need additional context in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for flow factors
        if result.context.get("flow_factors", []):
            await self.record_reflection(
                f"Flow factors identified in {self.domain} domain - monitoring required",
                domain=self.domain
            )
            
        # Record interaction patterns
        if conversation_id := content.get("conversation_id"):
            await self._record_interaction_patterns(conversation_id, result)
        
        return result
        
    async def start_conversation(
        self,
        conversation_id: str,
        participants: List[str],
        metadata: Optional[Dict] = None
    ):
        """Start a new conversation with interaction tracking."""
        self.active_conversations[conversation_id] = {
            "started_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "state": "active"
        }
        
        self.participating_agents[conversation_id] = set(participants)
        
        self.interaction_states[conversation_id] = {
            "turn_count": 0,
            "last_speaker": None,
            "pending_responses": set(),
            "completed_exchanges": [],
            "active_topics": set(),
            "context_stack": []
        }
        
        self.flow_controllers[conversation_id] = {
            "current_phase": "initiation",
            "expected_responses": set(),
            "blocked_topics": set(),
            "priority_queue": [],
            "intervention_needed": False
        }
        
        # Notify coordination agent
        await self._notify_coordination_agent(
            conversation_id,
            "conversation_started",
            {
                "participants": participants,
                "metadata": metadata
            }
        )
        
    async def end_conversation(
        self,
        conversation_id: str,
        reason: Optional[str] = None
    ):
        """End a conversation and cleanup interaction state."""
        if conversation_id in self.active_conversations:
            # Store final state
            final_state = {
                "ended_at": datetime.now().isoformat(),
                "reason": reason,
                "final_state": self.interaction_states.get(conversation_id, {}),
                "final_flow": self.flow_controllers.get(conversation_id, {})
            }
            
            # Store in memory
            await self.store_memory(
                content={
                    "type": "conversation_end",
                    "conversation_id": conversation_id,
                    "state": final_state
                },
                importance=0.7,
                context={
                    "type": "dialogue",
                    "domain": self.domain
                }
            )
            
            # Cleanup
            self.active_conversations.pop(conversation_id, None)
            self.participating_agents.pop(conversation_id, None)
            self.interaction_states.pop(conversation_id, None)
            self.flow_controllers.pop(conversation_id, None)
            
            # Notify coordination agent
            await self._notify_coordination_agent(
                conversation_id,
                "conversation_ended",
                final_state
            )
            
    async def _update_interaction_state(
        self,
        conversation_id: str,
        content: Dict[str, Any]
    ):
        """Update interaction state for a conversation."""
        if conversation_id not in self.interaction_states:
            return
            
        state = self.interaction_states[conversation_id]
        speaker = content.get("speaker")
        
        # Update basic state
        state["turn_count"] += 1
        state["last_speaker"] = speaker
        
        # Update pending responses
        if speaker:
            state["pending_responses"].discard(speaker)
            
        # Update topics
        if topics := content.get("topics", []):
            state["active_topics"].update(topics)
            
        # Update context stack
        if context := content.get("context"):
            state["context_stack"].append(context)
            if len(state["context_stack"]) > 10:  # Keep last 10 contexts
                state["context_stack"].pop(0)
                
        # Check for completed exchanges
        if content.get("completes_exchange"):
            state["completed_exchanges"].append({
                "timestamp": datetime.now().isoformat(),
                "type": content.get("exchange_type", "unknown"),
                "participants": list(state["pending_responses"])
            })
            
    async def _update_flow_state(
        self,
        conversation_id: str,
        flow_concept: Dict
    ):
        """Update conversation flow state."""
        if conversation_id not in self.flow_controllers:
            return
            
        controller = self.flow_controllers[conversation_id]
        
        # Update phase if needed
        if new_phase := flow_concept.get("suggested_phase"):
            controller["current_phase"] = new_phase
            
        # Update expected responses
        if expected := flow_concept.get("expected_responses", []):
            controller["expected_responses"] = set(expected)
            
        # Update blocked topics
        if blocked := flow_concept.get("blocked_topics", []):
            controller["blocked_topics"] = set(blocked)
            
        # Update priority queue
        if priorities := flow_concept.get("priorities", []):
            controller["priority_queue"] = priorities
            
        # Check if intervention needed
        controller["intervention_needed"] = flow_concept.get("needs_intervention", False)
        
        if controller["intervention_needed"]:
            await self._handle_flow_intervention(conversation_id, flow_concept)
            
    async def _handle_flow_intervention(
        self,
        conversation_id: str,
        flow_concept: Dict
    ):
        """Handle needed flow interventions."""
        # Record intervention need
        await self.record_reflection(
            f"Flow intervention needed in conversation {conversation_id}: {flow_concept.get('intervention_reason', 'unknown')}",
            domain=self.domain
        )
        
        # Notify coordination agent
        await self._notify_coordination_agent(
            conversation_id,
            "flow_intervention_needed",
            {
                "reason": flow_concept.get("intervention_reason"),
                "suggested_action": flow_concept.get("suggested_action"),
                "priority": flow_concept.get("intervention_priority", "medium")
            }
        )
        
    async def _record_interaction_patterns(
        self,
        conversation_id: str,
        analysis_result: Any
    ):
        """Record identified interaction patterns."""
        if not hasattr(analysis_result, "context"):
            return
            
        patterns = []
        
        # Extract patterns from flow factors
        if flow_factors := analysis_result.context.get("flow_factors", []):
            for factor in flow_factors:
                if factor.get("weight", 0) > 0.7:  # High importance factors
                    patterns.append({
                        "type": "flow_pattern",
                        "pattern": factor["factor"],
                        "confidence": factor["weight"]
                    })
                    
        # Extract patterns from utterances
        for utterance in analysis_result.utterances:
            if utterance.get("confidence", 0) > 0.8:  # High confidence utterances
                patterns.append({
                    "type": "utterance_pattern",
                    "pattern": utterance["statement"],
                    "confidence": utterance["confidence"]
                })
                
        # Store patterns if found
        if patterns:
            await self.store_memory(
                content={
                    "type": "interaction_patterns",
                    "conversation_id": conversation_id,
                    "patterns": patterns,
                    "timestamp": datetime.now().isoformat()
                },
                importance=0.6,
                context={
                    "type": "dialogue",
                    "domain": self.domain
                }
            )
            
    async def _notify_coordination_agent(
        self,
        conversation_id: str,
        event_type: str,
        event_data: Dict
    ):
        """Notify coordination agent of dialogue events."""
        if self.world and hasattr(self.world, "notify_agent"):
            await self.world.notify_agent(
                "coordination",
                {
                    "type": "dialogue_event",
                    "conversation_id": conversation_id,
                    "event_type": event_type,
                    "event_data": event_data,
                    "timestamp": datetime.now().isoformat(),
                    "source_agent": self.name,
                    "domain": self.domain
                }
            )
            
    async def get_domain_access(self, domain: str) -> bool:
        """Check if agent has access to specified domain."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            return await self.memory_system.semantic.store.get_domain_access(
                self.name,
                domain
            )
        return False
        
    async def validate_domain_access(self, domain: str):
        """Validate access to a domain before processing."""
        if not await self.get_domain_access(domain):
            raise PermissionError(
                f"DialogueAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
