"""TinyTroupe analytics agent implementation."""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...nova.core.analytics import AnalyticsAgent as NovaAnalyticsAgent
from ..tinytroupe_agent import TinyTroupeAgent
from ...world.environment import NIAWorld
from ...memory.two_layer import TwoLayerMemorySystem
from ...core.types.memory_types import AgentResponse

logger = logging.getLogger(__name__)

class AnalyticsAgent(TinyTroupeAgent, NovaAnalyticsAgent):
    """Analytics agent with TinyTroupe and memory capabilities."""
    
    def __init__(
        self,
        name: str,
        memory_system: Optional[TwoLayerMemorySystem] = None,
        world: Optional[NIAWorld] = None,
        attributes: Optional[Dict] = None,
        domain: Optional[str] = None
    ):
        """Initialize analytics agent."""
        # Set domain before initialization
        self.domain = domain or "professional"  # Default to professional domain
        
        # Initialize NovaAnalyticsAgent first
        NovaAnalyticsAgent.__init__(
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
            agent_type="analytics"
        )
        
        # Initialize analytics-specific attributes
        self._initialize_analytics_attributes()
        
        # Initialize analytics tracking
        self.active_analyses = {}  # analysis_id -> analysis_state
        self.analysis_strategies = {}  # strategy_id -> strategy_config
        self.pattern_templates = {}  # template_id -> template_config
        self.insight_models = {}  # model_id -> model_config
        self.trend_detectors = {}  # detector_id -> detector_config
        
    def _initialize_analytics_attributes(self):
        """Initialize analytics-specific attributes."""
        attributes = {
            "occupation": "Advanced Analytics Manager",
            "desires": [
                "Process analytics effectively",
                "Identify patterns and trends",
                "Generate insights",
                "Maintain analytics quality",
                "Analyze data efficiently",
                "Detect patterns properly",
                "Generate insights accurately",
                "Optimize trend analysis",
                "Manage forecasting",
                "Adapt to patterns"
            ],
            "emotions": {
                "baseline": "analytical",
                "towards_analytics": "focused",
                "towards_domain": "mindful",
                "towards_analysis": "precise",
                "towards_patterns": "attentive",
                "towards_insights": "intuitive",
                "towards_trends": "observant",
                "towards_forecasting": "predictive",
                "towards_adaptation": "adaptive"
            },
            "capabilities": [
                "analytics_processing",
                "pattern_recognition",
                "insight_generation",
                "trend_analysis",
                "analysis_optimization",
                "pattern_management",
                "insight_handling",
                "trend_optimization",
                "forecast_handling",
                "pattern_adaptation"
            ]
        }
        self.define(**attributes)
        
    async def process(self, content: Dict[str, Any], metadata: Optional[Dict] = None) -> AgentResponse:
        """Process content through both systems with enhanced analytics awareness."""
        # Add domain to metadata
        metadata = metadata or {}
        metadata["domain"] = self.domain
        
        # Update analysis tracking
        if analysis_id := content.get("analysis_id"):
            await self._update_analysis_state(analysis_id, content)
            
        # Process through memory system
        response = await super().process(content, metadata)
        
        # Update TinyTroupe state based on analytics results
        if response and response.concepts:
            for concept in response.concepts:
                # Update emotions based on analytics results
                if concept.get("type") == "analytics_result":
                    self.emotions.update({
                        "analytics_state": concept.get("description", "neutral")
                    })
                    
                # Update desires based on analytics needs
                if concept.get("type") == "analytics_need":
                    self.desires.append(f"Analyze {concept['name']}")
                    
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
                        
                # Update analysis state emotions
                if concept.get("type") == "analysis_state":
                    self.emotions.update({
                        "analysis_state": concept.get("state", "neutral")
                    })
                    
                # Update pattern state emotions
                if concept.get("type") == "pattern_state":
                    self.emotions.update({
                        "pattern_state": concept.get("state", "neutral")
                    })
                    
                # Update insight state emotions
                if concept.get("type") == "insight_state":
                    self.emotions.update({
                        "insight_state": concept.get("state", "neutral")
                    })
                    
                # Update trend state emotions
                if concept.get("type") == "trend_state":
                    self.emotions.update({
                        "trend_state": concept.get("state", "neutral")
                    })
                    
                # Update forecast state emotions
                if concept.get("type") == "forecast_state":
                    self.emotions.update({
                        "forecast_state": concept.get("state", "neutral")
                    })
                    
        return response
        
    async def process_and_store(
        self,
        content: Dict[str, Any],
        analytics_type: str,
        target_domain: Optional[str] = None
    ):
        """Process analytics and store results with enhanced analytics awareness."""
        # Validate domain access if specified
        if target_domain:
            await self.validate_domain_access(target_domain)
            
        # Update analysis strategies if needed
        if strategies := content.get("analysis_strategies"):
            self._update_analysis_strategies(strategies)
            
        # Update pattern templates
        if templates := content.get("pattern_templates"):
            self._update_pattern_templates(templates)
            
        # Update insight models
        if models := content.get("insight_models"):
            self._update_insight_models(models)
            
        # Update trend detectors
        if detectors := content.get("trend_detectors"):
            self._update_trend_detectors(detectors)
            
        # Process analytics
        result = await self.process_analytics(
            content,
            analytics_type,
            metadata={"domain": target_domain or self.domain}
        )
        
        # Store analytics results with enhanced metadata
        await self.store_memory(
            content={
                "type": "analytics_processing",
                "content": content,
                "analytics_type": analytics_type,
                "analytics": {
                    "is_valid": result.is_valid,
                    "analytics": result.analytics,
                    "insights": result.insights,
                    "confidence": result.confidence,
                    "issues": result.issues,
                    "analysis_states": self.active_analyses,
                    "strategy_states": self.analysis_strategies,
                    "pattern_states": self.pattern_templates,
                    "insight_states": self.insight_models,
                    "trend_states": self.trend_detectors,
                    "timestamp": datetime.now().isoformat()
                }
            },
            importance=0.8,
            context={
                "type": "analytics",
                "domain": target_domain or self.domain
            }
        )
        
        # Record reflection based on analytics result
        if result.is_valid and result.confidence > 0.8:
            await self.record_reflection(
                f"High confidence analytics completed in {self.domain} domain",
                domain=self.domain
            )
        elif not result.is_valid:
            await self.record_reflection(
                f"Analytics failed - issues detected in {self.domain} domain",
                domain=self.domain
            )
            
        # Record reflection for critical issues
        critical_issues = [i for i in result.issues if i.get("severity") == "high"]
        if critical_issues:
            await self.record_reflection(
                f"Critical analytics issues found in {self.domain} domain - immediate attention required",
                domain=self.domain
            )
            
        # Record reflection for important insights
        important_insights = [
            i for i in result.insights
            if i.get("importance", 0.0) > 0.8
        ]
        if important_insights:
            await self.record_reflection(
                f"Important analytics insights discovered in {self.domain} domain",
                domain=self.domain
            )
            
        # Record analysis-specific reflections
        for analysis_id, analysis_state in self.active_analyses.items():
            if analysis_state.get("needs_attention", False):
                await self.record_reflection(
                    f"Analysis {analysis_id} requires attention in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record strategy state reflections
        for strategy_id, strategy_state in self.analysis_strategies.items():
            if strategy_state.get("needs_optimization", False):
                await self.record_reflection(
                    f"Analysis strategy {strategy_id} needs optimization in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record pattern state reflections
        for template_id, template_state in self.pattern_templates.items():
            if template_state.get("needs_tuning", False):
                await self.record_reflection(
                    f"Pattern template {template_id} needs tuning in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record insight state reflections
        for model_id, model_state in self.insight_models.items():
            if model_state.get("needs_update", False):
                await self.record_reflection(
                    f"Insight model {model_id} needs update in {self.domain} domain",
                    domain=self.domain
                )
                
        # Record trend state reflections
        for detector_id, detector_state in self.trend_detectors.items():
            if detector_state.get("needs_review", False):
                await self.record_reflection(
                    f"Trend detector {detector_id} needs review in {self.domain} domain",
                    domain=self.domain
                )
        
        return result
        
    async def _update_analysis_state(self, analysis_id: str, content: Dict[str, Any]):
        """Update analysis state tracking."""
        if analysis_id not in self.active_analyses:
            self.active_analyses[analysis_id] = {
                "status": "active",
                "start_time": datetime.now().isoformat(),
                "type": "unknown",
                "data": None,
                "metadata": {},
                "needs_attention": False,
                "patterns": {},
                "insights": {},
                "trends": {},
                "history": []
            }
            
        analysis_state = self.active_analyses[analysis_id]
        
        # Update basic state
        if type_ := content.get("analysis_type"):
            analysis_state["type"] = type_
            analysis_state["history"].append({
                "type": type_,
                "timestamp": datetime.now().isoformat()
            })
            
        if data := content.get("analysis_data"):
            analysis_state["data"] = data
            
        # Update metadata
        if metadata := content.get("analysis_metadata", {}):
            analysis_state["metadata"].update(metadata)
            
        # Update patterns
        if patterns := content.get("analysis_patterns", {}):
            analysis_state["patterns"].update(patterns)
            
        # Update insights
        if insights := content.get("analysis_insights", {}):
            analysis_state["insights"].update(insights)
            
        # Update trends
        if trends := content.get("analysis_trends", {}):
            analysis_state["trends"].update(trends)
            analysis_state["needs_attention"] = any(
                trend.get("priority", 0.0) > 0.8
                for trend in trends.values()
            )
            
        # Apply pattern templates
        for template_id, template in self.pattern_templates.items():
            if self._matches_pattern_template(content, template):
                await self._apply_pattern_template(analysis_id, template_id, template)
                
        # Apply insight models
        for model_id, model in self.insight_models.items():
            if self._matches_insight_model(content, model):
                await self._apply_insight_model(analysis_id, model_id, model)
                
        # Apply trend detectors
        for detector_id, detector in self.trend_detectors.items():
            if self._matches_trend_detector(content, detector):
                await self._apply_trend_detector(analysis_id, detector_id, detector)
                
    def _update_analysis_strategies(self, strategies: Dict[str, Dict]):
        """Update analysis strategy configurations."""
        for strategy_id, strategy in strategies.items():
            if isinstance(strategy, dict):
                self.analysis_strategies[strategy_id] = {
                    "type": strategy.get("type", "static"),
                    "method": strategy.get("method", "statistical"),
                    "parameters": strategy.get("parameters", {}),
                    "needs_optimization": strategy.get("needs_optimization", False),
                    "metadata": strategy.get("metadata", {})
                }
                
    def _update_pattern_templates(self, templates: Dict[str, Dict]):
        """Update pattern template configurations."""
        for template_id, template in templates.items():
            if isinstance(template, dict):
                self.pattern_templates[template_id] = {
                    "type": template.get("type", "static"),
                    "pattern": template.get("pattern", ""),
                    "recognition": template.get("recognition", {}),
                    "needs_tuning": template.get("needs_tuning", False),
                    "metadata": template.get("metadata", {})
                }
                
    def _update_insight_models(self, models: Dict[str, Dict]):
        """Update insight model configurations."""
        for model_id, model in models.items():
            if isinstance(model, dict):
                self.insight_models[model_id] = {
                    "type": model.get("type", "static"),
                    "algorithm": model.get("algorithm", ""),
                    "parameters": model.get("parameters", {}),
                    "needs_update": model.get("needs_update", False),
                    "metadata": model.get("metadata", {})
                }
                
    def _update_trend_detectors(self, detectors: Dict[str, Dict]):
        """Update trend detector configurations."""
        for detector_id, detector in detectors.items():
            if isinstance(detector, dict):
                self.trend_detectors[detector_id] = {
                    "type": detector.get("type", "time"),
                    "window": detector.get("window", "1h"),
                    "algorithm": detector.get("algorithm", "moving_average"),
                    "needs_review": detector.get("needs_review", False),
                    "metadata": detector.get("metadata", {})
                }
                
    def _matches_pattern_template(self, content: Dict[str, Any], template: Dict) -> bool:
        """Check if content matches a pattern template."""
        recognition = template.get("recognition", {})
        if not recognition:
            return False
            
        # Check pattern against content
        if "data" in content:
            import re
            pattern = recognition.get("pattern", "")
            if pattern:
                return bool(re.search(pattern, str(content["data"])))
                
        return False
        
    def _matches_insight_model(self, content: Dict[str, Any], model: Dict) -> bool:
        """Check if content matches an insight model."""
        parameters = model.get("parameters", {})
        if not parameters:
            return False
            
        # Check if required data is present
        required_fields = parameters.get("required_fields", [])
        if not required_fields:
            return False
            
        return all(field in content for field in required_fields)
        
    def _matches_trend_detector(self, content: Dict[str, Any], detector: Dict) -> bool:
        """Check if content matches a trend detector."""
        algorithm = detector.get("algorithm", "")
        if not algorithm:
            return False
            
        # Check if time series data is present
        if "data" not in content:
            return False
            
        try:
            import pandas as pd
            import numpy as np

            data = content.get("data")
            if data is None:
                return False

            # Handle numpy array
            if isinstance(data, np.ndarray):
                # Convert numpy array to DataFrame if it has the right shape
                if len(data.shape) == 2:
                    data = pd.DataFrame(data)
                else:
                    return False

            # Handle dictionary
            elif isinstance(data, dict):
                data = pd.DataFrame(data)

            # Handle pandas DataFrame
            if isinstance(data, pd.DataFrame):
                return "timestamp" in data.columns

            return False
        except Exception as e:
            logger.error(f"Error in _matches_trend_detector: {str(e)}")
            return False
            
    async def _apply_pattern_template(
        self,
        analysis_id: str,
        template_id: str,
        template: Dict
    ):
        """Apply a pattern template's recognition."""
        analysis_state = self.active_analyses[analysis_id]
        recognition = template.get("recognition", {})
        
        if recognition:
            try:
                # Apply pattern recognition
                import re
                pattern = recognition.get("pattern", "")
                if pattern and "data" in analysis_state:
                    matches = re.findall(pattern, str(analysis_state["data"]))
                    
                    # Update analysis state
                    analysis_state["patterns"][template_id] = {
                        "matches": matches,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Record reflection if needed
                    if template.get("needs_tuning", False):
                        await self.record_reflection(
                            f"Pattern template {template_id} applied to {analysis_id} needs tuning",
                            domain=self.domain
                        )
                        
            except Exception as e:
                logger.error(f"Error applying pattern template: {str(e)}")
                
    async def _apply_insight_model(
        self,
        analysis_id: str,
        model_id: str,
        model: Dict
    ):
        """Apply an insight model's algorithm."""
        analysis_state = self.active_analyses[analysis_id]
        algorithm = model.get("algorithm", "")
        parameters = model.get("parameters", {})
        
        if algorithm and parameters:
            try:
                # Apply insight generation
                import numpy as np
                from sklearn import metrics
                
                data = analysis_state.get("data")
                if data is not None:
                    if algorithm == "clustering":
                        from sklearn.cluster import KMeans
                        n_clusters = parameters.get("n_clusters", 3)
                        kmeans = KMeans(n_clusters=n_clusters)
                        clusters = kmeans.fit_predict(data)
                        silhouette = metrics.silhouette_score(data, clusters)
                        
                        # Update analysis state
                        analysis_state["insights"][model_id] = {
                            "clusters": clusters.tolist(),
                            "silhouette": silhouette,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                    elif algorithm == "anomaly_detection":
                        from sklearn.ensemble import IsolationForest
                        contamination = parameters.get("contamination", 0.1)
                        iso_forest = IsolationForest(contamination=contamination)
                        anomalies = iso_forest.fit_predict(data)
                        
                        # Update analysis state
                        analysis_state["insights"][model_id] = {
                            "anomalies": anomalies.tolist(),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                    # Record reflection if needed
                    if model.get("needs_update", False):
                        await self.record_reflection(
                            f"Insight model {model_id} applied to {analysis_id} needs update",
                            domain=self.domain
                        )
                        
            except Exception as e:
                logger.error(f"Error applying insight model: {str(e)}")
                
    async def _apply_trend_detector(
        self,
        analysis_id: str,
        detector_id: str,
        detector: Dict
    ):
        """Apply a trend detector's algorithm."""
        analysis_state = self.active_analyses[analysis_id]
        algorithm = detector.get("algorithm", "")
        window = detector.get("window", "1h")
        
        if algorithm:
            try:
                # Apply trend detection
                import pandas as pd
                import numpy as np
                
                data = pd.DataFrame(analysis_state.get("data", []))
                if not data.empty and "timestamp" in data.columns:
                    if algorithm == "moving_average":
                        window_size = pd.Timedelta(window)
                        ma = data.rolling(window=window_size).mean()
                        
                        # Update analysis state
                        analysis_state["trends"][detector_id] = {
                            "moving_average": ma.to_dict(),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                    elif algorithm == "exponential_smoothing":
                        from statsmodels.tsa.holtwinters import ExponentialSmoothing
                        model = ExponentialSmoothing(data)
                        fitted = model.fit()
                        
                        # Update analysis state
                        analysis_state["trends"][detector_id] = {
                            "smoothed": fitted.fittedvalues.to_dict(),
                            "timestamp": datetime.now().isoformat()
                        }
                        
                    # Record reflection if needed
                    if detector.get("needs_review", False):
                        await self.record_reflection(
                            f"Trend detector {detector_id} applied to {analysis_id} needs review",
                            domain=self.domain
                        )
                        
            except Exception as e:
                logger.error(f"Error applying trend detector: {str(e)}")
                
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
                f"AnalyticsAgent {self.name} does not have access to domain: {domain}"
            )
            
    async def record_reflection(self, content: str, domain: Optional[str] = None):
        """Record a reflection with domain awareness."""
        if self.memory_system and hasattr(self.memory_system, "semantic"):
            await self.memory_system.semantic.store.record_reflection(
                content=content,
                domain=domain or self.domain
            )
