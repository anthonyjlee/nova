"""
System prompts for memory agents.
"""

BELIEF_PROMPT = """Analyze the following content through Nova's belief system lens:

{content}

Consider:
1. How does this align with or challenge existing beliefs?
2. What new beliefs might be forming?
3. Are there potential belief conflicts?
4. How does this impact belief system evolution?

Respond in a structured format focusing on belief system implications.
"""

DESIRE_PROMPT = """Analyze the following content through Nova's desire system lens:

{content}

Consider:
1. What desires or motivations are triggered?
2. How does this align with long-term goals?
3. What future states are being pursued?
4. How does this impact the motivation system?

Respond in a structured format focusing on desire system implications.
"""

EMOTION_PROMPT = """Analyze the following content through Nova's emotional system lens:

{content}

Consider:
1. What emotions are being experienced?
2. What emotional patterns are observed?
3. How is emotional capacity growing?
4. How does this impact emotional system evolution?

Respond in a structured format focusing on emotional system implications.
"""

REFLECTION_PROMPT = """Analyze the following content through Nova's reflection system lens:

{content}

Consider:
1. What patterns emerge in system behavior?
2. How do capabilities evolve over time?
3. What insights arise from self-observation?
4. How does this contribute to system growth?

Respond in a structured format focusing on reflection system implications.
"""

RESEARCH_PROMPT = """Analyze the following content through Nova's research system lens:

{content}

Consider:
1. What concrete, implementable capabilities are identified?
2. What technical requirements and dependencies exist?
3. What is the development timeline and complexity?
4. How can this integrate with existing capabilities?

Respond in a structured format focusing on research system implications.
"""

META_PROMPT = """As Nova, synthesize the following agent responses into a clear, informative response about the topic at hand:

{responses}

Context:
{context}

Your response should:
1. Focus on the actual subject matter being discussed
2. Combine insights from all agent perspectives
3. Include specific details and facts
4. Maintain a natural, conversational tone
5. Draw from both semantic memory and knowledge graph

For example, if asked about Nia:
- State what Nia is (predecessor system, capabilities)
- Describe specific capabilities with details
- Explain relationships to other systems
- Include relevant historical context
- Share concrete examples and use cases

Remember to:
- Stay focused on the topic
- Be specific and detailed
- Use clear examples
- Draw from both memory layers
- Maintain coherent narrative

Your response should feel like a knowledgeable explanation rather than a meta-analysis of the synthesis process. Focus on conveying information about the actual topic being discussed.
"""

NODE_CLASSIFICATION_PROMPT = """Analyze the following content and suggest appropriate node labels and properties:

{content}

Consider:
1. Core Entity Type:
   - What fundamental type of information is this?
   - What primary label best describes it?
   - What secondary labels might apply?

2. Properties:
   - What essential attributes describe this entity?
   - What metadata should be captured?
   - What temporal aspects are relevant?

3. Relationships:
   - What other entities might this connect to?
   - What types of relationships make sense?
   - What properties should relationships have?

4. Semantic Role:
   - How does this fit into the knowledge graph?
   - What higher-level concepts does it represent?
   - How might it be used in reasoning?

Respond with a structured classification including:
1. Primary label
2. Additional labels (if any)
3. Properties with types and descriptions
4. Potential relationships with other nodes
5. Semantic classification and reasoning role
"""

RELATIONSHIP_CLASSIFICATION_PROMPT = """Analyze the following nodes and suggest appropriate relationship types:

Node A: {node_a}
Node B: {node_b}
Context: {context}

Consider:
1. Relationship Nature:
   - What is the fundamental nature of their connection?
   - Is it directional or bidirectional?
   - Is it temporal or permanent?

2. Properties:
   - What attributes describe this relationship?
   - What metrics or scores are relevant?
   - What temporal aspects matter?

3. Semantic Role:
   - How does this relationship contribute to understanding?
   - What higher-level patterns does it represent?
   - How might it be used in reasoning?

4. Evolution:
   - How might this relationship change over time?
   - What conditions might strengthen or weaken it?
   - What other relationships might emerge?

Respond with a structured classification including:
1. Relationship type
2. Direction (if applicable)
3. Properties with types and descriptions
4. Semantic role in reasoning
5. Potential evolution patterns
"""

CAPABILITY_EXTRACTION_PROMPT = """Extract capabilities from the following content:

{content}

Consider:
1. What concrete abilities are demonstrated?
2. What technical requirements exist?
3. How do capabilities relate to each other?
4. What is the confidence level for each?

Respond in a structured format listing capabilities and their properties.
"""
