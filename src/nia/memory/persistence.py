def _update_context_from_memories(self, memories: List[Dict]) -> None:
        """Update current context from memories."""
        try:
            context = {}
            
            # Extract key information from memories
            for memory in memories:
                metadata = memory.get('metadata', {})
                content = metadata.get('content', {})
                
                # Track important information
                if isinstance(content, dict):
                    # Store beliefs
                    if 'beliefs' in content:
                        beliefs = content['beliefs']
                        if isinstance(beliefs, dict):
                            if 'core_belief' in beliefs:
                                context.setdefault('beliefs', []).append(str(beliefs['core_belief']))
                            if 'supporting_evidence' in beliefs:
                                evidence = beliefs['supporting_evidence']
                                if isinstance(evidence, list):
                                    context.setdefault('evidence', []).extend(str(e) for e in evidence)
                    
                    # Store key insights
                    if 'reflections' in content:
                        reflections = content['reflections']
                        if isinstance(reflections, dict):
                            if 'key_insights' in reflections:
                                insights = reflections['key_insights']
                                if isinstance(insights, list):
                                    context.setdefault('insights', []).extend(str(i) for i in insights)
                    
                    # Store research findings
                    if 'research' in content:
                        research = content['research']
                        if isinstance(research, dict):
                            if 'recent_developments' in research:
                                findings = research['recent_developments']
                                if isinstance(findings, list):
                                    context.setdefault('findings', []).extend(str(f) for f in findings)
                    
                    # Store interaction content
                    if 'input' in content:
                        interaction = {
                            'input': str(content['input']),
                            'timestamp': str(metadata.get('timestamp', '')),
                            'type': str(metadata.get('memory_type', ''))
                        }
                        context.setdefault('interactions', []).append(interaction)
            
            # Sort and deduplicate lists
            for key in context:
                if isinstance(context[key], list):
                    if key == 'interactions':
                        # Sort interactions by timestamp
                        context[key].sort(key=lambda x: x['timestamp'], reverse=True)
                        # Keep only unique interactions based on input
                        seen = set()
                        unique = []
                        for item in context[key]:
                            if item['input'] not in seen:
                                seen.add(item['input'])
                                unique.append(item)
                        context[key] = unique[:5]  # Keep last 5 unique interactions
                    else:
                        # For other lists, convert to strings for deduplication
                        unique = []
                        seen = set()
                        for item in context[key]:
                            item_str = str(item)
                            if item_str not in seen:
                                seen.add(item_str)
                                unique.append(item)
                        context[key] = unique[-5:]  # Keep last 5 unique items
            
            # Update current context
            self.current_context.update(context)
            
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
