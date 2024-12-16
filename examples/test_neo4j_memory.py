"""
Example showing Neo4j memory store with visualization.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from nia.memory.neo4j_store import Neo4jMemoryStore
from nia.dag import TaskType, TaskStatus

async def store_interaction_memory(
    store: Neo4jMemoryStore,
    content: str,
    response: str
) -> str:
    """Store an interaction memory."""
    memory_id = await store.store_memory(
        memory_type="interaction",
        content={
            'input': content,
            'response': response,
            'timestamp': datetime.now().isoformat()
        },
        metadata={
            'importance': 1.0 if "artificial intelligence" in content.lower() else 0.5,
            'interaction_type': 'conversation'
        }
    )
    return memory_id

async def store_task_with_memory(
    store: Neo4jMemoryStore,
    task_type: str,
    task_content: Dict[str, Any]
) -> None:
    """Store a task and its generated memory."""
    # Store task
    task_id = f"{task_type}_{datetime.now().isoformat()}"
    await store.store_task_execution(
        task_id=task_id,
        task_type=task_type,
        content=task_content,
        metadata={
            'status': TaskStatus.COMPLETED.name,
            'task_type': task_type
        }
    )
    
    # Store memory from task
    memory_id = await store.store_memory(
        memory_type="task_result",
        content=task_content,
        metadata={
            'task_id': task_id,
            'task_type': task_type
        }
    )
    
    # Link task to memory
    await store.link_task_memory(task_id, memory_id)

async def print_memory_graph(store: Neo4jMemoryStore, memory_id: str) -> None:
    """Print memory graph in a readable format."""
    graph = await store.get_memory_graph(memory_id)
    
    print("\nMemory Graph:")
    print("============")
    
    print("\nNodes:")
    for node in graph['nodes']:
        labels = ", ".join(node['labels'])
        content = json.loads(node['content']) if 'content' in node else {}
        print(f"- [{labels}] {node['id']}")
        if isinstance(content, dict):
            for key, value in content.items():
                if isinstance(value, str) and len(value) > 50:
                    print(f"  {key}: {value[:50]}...")
                else:
                    print(f"  {key}: {value}")
    
    print("\nEdges:")
    for edge in graph['edges']:
        print(f"- {edge['from']} --[{edge['type']}]--> {edge['to']}")

async def main():
    """Run the example."""
    print("Initializing Neo4j store...")
    store = Neo4jMemoryStore()
    
    try:
        # Store some interactions
        interactions = [
            ("Hello! How are you today?", 
             "I'm doing well, thank you for asking! How can I help you today?"),
            
            ("What do you know about artificial intelligence?",
             "AI is a broad field of computer science focused on creating intelligent machines. " +
             "It encompasses machine learning, neural networks, and natural language processing."),
            
            ("Can you help me learn Python programming?",
             "I'd be happy to help you learn Python! Let's start with the basics. " +
             "Python is a high-level, interpreted programming language known for its readability.")
        ]
        
        print("\nStoring interactions...")
        for content, response in interactions:
            memory_id = await store_interaction_memory(store, content, response)
            print(f"\nStored interaction: {content}")
            await print_memory_graph(store, memory_id)
        
        # Store some task results with beliefs and insights
        tasks = [
            {
                'type': TaskType.ANALYSIS.name,
                'content': {
                    'beliefs': {
                        'core_belief': "User is interested in learning and technology",
                        'confidence': "high",
                        'supporting_evidence': [
                            "Asked about AI",
                            "Interested in Python programming"
                        ]
                    }
                }
            },
            {
                'type': TaskType.REFLECTION.name,
                'content': {
                    'insights': [
                        "User shows systematic learning approach",
                        "Interest in both theoretical and practical aspects"
                    ],
                    'patterns': [
                        "Asks follow-up questions",
                        "Focuses on fundamental concepts"
                    ]
                }
            }
        ]
        
        print("\nStoring tasks and their memories...")
        for task in tasks:
            await store_task_with_memory(store, task['type'], task['content'])
            print(f"\nStored task: {task['type']}")
        
        # Get related memories
        print("\nFinding memories related to 'Python'...")
        related = await store.get_related_memories("Python")
        for memory in related:
            print(f"\nRelated memory ({memory['type']}):")
            content = memory['content']
            if isinstance(content, dict):
                for key, value in content.items():
                    print(f"- {key}: {value}")
        
        print("\nDone!")
        
    finally:
        store.close()

if __name__ == "__main__":
    asyncio.run(main())
