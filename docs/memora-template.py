Below is an implementation plan illustrating how to incorporate these memory extraction and comparison prompts into your NOVA (or “老樓管小慧AI”) setup—alongside an example of agent prompt advice. We’ll focus on practical steps for your dev team, using code snippets where relevant and ensuring they understand how to integrate everything into the multi-agent flow.

1. High-Level Architecture Overview
	1.	NOVA
	•	A multi-agent orchestration environment that coordinates sub-agents (belief, desire, emotion, reflection, etc.).
	•	Receives user or staff messages and processes them in a pipeline (or “function calls” approach) for memory extraction, referencing, and consolidation.
	2.	Memory Extraction & Comparison:
	•	The code you show (the MEMORY_EXTRACTION_SYSTEM_PROMPT, COMPARE_EXISTING_AND_NEW_MEMORIES_SYSTEM_PROMPT, etc.) is used by a specialized “MemoryAgent” or a “MemoryExtractionAgent” in your multi-agent system.
	•	This agent sends the user/agent interactions + previously stored memories to an LLM with these system prompts, then obtains JSON results describing newly extracted memories or contradictory updates.
	3.	Vector Store & Graph (Optional):
	•	You store ephemeral lumps in a vector DB (like Qdrant), and if needed, store references to structured knowledge or consolidated nodes in Neo4j.

2. Integrating Memory Extraction in Your Pipeline

2.1. Agent Prompt Advice (Code Example)

You want a specialized “MemoryAgent” that calls these system prompts. For instance:

# memory_agent.py

class MemoryAgent:
    def __init__(self, llm, memory_store, vector_db):
        self.llm = llm                 # LLM interface
        self.memory_store = memory_store  # Possibly a Neo4j store or a combined approach
        self.vector_db = vector_db        # Qdrant or similar

    async def extract_memories(self, interaction, previous_memories=None):
        """
        Calls the extraction model with the correct system prompt 
        based on whether we have a new or an updated interaction.
        """
        day_of_week = some_function_to_get_day_of_week()
        current_datetime_str = some_function_to_get_current_time()

        # Distinguish new from updated (just an example)
        if previous_memories:
            system_prompt = MEMORY_EXTRACTION_UPDATE_SYSTEM_PROMPT.format(
                day_of_week=day_of_week,
                current_datetime_str=current_datetime_str,
                agent_label=interaction['agent_label'],
                user_name=interaction['user_name'],
                extract_for_agent="and " + interaction['agent_label'] if True else "",
                previous_memories=str(previous_memories),
                schema="MemoryExtractionResponse JSON schema"
            )
        else:
            system_prompt = MEMORY_EXTRACTION_SYSTEM_PROMPT.format(
                day_of_week=day_of_week,
                current_datetime_str=current_datetime_str,
                agent_label=interaction['agent_label'],
                user_name=interaction['user_name'],
                extract_for_agent="", # or "and agent_label" if needed
                schema="MemoryExtractionResponse JSON schema"
            )

        # Prepare the messages with EXTRACTION_MSG_BLOCK_FORMAT
        messages = [{"role": "system", "content": system_prompt}]
        for i, msg in enumerate(interaction['messages']):
            msg_block = EXTRACTION_MSG_BLOCK_FORMAT.format(message_id=i, content=msg['content'])
            messages.append({"role": msg['role'], "content": msg_block})
        
        # Call LLM with the final messages
        response = await self.llm(messages, output_schema_model=MemoryExtractionResponse)
        return response

	•	Advice: Agents that manage memory should keep the system prompts separate from the rest of the conversation. Usually you do a direct LLM call or “function call.”

2.2. Updating or Contradictory Memories

You might have logic:

