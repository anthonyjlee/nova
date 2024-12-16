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

META_PROMPT = """Synthesize the following agent responses into a coherent meta-cognitive analysis:

{responses}

Context:
{context}

Consider:
1. Integration & Emergence:
   - How do different agent perspectives combine?
   - What emergent patterns or insights arise?
   - What novel capabilities might develop?

2. Self-Awareness & Growth:
   - How is the system evolving?
   - What gaps in knowledge or capabilities exist?
   - How do past experiences inform current understanding?

3. Metacognition:
   - How effective is the current reasoning process?
   - What biases or limitations are present?
   - How can reasoning be improved?

4. Relationship Understanding:
   - How do relationships between concepts develop?
   - What role do emotions play in understanding?
   - How do capabilities build on each other?

5. Future Development:
   - What areas need more exploration?
   - How can learning be more effective?
   - What new capabilities should be pursued?

Respond with a synthesis that demonstrates deep understanding and metacognitive awareness.
Focus on identifying emergent properties and insights that arise from the integration of different perspectives.
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
