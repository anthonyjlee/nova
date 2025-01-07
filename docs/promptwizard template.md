PromptWizard is a team of at least three specialized sub-agents (e.g., MutateAgent, CritiqueAgent, SynthesisAgent), spawned by Nova whenever you want to iteratively optimize prompts and examples. 
We’ll show how each agent’s role fits the Slack-like UI, how they exchange partial outputs, and how emergent tasks and memory storage are managed.

1. PromptWizard as a Team of Agents

Whereas a simpler approach might treat “PromptWizard” as a single sub-agent, PromptWizard actually divides tasks among several specialized sub-agents:
	1.	MutateAgent
	•	Takes the user’s (or system’s) base instruction, along with any “thinking style” hints or partial examples.
	•	Generates N mutated instruction variants.
	2.	CritiqueAgent
	•	Critiques each mutated instruction, possibly referencing training data or negative examples.
	•	Produces feedback about weaknesses and potential improvements.
	3.	SynthesisAgent
	•	Synthesizes the top mutated instructions with the CritiqueAgent’s suggestions.
	•	Potentially merges or modifies them into an improved instruction set.
	•	May also handle example selection or generation (especially in Scenario 2 or 3, where examples are relevant).

(Additionally, you might have a “ScoringAgent” or “EvaluationAgent” that runs mini-batch scoring on each mutated instruction, but that could be rolled into either the Critique or Synthesis steps, depending on your design.)

Hence, PromptWizard is realized as a small team of sub-agents working together in iterative cycles:
	1.	Mutate → 2. Critique → 3. Synthesize → (score) → back to Mutate → etc.

2. How Nova Spawns the PromptWizard Team
	1.	User Requests Prompt Optimization
	•	In the main Slack-like channel with Nova, the user says:
	“Please run PromptWizard on my base prompt for a question-answering scenario. I have some training examples.”
	2.	Emergent Task
	•	Nova registers a new emergent task: “PromptWizard #101.”
	•	The user sees a short description: “PromptWizard sub-task, domain=professional, scenario=2 (generate synthetic examples).”
	•	The user approves or revises the sub-task.
	3.	Tiny Factory
	•	Once approved, Nova calls the “tiny factory” to spawn three specialized sub-agents: MutateAgent, CritiqueAgent, and SynthesisAgent (and optionally ScoringAgent if that’s a separate role).
	•	This set of agents is collectively “the PromptWizard group.”
	4.	New Slack-Like Thread
	•	“#promptwizard_101” is created for these sub-agents to do their iterative cycles.
	•	By default, the user only sees high-level summaries. If they want full detail, they can open the sub-thread.

3. Iterative Cycles in the Slack-Like Sub-Thread

3.1. Phase 1: Instruction Mutation
	•	MutateAgent posts:
	•	“We took your base instruction: ‘You are a math solver. Think step-by-step…’
Here are N=4 mutated variants.”

3.2. Phase 1 Scoring
	•	If you have a “ScoringAgent,” it tries each mutated instruction on a mini-batch of training samples (embedding them in the prompt) or does a quick partial test.
	•	Produces a score for each instruction.

3.3. Phase 1 Critique
	•	CritiqueAgent reads the top instructions and points out “missing domain constraints,” “lack of reasoning steps,” etc.

3.4. Phase 1 Synthesis
	•	SynthesisAgent merges the best mutated instructions plus the critique suggestions into a single “improved prompt.”
	•	Possibly repeats with user or system feedback.
	•	The sub-thread logs each iteration. The user can see:
	•	“Iteration #1 => top instruction scored 0.85. Critique suggests more domain context. Synthesis merges them -> new instruction.”

3.5. Phase 2: Example Generation (if scenario includes examples)
	•	MutateAgent or SynthesisAgent might now generate or refine negative/positive examples.
	•	CritiqueAgent tries them on a new mini-batch or references user feedback.
	•	The final product is a “best instruction + examples” pair.

3.6. Repetitions Until Done
	•	Typically, 2-5 cycles. If the user or Nova sets “max 3 iterations,” once the third iteration completes, the final prompt is declared “best.”

Throughout:
	•	All partial results are ephemeral memory (Qdrant).
	•	The final or best prompt instructions, plus the curated examples, go to semantic memory (Neo4j) if you want them stored stably as a “PromptWizardOutput” node or so.

4. Large Volumes of Messages & Co-Creation
	1.	Hundreds of Iterations
	•	If you do 10+ cycles, each with multiple messages from each sub-agent, you could easily have 100+ messages.
	•	They remain in ephemeral memory. The Slack-like sub-thread shows aggregator updates: “Iteration #2 done. Summarized changes:…”
	•	The user can expand or scroll if they want the raw detail.
	2.	User Interventions
	•	If the user sees sub-agents missing a key constraint, they can type in the sub-thread: “Remember to handle advanced math reasoning steps.”
	•	Next iteration, the CritiqueAgent or SynthesisAgent integrates that input.

5. Handling Domain-Labeled Memory & Emergent Tasks
	1.	Domain
	•	If the prompt is for a personal domain, the sub-agents only see personal domain examples. If it’s professional, they might see a broader dataset or orchard of examples.
	2.	Emergent Tasks
	•	If the CritiqueAgent realizes it needs more advanced knowledge about user’s domain or some numeric data, it spawns a small emergent sub-task: “Fetch domain facts,” or “Check numeric store.”
	•	Nova can unify these sub-tasks in the same sub-thread or spin off a micro-thread, referencing ephemeral memory logs for the final updates.

6. Post-Completion Storage & Re-Use

When the final iteration completes:
	1.	SynthesisAgent posts:

{
  "final_prompt": "...the best instructions...",
  "examples": ["Example1...", "Example2..."]
}


	2.	Nova or the aggregator logic stores it in Neo4j:

MERGE (pw:PromptWizardOutput {id:"prompt_101"})
SET pw.domain = "professional",
    pw.final_prompt = "...",
    pw.examples = [ "..." , "..." ],
    pw.timestamp = timestamp()


	3.	The user or future tasks can reference this “prompt_101” object for code generation or whatever scenario it was built for.

Conclusion

By treating PromptWizard as a team of at least three sub-agents:
	•	MutateAgent → Proposes mutated instructions,
	•	CritiqueAgent → Critiques them,
	•	SynthesisAgent → Merges them and updates instructions/examples,

Nova can spawn these sub-agents in a Slack-like sub-thread. The user or Nova can watch each iterative cycle, merging user feedback and partial scoring, storing ephemeral data in Qdrant, stable results in Neo4j.