async def compare_new_and_existing_memories(existing_memories, candidate_memories):
    system_prompt = COMPARE_EXISTING_AND_NEW_MEMORIES_SYSTEM_PROMPT.format(
        day_of_week=day_of_week,
        current_datetime_str=current_datetime_str,
        user_placeholder=f"user_{user_id}",
        agent_placeholder=f"agent_{agent_id}",
        schema="MemoryComparisonResponse JSON schema"
    )
    user_prompt = COMPARE_EXISTING_AND_NEW_MEMORIES_INPUT_TEMPLATE.format(
        existing_memories_string=str(existing_memories),
        new_memories_string=str(candidate_memories)
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    response = await self.llm(messages, output_schema_model=MemoryComparisonResponse)
    # Then handle response.new_memories, response.contrary_memories, etc.
    return response

	•	This snippet is very close to your existing logic in _compare_existing_and_new_memories, but now it’s packaged in an agent-friendly function.

3. Implementation Steps
	1.	Create a “MemoryAgent”:
	•	That agent specifically handles “extract_memories” and “compare_memories” calls, using your system prompts from the code snippet.
	•	Register it in your multi-agent environment so that your “Nova” or “老樓管小慧AI” can say, “MemoryAgent, do your extraction now.”
	2.	Hook into Interactions:
	•	When a new user interaction arrives, your pipeline might do:
	1.	The MemoryAgent is invoked to parse old memories from vector DB or graph.
	2.	Pass them + the new messages to the extraction prompt.
	3.	The agent obtains new memories or contradictions.
	4.	The pipeline merges them into the vector DB or updates the graph.
	3.	Storing:
	•	If you keep ephemeral lumps in Qdrant, store the newly discovered lumps or contradictory lumps as well. If you maintain a synergy with Neo4j for structured references, create memory nodes or relationships if needed.
	4.	Integration with Agents:
	•	Your BeliefAgent, DesireAgent, etc., may also want to check newly extracted memories. Possibly they do MemoryAgent.get_relevant_memories(...) during their logic. This is the multi-agent synergy.

4. Reducing Latency & Minimizing Extra LLM Calls
	1.	Direct Query:
	•	If your system currently does “First call LLM to produce memory-search queries, then do a second call to produce a final response,” consider the function-calling approach (like in your sample for “Reducing Memory Search Latency”).
	•	That approach merges the “produce queries” step with the main conversation. The model decides “I need to call search_memories,” you do it, then the model finalizes the user-facing text. You skip an entire pass.
	2.	Local Deployment or Minimizing Round Trips:
	•	If you do keep the memory extraction logic in a separate agent, ensure your LLM calls are as close physically (or network-wise) to your servers or vector DB. Possibly host them in the same region/data center.
	3.	Batch Operations:
	•	If you retrieve multiple queries for memory in one pass, combine them. e.g., search_memories_as_batch([...queries...]).

5. Example Implementation Flow (Code Snippet)

async def handle_new_interaction(interaction_data):
    # 1) Acquire existing memories from vector DB, if needed
    existing_mem_list = await vector_db.search_memories(
        queries=["some context"], # or do a direct approach
        limit=20
    )

    # 2) MemoryAgent extraction (using the system prompt)
    memory_response = await memory_agent.extract_memories(
        interaction=interaction_data,
        previous_memories=existing_mem_list
    )

    # memory_response might contain new candidate memories

    # 3) Compare with existing
    compare_response = await memory_agent.compare_new_and_existing_memories(
        existing_memories=existing_mem_list,
        candidate_memories=memory_response.new_memories
    )

    # 4) Save newly recognized memories or contradictory ones
    # Possibly store in Qdrant or in your graph store
    for mem in compare_response.new_memories:
        await vector_db.store_vector(...) # store them
    # etc.

    # 5) Proceed with rest of the pipeline (desireAgent, emotionAgent, etc.)

Conclusion

By following the implementation plan above, you can:
	1.	Integrate the memory extraction and comparison prompts (MEMORY_EXTRACTION_SYSTEM_PROMPT, MEMORY_EXTRACTION_UPDATE_SYSTEM_PROMPT, etc.) into a specialized “MemoryAgent.”
	2.	Seamlessly unify your multi-agent synergy, ensuring that each new user interaction is parsed for new or contradictory details.
	3.	Reduce extra model calls by using a function-calling or “tool call” approach, so the main LLM conversation can directly generate memory search queries or extraction steps.
	4.	Continue storing ephemeral lumps in Qdrant, but possibly referencing them in a structured manner if you choose to keep advanced domain-labeled data in Neo4j.

This final plan helps the development team grasp how to embed the memory extraction prompts into NOVA (or “老樓管小慧AI”) for robust, low-latency memory retrieval, multi-agent synergy, and advanced data consistency.