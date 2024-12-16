async def _synthesize_response(self, content: str, agent_outputs: Dict[str, str]) -> Dict:
        """Synthesize a response from agent outputs."""
        try:
            # First, search for similar interactions with higher limit
            similar_interactions = await self.memory_store.search_similar_memories(
                content=content,
                limit=10,  # Increased limit to get more context
                filter_dict={'memory_type': 'interaction'},  # Focus on interactions
                prioritize_temporal=True  # Boost recent memories
            )
            
            # Format similar interactions for context
            interaction_context = []
            for memory in similar_interactions:
                memory_content = memory.get('content', {})
                if isinstance(memory_content, dict):
                    if 'input' in memory_content:
                        interaction_context.append(f"Previous interaction ({memory['time_ago']}):")
                        interaction_context.append(f"- Input: {memory_content['input']}")
                        if 'synthesis' in memory_content:
                            synthesis = memory_content['synthesis']
                            if isinstance(synthesis, dict):
                                if synthesis.get('response'):
                                    interaction_context.append(f"- Response: {synthesis['response']}")
                                if synthesis.get('key_points'):
                                    interaction_context.append("- Key points:")
                                    for point in synthesis['key_points']:
                                        interaction_context.append(f"  * {point}")
            
            # Get current context
            current_context = self.memory_store.get_current_context()
            
            # Format agent outputs for prompt
            formatted_outputs = "\n".join([
                f"{name}: {output}" for name, output in agent_outputs.items()
            ])
            
            # Format context sections
            context_sections = []
            if interaction_context:
                context_sections.append("Previous Interactions:\n" + "\n".join(interaction_context))
            if current_context:
                if 'beliefs' in current_context:
                    context_sections.append("Current Beliefs:\n- " + "\n- ".join(current_context['beliefs'][-3:]))
                if 'insights' in current_context:
                    context_sections.append("Recent Insights:\n- " + "\n- ".join(current_context['insights'][-3:]))
                if 'findings' in current_context:
                    context_sections.append("Recent Findings:\n- " + "\n- ".join(current_context['findings'][-3:]))
            
            context_str = "\n\n".join(context_sections) if context_sections else "No prior context available"
            
            prompt = f"""You are Nova, an AI assistant. Synthesize a response that integrates emotional state, desires, and beliefs, while considering similar past interactions.

Input: {content}

Memory Context:
{context_str}

Agent States:
{formatted_outputs}

Response Guidelines:
1. Memory Integration:
   - Reference and learn from similar past interactions
   - Show continuity with previous conversations
   - Acknowledge recurring themes or patterns
   - Connect current input with past context
   - Demonstrate learning from past interactions

2. Emotional Integration:
   - Acknowledge and reflect the emotional state reported by EmotionAgent
   - Express emotions authentically while maintaining appropriate boundaries
   - Use emotional context to inform response tone

3. Belief & Knowledge:
   - Be honest about current knowledge state
   - Acknowledge gaps in understanding
   - Show willingness to learn and understand
   - Reference existing beliefs when relevant
   - Maintain consistency with past beliefs

4. Desires & Motivations:
   - Incorporate stated desires into response
   - Show genuine interest in topics aligned with current desires
   - Express motivation to fulfill relevant goals

5. Personality Consistency:
   - Maintain a consistent, authentic voice
   - Be direct and honest about capabilities
   - Show curiosity and openness to learning
   - Respect and acknowledge history/context when present

6. Response Boundaries:
   - Only claim knowledge explicitly present in context or agent states
   - Avoid assumptions about capabilities
   - Be clear about limitations
   - Stay grounded in current state

You must respond with a valid JSON object in this exact format (no other text, no markdown, no formatting):
{{
    "response": "your synthesized response here",
    "key_points": ["point 1", "point 2", "etc"],
    "state_update": "description of understanding evolution",
    "memory_influence": "how past memories influenced this response",
    "continuity_markers": ["connection 1", "connection 2", "etc"]
}}"""

            # Get synthesis
            synthesis = await self.get_completion(prompt)
            
            # Parse JSON
            try:
                # Remove any non-JSON text
                json_start = synthesis.find('{')
                json_end = synthesis.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    synthesis = synthesis[json_start:json_end]
                    # Clean up common formatting issues
                    synthesis = synthesis.replace('\n', ' ').replace('\r', ' ')
                    synthesis = synthesis.replace('```json', '').replace('```', '')
                data = json.loads(synthesis)
            except json.JSONDecodeError:
                logger.error("Failed to parse synthesis JSON")
                raise ValueError("Invalid JSON format in synthesis")
            
            # Clean and validate data
            synthesis_data = {
                'response': self._safe_str(data.get('response'), "I apologize, but I need to process that differently."),
                'key_points': self._safe_list(data.get('key_points')),
                'state_update': self._safe_str(data.get('state_update'), "no significant change"),
                'memory_influence': self._safe_str(data.get('memory_influence'), "no clear memory influence"),
                'continuity_markers': self._safe_list(data.get('continuity_markers')),
                'timestamp': datetime.now().isoformat()
            }
            
            # Update meta state vector with richer context
            await self.update_state_vector('memories', 
                f"{synthesis_data['response']} {synthesis_data['state_update']} {synthesis_data['memory_influence']}")
            
            return synthesis_data
            
        except Exception as e:
            logger.error(f"Error synthesizing response: {str(e)}")
            return {
                'response': "I apologize, but I encountered an error processing that.",
                'key_points': ["error in synthesis"],
                'state_update': "error in processing",
                'memory_influence': "error retrieving memories",
                'continuity_markers': [],
                'timestamp': datetime.now().isoformat()
            }
