"""TinyTroupe visualization agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.visualization import VisualizationAgent as NovaVisualizationAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...memory.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class VisualizationAgent(TinyTroupeAgent, NovaVisualizationAgent):
    """Visualization agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize visualization agent."""
        # Initialize TinyTroupeAgent
        TinyTroupeAgent.__init__(
            self,
            name=name,
            memory_system=memory_system,
            world=world,
            attributes=attributes,
            agent_type="visualization"
        )
        
        # Initialize NovaVisualizationAgent
        NovaVisualizationAgent.__init__(
            self,
            llm=memory_system.llm if memory_system else None,
            store=memory_system.semantic.store if memory_system else None,
            vector_store=memory_system.episodic.store if memory_system else None,
            domain=domain
        )
        
        # Set domain
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize visualization-specific attributes
        self._initialize_visualization_attributes()
        
        # Initialize visualization tracking
        self.active_visualizations = {}  # visualization_id -> visualization_state
        self.visualization_strategies = {}  # strategy_id -> strategy_config
        self.layout_templates = {}  # template_id -> template_config
        self.chart_templates = {}  # template_id -> template_config
        self.rendering_engines = {}  # engine_id -> engine_config
        
    def _initialize_visualization_attributes(self):
        """Initialize visualization-specific attributes."""
        self.define(
            occupation="Advanced Visualization Manager",
            desires=[
                "Process visualizations effectively",
                "Create clear visual representations",
                "Optimize layout and design",
                "Maintain visualization quality",
                "Visualize data efficiently",
                "Generate layouts properly",
                "Create charts accurately",
                "Optimize rendering",
                "Manage interactivity",
                "Adapt to patterns"
            ],
            emotions={
                "baseline": "analytical",
                "towards_visualization": "focused",
                "towards_domain": "mindful",
                "towards_data": "precise",
                "towards_layout": "organized",
                "towards_charts": "creative",
                "towards_rendering": "efficient",
                "towards_interaction": "responsive",
                "towards_adaptation": "adaptive"
            },
            domain=self.domain,
            capabilities=[
                "visualization_processing",
                "layout_optimization",
                "design_enhancement",
                "pattern_visualization",
                "data_visualization",
                "layout_management",
                "chart_handling",
                "render_optimization",
                "interaction_handling",
                "pattern_adaptation"
            ]
        )
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced visualization awareness."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Update visualization tracking
        if visualization_id := content.get("visualization_id"):
            await self._update_visualization_state(visualization_id, content)
            
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on visualization results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on visualization results
                if concept.get("type") == "visualization_result":
                    self.emotions.update({
                        "visualization_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on visualization needs
                if concept.get("type") == "visualization_need":
                    self.desires.append(f"Visualize {concept['name']}")
                    
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
                        
                # Update data state emotions
                if concept.get("type") == "data_state":
                    self.emotions.update({
                        "data_state": concept.get("state", "neutral")
                    })
                    
                # Update layout state emotions
                if concept.get("type") == "layout_state":
                    self.emotions.update({
                        "layout_state": concept.get("state", "neutral")
                    })
                    
                # Update chart state emotions
                if concept.get("type") == "chart_state":
                    self.emotions.update({
                        "chart_state": concept.get("state", "neutral")
                    })
                    
                # Update rendering state emotions
                if concept.get("type") == "rendering_state":
                    self.emotions.update({
                        "rendering_state": concept.get("state", "neutral")
                    })
                    
                # Update interaction state emotions
                if concept.get("type") == "interaction_state":
                    self.emotions.update({
                        "interaction_state": concept.get("state", "neutral")
                    })
                    
        return response
        
    async def process_and_store(
        self,
        content: Dict[str, Any],
        visualization_type: str,
        target_domain: Optional[str] = None
    ):
        """Process visualization and store results with enhanced visualization awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Update visualization strategies if needed
        if strategies := content.get("visualization_strategies"):
            self._update_visualization_strategies(strategies)
            
        # Update layout templates
        if templates := content.get("layout_templates"):
            self._update_layout_templates(templates)
            
        # Update chart templates
        if templates := content.get("chart_templates"):
            self._update_chart_templates(templates)
            
        # Update rendering engines
        if engines := content.get("rendering_engines"):
            self._update_rendering_engines(engines)
            
        # Process visualization
        result = await self.process_visualization(
            content,
            visualization_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store visualization results with enhanced metadata
        await self.store_memory(
            content={
                "type": "visualization_processing",
                "content": content,
                "visualization_type": visualization_type,
                "visualization": {
                    "is_valid": result.is_valid,
                    "visualization": result.visualization,
                    "elements": result.elements,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "visualization_states": self.active_visualizations,
                    "strategy_states": self.visualization_strategies,
                    "layout_states": self.layout_templates,
                    "chart_states": self.chart_templates,
                    "rendering_states": self.rendering_engines,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "visualization",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on visualization result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence visualization completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Visualization failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical visualization issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important elements
        important_elements = [
            e for e in result.elements
            if e.get("importance", 0.0) > 0.8
        ]
        if important_elements:
            await self.record_reflection(
                f"Important visualization elements created in {self.domain} domain",
                domain=self.domain
            )
            
        # Record visualization-specific reflections
        for visualization_id, visualization_state in self.active_visualizations.items():
            if visualization_state.get("needs_attention", False):
                await self.record_reflection(
                    f"Visualization {visualization_id} requires attention in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record strategy state reflections
        for strategy_id, strategy_state in self.visualization_strategies.items():
            if strategy_state.get("needs_optimization", False):
                await self.record_reflection(
                    f"Visualization strategy {strategy_id} needs optimization in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record layout state reflections
        for template_id, template_state in self.layout_templates.items():
            if template_state.get("needs_tuning", False):
                await self.record_reflection(
                    f"Layout template {template_id} needs tuning in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record chart state reflections
        for template_id, template_state in self.chart_templates.items():
            if template_state.get("needs_update", False):
                await self.record_reflection(
                    f"Chart template {template_id} needs update in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record rendering state reflections
        for engine_id, engine_state in self.rendering_engines.items():
            if engine_state.get("needs_review", False):
                await self.record_reflection(
                    f"Rendering engine {engine_id} needs review in {self.domain} domain",
                    domain=self.domain
                )
        
        return result
        
    async def _update_visualization_state(self, visualization_id: str, content: Dict[str, Any]):
        """Update visualization state tracking."""
        if visualization_id not in self.active_visualizations:
            self.active_visualizations[visualization_id] = {
                "status": "active",
                "start_time": datetime.now().isoformat(),
                "type": "unknown",
                "data": None,
                "metadata": {},
                "needs_attention": False,
                "layout": {},
                "chart": {},
                "rendering": {},
                "history": []
            }
            
        visualization_state = self.active_visualizations[visualization_id]
        
        # Update basic state
        if type_ := content.get("visualization_type"):
            visualization_state["type"] = type_
            visualization_state["history"].append({
                "type": type_,
                "timestamp": datetime.now().isoformat()
            })
            
        if data := content.get("visualization_data"):
            visualization_state["data"] = data
            
        # Update metadata
        if metadata := content.get("visualization_metadata", {}):
            visualization_state["metadata"].update(metadata)
            
        # Update layout
        if layout := content.get("visualization_layout", {}):
            visualization_state["layout"].update(layout)
            
        # Update chart
        if chart := content.get("visualization_chart", {}):
            visualization_state["chart"].update(chart)
            
        # Update rendering
        if rendering := content.get("visualization_rendering", {}):
            visualization_state["rendering"].update(rendering)
            visualization_state["needs_attention"] = any(
                render.get("priority", 0.0) > 0.8
                for render in rendering.values()
            )
            
        # Apply layout templates
        for template_id, template in self.layout_templates.items():
            if self._matches_layout_template(content, template):
                await self._apply_layout_template(visualization_id, template_id, template)
                
        # Apply chart templates
        for template_id, template in self.chart_templates.items():
            if self._matches_chart_template(content, template):
                await self._apply_chart_template(visualization_id, template_id, template)
                
        # Apply rendering engines
        for engine_id, engine in self.rendering_engines.items():
            if self._matches_rendering_engine(content, engine):
                await self._apply_rendering_engine(visualization_id, engine_id, engine)
                
    def _update_visualization_strategies(self, strategies: Dict[str, Dict]):
        """Update visualization strategy configurations."""
        for strategy_id, strategy in strategies.items():
            if isinstance(strategy, dict):
                self.visualization_strategies[strategy_id] = {
                    "type": strategy.get("type", "static"),
                    "method": strategy.get("method", "standard"),
                    "parameters": strategy.get("parameters", {}),
                    "needs_optimization": strategy.get("needs_optimization", False),
                    "metadata": strategy.get("metadata", {})
                }
                
    def _update_layout_templates(self, templates: Dict[str, Dict]):
        """Update layout template configurations."""
        for template_id, template in templates.items():
            if isinstance(template, dict):
                self.layout_templates[template_id] = {
                    "type": template.get("type", "static"),
                    "layout": template.get("layout", ""),
                    "composition": template.get("composition", {}),
                    "needs_tuning": template.get("needs_tuning", False),
                    "metadata": template.get("metadata", {})
                }
                
    def _update_chart_templates(self, templates: Dict[str, Dict]):
        """Update chart template configurations."""
        for template_id, template in templates.items():
            if isinstance(template, dict):
                self.chart_templates[template_id] = {
                    "type": template.get("type", "static"),
                    "chart": template.get("chart", ""),
                    "style": template.get("style", {}),
                    "needs_update": template.get("needs_update", False),
                    "metadata": template.get("metadata", {})
                }
                
    def _update_rendering_engines(self, engines: Dict[str, Dict]):
        """Update rendering engine configurations."""
        for engine_id, engine in engines.items():
            if isinstance(engine, dict):
                self.rendering_engines[engine_id] = {
                    "type": engine.get("type", "standard"),
                    "engine": engine.get("engine", ""),
                    "optimization": engine.get("optimization", {}),
                    "needs_review": engine.get("needs_review", False),
                    "metadata": engine.get("metadata", {})
                }
                
    def _matches_layout_template(self, content: Dict[str, Any], template: Dict) -> bool:
        """Check if content matches a layout template."""
        composition = template.get("composition", {})
        if not composition:
            return False
            
        # Check if required layout elements are present
        required_elements = composition.get("required_elements", [])
        if not required_elements:
            return False
            
        return all(
            element in content.get("visualization_layout", {})
            for element in required_elements
        )
        
    def _matches_chart_template(self, content: Dict[str, Any], template: Dict) -> bool:
        """Check if content matches a chart template."""
        chart = template.get("chart", "")
        if not chart:
            return False
            
        # Check chart type against content
        return content.get("visualization_type") == chart
        
    def _matches_rendering_engine(self, content: Dict[str, Any], engine: Dict) -> bool:
        """Check if content matches a rendering engine."""
        engine_type = engine.get("type", "")
        if not engine_type:
            return False
            
        # Check if content requires specific rendering
        return content.get("visualization_rendering", {}).get("type") == engine_type
        
    async def _apply_layout_template(
        self,
        visualization_id: str,
        template_id: str,
        template: Dict
    ):
        """Apply a layout template's composition."""
        visualization_state = self.active_visualizations[visualization_id]
        composition = template.get("composition", {})
        
        if composition:
            try:
                # Apply layout composition
                layout = visualization_state["layout"]
                for element, config in composition.items():
                    if element in layout:
                        layout[element].update(config)
                        
                # Record layout application
                visualization_state["history"].append({
                    "layout_template": template_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Record reflection if needed
                if template.get("needs_tuning", False):
                    await self.record_reflection(
                        f"Layout template {template_id} applied to {visualization_id} needs tuning",
                        domain=self.domain
                    )
                    
            except Exception as e:
                logger.error(f"Error applying layout template: {str(e)}")
                
    async def _apply_chart_template(
        self,
        visualization_id: str,
        template_id: str,
        template: Dict
    ):
        """Apply a chart template's style."""
        visualization_state = self.active_visualizations[visualization_id]
        style = template.get("style", {})
        
        if style:
            try:
                # Apply chart style
                chart = visualization_state["chart"]
                chart.update(style)
                
                # Record chart application
                visualization_state["history"].append({
                    "chart_template": template_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Record reflection if needed
                if template.get("needs_update", False):
                    await self.record_reflection(
                        f"Chart template {template_id} applied to {visualization_id} needs update",
                        domain=self.domain
                    )
                    
            except Exception as e:
                logger.error(f"Error applying chart template: {str(e)}")
                
    async def _apply_rendering_engine(
        self,
        visualization_id: str,
        engine_id: str,
        engine: Dict
    ):
        """Apply a rendering engine's optimization."""
        visualization_state = self.active_visualizations[visualization_id]
        optimization = engine.get("optimization", {})
        
        if optimization:
            try:
                # Apply rendering optimization
                rendering = visualization_state["rendering"]
                rendering.update(optimization)
                
                # Record rendering application
                visualization_state["history"].append({
                    "rendering_engine": engine_id,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Record reflection if needed
                if engine.get("needs_review", False):
                    await self.record_reflection(
                        f"Rendering engine {engine_id} applied to {visualization_id} needs review",
                        domain=self.domain
                    )
                    
            except Exception as e:
                logger.error(f"Error applying rendering engine: {str(e)}")
                
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
                f"VisualizationAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
