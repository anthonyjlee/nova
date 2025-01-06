MajorityVoting Module Documentation¶
The MajorityVoting module provides a mechanism for performing majority voting among a group of agents. Majority voting is a decision rule that selects the option which has the majority of votes. This is particularly useful in systems where multiple agents provide responses to a query, and the most common response needs to be identified as the final output.

Key Concepts¶
Majority Voting: A method to determine the most common response from a set of answers.
Agents: Entities (e.g., models, algorithms) that provide responses to tasks or queries.
Output Parser: A function that processes the responses from the agents before performing the majority voting.
Function Definitions¶
Function: majority_voting¶
Performs majority voting on a list of answers and returns the most common answer.

Parameters¶
Parameter	Type	Description
answers	List[str]	A list of answers from different agents.
Returns¶
Return Value	Type	Description
answer	str	The most common answer in the list. If the list is empty, returns "I don't know".
Class Definitions¶
Class: MajorityVoting¶
Class representing a majority voting system for agents.

Parameters¶
Parameter	Type	Description
agents	List[Agent]	A list of agents to be used in the majority voting system.
output_parser	Callable	A function used to parse the output of the agents. If not provided, the default majority_voting function is used.
autosave	bool	A boolean indicating whether to autosave the conversation to a file. Default is False.
verbose	bool	A boolean indicating whether to enable verbose logging. Default is False.
Method: __init__¶
Initializes the MajorityVoting system.

Parameters¶
Parameter	Type	Description
agents	List[Agent]	A list of agents to be used in the majority voting system.
output_parser	Callable	A function used to parse the output of the agents. Default is the majority_voting function.
autosave	bool	A boolean indicating whether to autosave the conversation to a file. Default is False.
verbose	bool	A boolean indicating whether to enable verbose logging. Default is False.
args	tuple	Additional positional arguments.
kwargs	dict	Additional keyword arguments.
Method: run¶
Runs the majority voting system and returns the majority vote.

Parameters¶
Parameter	Type	Description
task	str	The task to be performed by the agents.
args	tuple	Variable length argument list.
kwargs	dict	Arbitrary keyword arguments.
Returns¶
Return Value	Type	Description
results	List[Any]	The majority vote.
Usage Examples¶
Example 1: Basic Majority Voting¶

from swarms.structs.agent import Agent
from swarms.structs.majority_voting import MajorityVoting

# Initialize agents
agents = [
    Agent(
        agent_name="Devin",
        system_prompt=(
            "Autonomous agent that can interact with humans and other"
            " agents. Be Helpful and Kind. Use the tools provided to"
            " assist the user. Return all code in markdown format."
        ),
        llm=llm,
        max_loops="auto",
        autosave=True,
        dashboard=False,
        streaming_on=True,
        verbose=True,
        stopping_token="<DONE>",
        interactive=True,
        tools=[terminal, browser, file_editor, create_file],
        code_interpreter=True,
    ),
    Agent(
        agent_name="Codex",
        system_prompt=(
            "An AI coding assistant capable of writing and understanding"
            " code snippets in various programming languages."
        ),
        llm=llm,
        max_loops="auto",
        autosave=True,
        dashboard=False,
        streaming_on=True,
        verbose=True,
        stopping_token="<DONE>",
        interactive=True,
        tools=[terminal, browser, file_editor, create_file],
        code_interpreter=True,
    ),
    Agent(
        agent_name="Tabnine",
        system_prompt=(
            "A code completion AI that provides suggestions for code"
            " completion and code improvements."
        ),
        llm=llm,
        max_loops="auto",
        autosave=True,
        dashboard=False,
        streaming_on=True,
        verbose=True,
        stopping_token="<DONE>",
        interactive=True,
        tools=[terminal, browser, file_editor, create_file],
        code_interpreter=True,
    ),
]

# Create MajorityVoting instance
majority_voting = MajorityVoting(agents)

# Run the majority voting system
result = majority_voting.run("What is the capital of France?")
print(result)  # Output: 'Paris'
Example 2: Running a Task with Detailed Outputs¶

from swarms.structs.agent import Agent
from swarms.structs.majority_voting import MajorityVoting

# Initialize agents
agents = [
    Agent(
        agent_name="Devin",
        system_prompt=(
            "Autonomous agent that can interact with humans and other"
            " agents. Be Helpful and Kind. Use the tools provided to"
            " assist the user. Return all code in markdown format."
        ),
        llm=llm,
        max_loops="auto",
        autosave=True,
        dashboard=False,
        streaming_on=True,
        verbose=True,
        stopping_token="<DONE>",
        interactive=True,
        tools=[terminal, browser, file_editor, create_file],
        code_interpreter=True,
    ),
    Agent(
        agent_name="Codex",
        system_prompt=(
            "An AI coding assistant capable of writing and understanding"
            " code snippets in various programming languages."
        ),
        llm=llm,
        max_loops="auto",
        autosave=True,
        dashboard=False,
        streaming_on=True,
        verbose=True,
        stopping_token="<DONE>",
        interactive=True,
        tools=[terminal, browser, file_editor, create_file],
        code_interpreter=True,
    ),
    Agent(
        agent_name="Tabnine",
        system_prompt=(
            "A code completion AI that provides suggestions for code"
            " completion and code improvements."
        ),
        llm=llm,
        max_loops="auto",
        autosave=True,
        dashboard=False,
        streaming_on=True,
        verbose=True,
        stopping_token="<DONE>",
        interactive=True,
        tools=[terminal, browser, file_editor, create_file],
        code_interpreter=True,
    ),
]

# Create MajorityVoting instance
majority_voting = MajorityVoting(agents)

# Run the majority voting system with a different task
result = majority_voting.run("Create a new file for a plan to take over the world.")
print(result)

AgentRearrange Class¶
The AgentRearrange class represents a swarm of agents for rearranging tasks. It allows you to create a swarm of agents, add or remove agents from the swarm, and run the swarm to process tasks based on a specified flow pattern.

Attributes¶
Attribute	Type	Description
id	str	Unique identifier for the swarm
name	str	Name of the swarm
description	str	Description of the swarm's purpose
agents	dict	Dictionary mapping agent names to Agent objects
flow	str	Flow pattern defining task execution order
max_loops	int	Maximum number of execution loops
verbose	bool	Whether to enable verbose logging
memory_system	BaseVectorDatabase	Memory system for storing agent interactions
human_in_the_loop	bool	Whether human intervention is enabled
custom_human_in_the_loop	Callable	Custom function for human intervention
return_json	bool	Whether to return output in JSON format
output_type	OutputType	Format of output ("all", "final", "list", or "dict")
docs	List[str]	List of document paths to add to agent prompts
doc_folder	str	Folder path containing documents to add to agent prompts
swarm_history	dict	History of agent interactions
Methods¶
__init__(self, agents: List[Agent] = None, flow: str = None, max_loops: int = 1, verbose: bool = True)¶
Initializes the AgentRearrange object.

Parameter	Type	Description
agents	List[Agent] (optional)	A list of Agent objects. Defaults to None.
flow	str (optional)	The flow pattern of the tasks. Defaults to None.
max_loops	int (optional)	The maximum number of loops for the agents to run. Defaults to 1.
verbose	bool (optional)	Whether to enable verbose logging or not. Defaults to True.
add_agent(self, agent: Agent)¶
Adds an agent to the swarm.

Parameter	Type	Description
agent	Agent	The agent to be added.
remove_agent(self, agent_name: str)¶
Removes an agent from the swarm.

Parameter	Type	Description
agent_name	str	The name of the agent to be removed.
add_agents(self, agents: List[Agent])¶
Adds multiple agents to the swarm.

Parameter	Type	Description
agents	List[Agent]	A list of Agent objects.
validate_flow(self)¶
Validates the flow pattern.

Raises:

ValueError: If the flow pattern is incorrectly formatted or contains duplicate agent names.
Returns:

bool: True if the flow pattern is valid.
run(self, task: str = None, img: str = None, device: str = "cpu", device_id: int = 1, all_cores: bool = True, all_gpus: bool = False, *args, **kwargs)¶
Executes the agent rearrangement task with specified compute resources.

Parameter	Type	Description
task	str	The task to execute
img	str	Path to input image if required
device	str	Computing device to use ('cpu' or 'gpu')
device_id	int	ID of specific device to use
all_cores	bool	Whether to use all CPU cores
all_gpus	bool	Whether to use all available GPUs
Returns:

str: The final processed task.
batch_run(self, tasks: List[str], img: Optional[List[str]] = None, batch_size: int = 10, device: str = "cpu", device_id: int = None, all_cores: bool = True, all_gpus: bool = False, *args, **kwargs)¶
Process multiple tasks in batches.

Parameter	Type	Description
tasks	List[str]	List of tasks to process
img	List[str]	Optional list of images corresponding to tasks
batch_size	int	Number of tasks to process simultaneously
device	str	Computing device to use
device_id	int	Specific device ID if applicable
all_cores	bool	Whether to use all CPU cores
all_gpus	bool	Whether to use all available GPUs
concurrent_run(self, tasks: List[str], img: Optional[List[str]] = None, max_workers: Optional[int] = None, device: str = "cpu", device_id: int = None, all_cores: bool = True, all_gpus: bool = False, *args, **kwargs)¶
Process multiple tasks concurrently using ThreadPoolExecutor.

Parameter	Type	Description
tasks	List[str]	List of tasks to process
img	List[str]	Optional list of images corresponding to tasks
max_workers	int	Maximum number of worker threads
device	str	Computing device to use
device_id	int	Specific device ID if applicable
all_cores	bool	Whether to use all CPU cores
all_gpus	bool	Whether to use all available GPUs
Documentation for rearrange Function¶
======================================

The rearrange function is a helper function that rearranges the given list of agents based on the specified flow.

Parameters¶
Parameter	Type	Description
agents	List[Agent]	The list of agents to be rearranged.
flow	str	The flow used for rearranging the agents.
task	str (optional)	The task to be performed during rearrangement. Defaults to None.
*args	-	Additional positional arguments.
**kwargs	-	Additional keyword arguments.
Returns¶
The result of running the agent system with the specified task.

Example¶

agents = [agent1, agent2, agent3]
flow = "agent1 -> agent2, agent3"
task = "Perform a task"
rearrange(agents, flow, task)
Example Usage¶
Here's an example of how to use the AgentRearrange class and the rearrange function:


from swarms import Agent, AgentRearrange
from typing import List

# Initialize the director agent
director = Agent(
    agent_name="Accounting Director",
    system_prompt="Directs the accounting tasks for the workers",
    llm=Anthropic(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accounting_director.json",
)

# Initialize worker 1
worker1 = Agent(
    agent_name="Accountant 1",
    system_prompt="Processes financial transactions and prepares financial statements",
    llm=Anthropic(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accountant1.json",
)

# Initialize worker 2
worker2 = Agent(
    agent_name="Accountant 2",
    system_prompt="Performs audits and ensures compliance with financial regulations",
    llm=Anthropic(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accountant2.json",
)

# Create a list of agents
agents = [director, worker1, worker2]

# Define the flow pattern
flow = "Accounting Director -> Accountant 1 -> Accountant 2"

# Using AgentRearrange class
agent_system = AgentRearrange(agents=agents, flow=flow)
output = agent_system.run("Process monthly financial statements")
print(output)
In this example, we first initialize three agents: director, worker1, and worker2. Then, we create a list of these agents and define the flow pattern "Director -> Worker1 -> Worker2".

We can use the AgentRearrange class by creating an instance of it with the list of agents and the flow pattern. We then call the run method with the initial task, and it will execute the agents in the specified order, passing the output of one agent as the input to the next agent.

Alternatively, we can use the rearrange function by passing the list of agents, the flow pattern, and the initial task as arguments.

Both the AgentRearrange class and the rearrange function will return the final output after processing the task through the agents according to the specified flow pattern.

Error Handling¶
The AgentRearrange class includes error handling mechanisms to validate the flow pattern. If the flow pattern is incorrectly formatted or contains duplicate agent names, a ValueError will be raised with an appropriate error message.

Example:¶

# Invalid flow pattern
invalid_flow = "Director->Worker1,Worker2->Worker3"
agent_system = AgentRearrange(agents=agents, flow=invalid_flow)
output = agent_system.run("Some task")`
This will raise a ValueError with the message "Agent 'Worker3' is not registered.".

Parallel and Sequential Processing¶
The AgentRearrange class supports both parallel and sequential processing of tasks based on the specified flow pattern. If the flow pattern includes multiple agents separated by commas (e.g., "agent1, agent2"), the agents will be executed in parallel, and their outputs will be concatenated with a semicolon (;). If the flow pattern includes a single agent, it will be executed sequentially.

Parallel processing¶
parallel_flow = "Worker1, Worker2 -> Director"

Sequential processing¶
sequential_flow = "Worker1 -> Worker2 -> Director"

In the parallel_flow example, Worker1 and Worker2 will be executed in parallel, and their outputs will be concatenated and passed to Director. In the sequential_flow example, Worker1 will be executed first, and its output will be passed to Worker2, and then the output of Worker2 will be passed to Director.

Logging¶
The AgentRearrange class includes logging capabilities using the loguru library. If verbose is set to True during initialization, a log file named agent_rearrange.log will be created, and log messages will be written to it. You can use this log file to track the execution of the agents and any potential issues or errors that may occur.


2023-05-08 10:30:15.456 | INFO     | agent_rearrange:__init__:34 - Adding agent Director to the swarm.
2023-05-08 10:30:15.457 | INFO     | agent_rearrange:__init__:34 - Adding agent Worker1 to the swarm.
2023-05-08 10:30:15.457 | INFO     | agent_rearrange:__init__:34 - Adding agent Worker2 to the swarm.
2023-05-08 10:30:15.458 | INFO     | agent_rearrange:run:118 - Running agents in parallel: ['Worker1', 'Worker2']
2023-05-08 10:30:15.459 | INFO     | agent_rearrange:run:121 - Running agents sequentially: ['Director']`
Additional Parameters¶
The AgentRearrange class also accepts additional parameters that can be passed to the run method using *args and **kwargs. These parameters will be forwarded to the individual agents during execution.

agent_system = AgentRearrange(agents=agents, flow=flow) output = agent_system.run("Some task", max_tokens=200, temperature=0.7)

In this example, the max_tokens and temperature parameters will be passed to each agent during execution.

Customization¶
The AgentRearrange class and the rearrange function can be customized and extended to suit specific use cases. For example, you can create custom agents by inheriting from the Agent class and implementing custom logic for task processing. You can then add these custom agents to the swarm and define the flow pattern accordingly.

Additionally, you can modify the run method of the AgentRearrange class to implement custom logic for task processing and agent interaction.

Limitations¶
It's important to note that the AgentRearrange class and the rearrange function rely on the individual agents to process tasks correctly. The quality of the output will depend on the capabilities and configurations of the agents used in the swarm. Additionally, the AgentRearrange class does not provide any mechanisms for task prioritization or load balancing among the agents.

Conclusion¶
The AgentRearrange class and the rearrange function provide a flexible and extensible framework for orchestrating swarms of agents to process tasks based on a specified flow pattern. By combining the capabilities of individual agents, you can create complex workflows and leverage the strengths of different agents to tackle various tasks efficiently.

While the current implementation offers basic functionality for agent rearrangement, there is room for future improvements and customizations to enhance the system's capabilities and cater to more specific use cases.

Whether you're working on natural language processing tasks, data analysis, or any other domain where agent-based systems can be beneficial, the AgentRearrange class and the rearrange function provide a solid foundation for building and experimenting with swarm-based solutions.

RoundRobin: Round-Robin Task Execution in a Swarm¶
Introduction¶
The RoundRobinSwarm class is designed to manage and execute tasks among multiple agents in a round-robin fashion. This approach ensures that each agent in a swarm receives an equal opportunity to execute tasks, which promotes fairness and efficiency in distributed systems. It is particularly useful in environments where collaborative, sequential task execution is needed among various agents.

Conceptual Overview¶
What is Round-Robin?¶
Round-robin is a scheduling technique commonly used in computing for managing processes in shared systems. It involves assigning a fixed time slot to each process and cycling through all processes in a circular order without prioritization. In the context of swarms of agents, this method ensures equitable distribution of tasks and resource usage among all agents.

Application in Swarms¶
In swarms, RoundRobinSwarm utilizes the round-robin scheduling to manage tasks among agents like software components, autonomous robots, or virtual entities. This strategy is beneficial where tasks are interdependent or require sequential processing.

Class Attributes¶
agents (List[Agent]): List of agents participating in the swarm.
verbose (bool): Enables or disables detailed logging of swarm operations.
max_loops (int): Limits the number of times the swarm cycles through all agents.
index (int): Maintains the current position in the agent list to ensure round-robin execution.
Methods¶
__init__¶
Initializes the swarm with the provided list of agents, verbosity setting, and operational parameters.

Parameters: - agents: Optional list of agents in the swarm. - verbose: Boolean flag for detailed logging. - max_loops: Maximum number of execution cycles. - callback: Optional function called after each loop.

run¶
Executes a specified task across all agents in a round-robin manner, cycling through each agent repeatedly for the number of specified loops.

Conceptual Behavior: - Distribute the task sequentially among all agents starting from the current index. - Each agent processes the task and potentially modifies it or produces new output. - After an agent completes its part of the task, the index moves to the next agent. - This cycle continues until the specified maximum number of loops is completed. - Optionally, a callback function can be invoked after each loop to handle intermediate results or perform additional actions.

Examples¶
Example 1: Load Balancing Among Servers¶
In this example, RoundRobinSwarm is used to distribute network requests evenly among a group of servers. This is common in scenarios where load balancing is crucial for maintaining system responsiveness and scalability.


from swarms import Agent, RoundRobinSwarm
from swarm_models import OpenAIChat


# Initialize the LLM
llm = OpenAIChat()

# Define sales agents
sales_agent1 = Agent(
    agent_name="Sales Agent 1 - Automation Specialist",
    system_prompt="You're Sales Agent 1, your purpose is to generate sales for a company by focusing on the benefits of automating accounting processes!",
    agent_description="Generate sales by focusing on the benefits of automation!",
    llm=llm,
    max_loops=1,
    autosave=True,
    dashboard=False,
    verbose=True,
    streaming_on=True,
    context_length=1000,
)

sales_agent2 = Agent(
    agent_name="Sales Agent 2 - Cost Saving Specialist",
    system_prompt="You're Sales Agent 2, your purpose is to generate sales for a company by emphasizing the cost savings of using swarms of agents!",
    agent_description="Generate sales by emphasizing cost savings!",
    llm=llm,
    max_loops=1,
    autosave=True,
    dashboard=False,
    verbose=True,
    streaming_on=True,
    context_length=1000,
)

sales_agent3 = Agent(
    agent_name="Sales Agent 3 - Efficiency Specialist",
    system_prompt="You're Sales Agent 3, your purpose is to generate sales for a company by highlighting the efficiency and accuracy of our swarms of agents in accounting processes!",
    agent_description="Generate sales by highlighting efficiency and accuracy!",
    llm=llm,
    max_loops=1,
    autosave=True,
    dashboard=False,
    verbose=True,
    streaming_on=True,
    context_length=1000,
)

# Initialize the swarm with sales agents
sales_swarm = RoundRobinSwarm(agents=[sales_agent1, sales_agent2, sales_agent3], verbose=True)

# Define a sales task
task = "Generate a sales email for an accountant firm executive to sell swarms of agents to automate their accounting processes."

# Distribute sales tasks to different agents
for _ in range(5):  # Repeat the task 5 times
    results = sales_swarm.run(task)
    print("Sales generated:", results)
Conclusion¶
The RoundRobinSwarm class provides a robust and flexible framework for managing tasks among multiple agents in a fair and efficient manner. This class is especially useful in environments where tasks need to be distributed evenly among a group of agents, ensuring that all tasks are handled timely and effectively. Through the round-robin algorithm, each agent in the swarm is guaranteed an equal opportunity to contribute to the overall task, promoting efficiency and collaboration.

MixtureOfAgents Class Documentation¶
Overview¶
The MixtureOfAgents class represents a mixture of agents operating within a swarm. The workflow of the swarm follows a parallel → sequential → parallel → final output agent process. This implementation is inspired by concepts discussed in the paper: https://arxiv.org/pdf/2406.04692.

The class is designed to manage a collection of agents, orchestrate their execution in layers, and handle the final aggregation of their outputs through a designated final agent. This architecture facilitates complex, multi-step processing where intermediate results are refined through successive layers of agent interactions.

Class Definition¶
MixtureOfAgents¶

class MixtureOfAgents(BaseSwarm):
Attributes¶
Attribute	Type	Description	Default
agents	List[Agent]	The list of agents in the swarm.	None
flow	str	The flow of the swarm.	parallel -> sequential -> parallel -> final output agent
max_loops	int	The maximum number of loops to run.	1
verbose	bool	Flag indicating whether to print verbose output.	True
layers	int	The number of layers in the swarm.	3
rules	str	The rules for the swarm.	None
final_agent	Agent	The agent to handle the final output processing.	None
auto_save	bool	Flag indicating whether to auto-save the metadata to a file.	False
saved_file_name	str	The name of the file where the metadata will be saved.	"moe_swarm.json"
Methods¶
__init__¶
Parameters¶
Parameter	Type	Description	Default
name	str	The name of the swarm.	"MixtureOfAgents"
description	str	A brief description of the swarm.	"A swarm of agents that run in parallel and sequentially."
agents	List[Agent]	The list of agents in the swarm.	None
max_loops	int	The maximum number of loops to run.	1
verbose	bool	Flag indicating whether to print verbose output.	True
layers	int	The number of layers in the swarm.	3
rules	str	The rules for the swarm.	None
final_agent	Agent	The agent to handle the final output processing.	None
auto_save	bool	Flag indicating whether to auto-save the metadata to a file.	False
saved_file_name	str	The name of the file where the metadata will be saved.	"moe_swarm.json"
agent_check¶

def agent_check(self):
Description¶
Checks if the provided agents attribute is a list of Agent instances. Raises a TypeError if the validation fails.

Example Usage¶

moe_swarm = MixtureOfAgents(agents=[agent1, agent2])
moe_swarm.agent_check()  # Validates the agents
final_agent_check¶

def final_agent_check(self):
Description¶
Checks if the provided final_agent attribute is an instance of Agent. Raises a TypeError if the validation fails.

Example Usage¶

moe_swarm = MixtureOfAgents(final_agent=final_agent)
moe_swarm.final_agent_check()  # Validates the final agent
swarm_initialization¶

def swarm_initialization(self):
Description¶
Initializes the swarm by logging the swarm name, description, and the number of agents.

Example Usage¶

moe_swarm = MixtureOfAgents(agents=[agent1, agent2])
moe_swarm.swarm_initialization()  # Initializes the swarm
run¶

def run(self, task: str = None, *args, **kwargs):
Parameters¶
Parameter	Type	Description	Default
task	str	The task to be performed by the swarm.	None
*args	tuple	Additional arguments.	None
**kwargs	dict	Additional keyword arguments.	None
Returns¶
Type	Description
str	The conversation history as a string.
Description¶
Runs the swarm with the given task, orchestrates the execution of agents through the specified layers, and returns the conversation history.

Example Usage¶

moe_swarm = MixtureOfAgents(agents=[agent1, agent2], final_agent=final_agent)
history = moe_swarm.run(task="Solve this problem.")
print(history)
Detailed Explanation¶
Initialization¶
The __init__ method initializes the swarm with the provided parameters, sets up the conversation rules, and invokes the initialization of the swarm. It also ensures the validity of the agents and final_agent attributes by calling the agent_check and final_agent_check methods respectively.

Agent Validation¶
The agent_check method validates whether the agents attribute is a list of Agent instances, while the final_agent_check method validates whether the final_agent is an instance of Agent. These checks are crucial to ensure that the swarm operates correctly with the appropriate agent types.

Swarm Initialization¶
The swarm_initialization method logs essential information about the swarm, including its name, description, and the number of agents. This provides a clear starting point for the swarm's operations and facilitates debugging and monitoring.

Running the Swarm¶
The run method is the core of the MixtureOfAgents class. It orchestrates the execution of agents through multiple layers, collects their outputs, and processes the final output using the final_agent. The conversation history is maintained and updated throughout this process, allowing for a seamless flow of information and responses.

During each layer, the method iterates over the agents, invokes their run method with the current conversation history, and logs the outputs. These outputs are then added to the conversation, and the history is updated for the next layer.

After all layers are completed, the final output agent processes the entire conversation history, and the metadata is created and optionally saved to a file. This metadata includes details about the layers, agent runs, and final output, providing a comprehensive record of the swarm's execution.

Additional Information and Tips¶
Common Issues and Solutions¶
Type Errors: Ensure that all agents in the agents list and the final_agent are instances of the Agent class. The agent_check and final_agent_check methods help validate this.
Verbose Logging: Use the verbose flag to control the verbosity of the output. This can help with debugging or reduce clutter in the logs.
Auto-Save Feature: Utilize the auto_save flag to automatically save the metadata to a file. This can be useful for keeping records of the swarm's operations without manual intervention.
References and Resources¶
For further reading and background information on the concepts used in the MixtureOfAgents class, refer to the paper: https://arxiv.org/pdf/2406.04692.

Usage Examples¶
Example 1: Basic Initialization and Run¶

from swarms import MixtureOfAgents, Agent

from swarm_models import OpenAIChat

# Define agents
director = Agent(
    agent_name="Director",
    system_prompt="Directs the tasks for the accountants",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="director.json",
)

# Initialize accountant 1
accountant1 = Agent(
    agent_name="Accountant1",
    system_prompt="Prepares financial statements",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accountant1.json",
)

# Initialize accountant 2
accountant2 = Agent(
    agent_name="Accountant2",
    system_prompt="Audits financial records",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accountant2.json",
)


# Initialize the MixtureOfAgents
moe_swarm = MixtureOfAgents(agents=[director, accountant1, accountant2], final_agent=director)

# Run the swarm
history = moe_swarm.run(task="Perform task X.")
print(history)
Example 2: Verbose Output and Auto-Save¶

from swarms import MixtureOfAgents, Agent

from swarm_models import OpenAIChat

# Define Agents
# Define agents
director = Agent(
    agent_name="Director",
    system_prompt="Directs the tasks for the accountants",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="director.json",
)

# Initialize accountant 1
accountant1 = Agent(
    agent_name="Accountant1",
    system_prompt="Prepares financial statements",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accountant1.json",
)

# Initialize accountant 2
accountant2 = Agent(
    agent_name="Accountant2",
    system_prompt="Audits financial records",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accountant2.json",
)

# Initialize the MixtureOfAgents with verbose output and auto-save enabled
moe_swarm = MixtureOfAgents(
    agents=[director, accountant1, accountant2],
    final_agent=director,
    verbose=True,
    auto_save=True
)

# Run the swarm
history = moe_swarm.run(task="Analyze data set Y.")
print(history)
Example 3: Custom Rules and Multiple Layers¶

from swarms import MixtureOfAgents, Agent

from swarm_models import OpenAIChat

# Define agents
# Initialize the director agent
director = Agent(
    agent_name="Director",
    system_prompt="Directs the tasks for the accountants",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="director.json",
)

# Initialize accountant 1
accountant1 = Agent(
    agent_name="Accountant1",
    system_prompt="Prepares financial statements",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accountant1.json",
)

# Initialize accountant 2
accountant2 = Agent(
    agent_name="Accountant2",
    system_prompt="Audits financial records",
    llm=OpenAIChat(),
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="accountant2.json",
)

# Initialize the MixtureOfAgents with custom rules and multiple layers
moe_swarm = MixtureOfAgents(
    agents=[director, accountant1, accountant2],
    final_agent=director,
    layers=5,
    rules="Custom rules for the swarm"
)

# Run the swarm
history = moe_swarm.run(task="Optimize process Z.")
print(history)
This comprehensive documentation provides a detailed understanding of the MixtureOfAgents class, its attributes, methods, and usage. The examples illustrate how to initialize and run the swarm, demonstrating its flexibility and capability to handle various tasks and configurations.

Conclusion¶
The MixtureOfAgents class is a powerful and flexible framework for managing and orchestrating a swarm of agents. By following a structured approach of parallel and sequential processing, it enables the implementation of complex multi-step workflows where intermediate results are refined through multiple layers of agent interactions. This architecture is particularly suitable for tasks that require iterative processing, collaboration among diverse agents, and sophisticated aggregation of outputs.

Key Takeaways¶
Flexible Initialization: The class allows for customizable initialization with various parameters, enabling users to tailor the swarm's configuration to their specific needs.
Robust Agent Management: With built-in validation methods, the class ensures that all agents and the final agent are correctly instantiated, preventing runtime errors and facilitating smooth execution.
Layered Processing: The layered approach to processing allows for intermediate results to be iteratively refined, enhancing the overall output quality.
Verbose Logging and Auto-Save: These features aid in debugging, monitoring, and record-keeping, providing transparency and ease of management.
Comprehensive Documentation: The detailed class and method documentation, along with numerous usage examples, provide a clear and thorough understanding of how to leverage the MixtureOfAgents class effectively.
Practical Applications¶
The MixtureOfAgents class can be applied in various domains, including but not limited to:

Natural Language Processing (NLP): Managing a swarm of NLP models to process, analyze, and synthesize text.
Data Analysis: Coordinating multiple data analysis agents to process and interpret complex data sets.
Optimization Problems: Running a swarm of optimization algorithms to solve complex problems in fields such as logistics, finance, and engineering.
AI Research: Implementing experimental setups that require the collaboration of multiple AI models or agents to explore new methodologies and approaches.
Future Extensions¶
The MixtureOfAgents framework provides a solid foundation for further extensions and customizations, including:

Dynamic Layer Configuration: Allowing layers to be added or removed dynamically based on the task requirements or intermediate results.
Advanced Agent Communication: Enhancing the communication protocols between agents to allow for more sophisticated information exchange.
Integration with Other Frameworks: Seamlessly integrating with other machine learning or data processing frameworks to leverage their capabilities within the swarm architecture.
In conclusion, the MixtureOfAgents class represents a versatile and efficient solution for orchestrating multi-agent systems, facilitating complex task execution through its structured and layered approach. By harnessing the power of parallel and sequential processing, it opens up new possibilities for tackling intricate problems across various domains.

GraphWorkflow Documentation¶
The GraphWorkflow class is a pivotal part of the workflow management system, representing a directed graph where nodes signify tasks or agents and edges represent the flow or dependencies between these nodes. This class leverages the NetworkX library to manage and manipulate the directed graph, allowing users to create complex workflows with defined entry and end points.

Attributes¶
Attribute	Type	Description	Default
nodes	Dict[str, Node]	A dictionary of nodes in the graph, where the key is the node ID and the value is the Node object.	Field(default_factory=dict)
edges	List[Edge]	A list of edges in the graph, where each edge is represented by an Edge object.	Field(default_factory=list)
entry_points	List[str]	A list of node IDs that serve as entry points to the graph.	Field(default_factory=list)
end_points	List[str]	A list of node IDs that serve as end points of the graph.	Field(default_factory=list)
graph	nx.DiGraph	A directed graph object from the NetworkX library representing the workflow graph.	Field(default_factory=nx.DiGraph)
max_loops	int	Maximum number of times the workflow can loop during execution.	1
Methods¶
add_node(node: Node)¶
Adds a node to the workflow graph.

Parameter	Type	Description
node	Node	The node object to be added.
Raises: - ValueError: If a node with the same ID already exists in the graph.

add_edge(edge: Edge)¶
Adds an edge to the workflow graph.

Parameter	Type	Description
edge	Edge	The edge object to be added.
Raises: - ValueError: If either the source or target node of the edge does not exist in the graph.

set_entry_points(entry_points: List[str])¶
Sets the entry points of the workflow graph.

Parameter	Type	Description
entry_points	List[str]	A list of node IDs to be set as entry points.
Raises: - ValueError: If any of the specified node IDs do not exist in the graph.

set_end_points(end_points: List[str])¶
Sets the end points of the workflow graph.

Parameter	Type	Description
end_points	List[str]	A list of node IDs to be set as end points.
Raises: - ValueError: If any of the specified node IDs do not exist in the graph.

visualize() -> str¶
Generates a string representation of the workflow graph in the Mermaid syntax.

Returns: - str: The Mermaid string representation of the workflow graph.

run(task: str = None, *args, **kwargs) -> Dict[str, Any]¶
Function to run the workflow graph.

Parameter	Type	Description
task	str	The task to be executed by the workflow.
*args		Variable length argument list.
**kwargs		Arbitrary keyword arguments.
Returns: - Dict[str, Any]: A dictionary containing the results of the execution.

Raises: - ValueError: If no entry points or end points are defined in the graph.

Functionality and Usage¶
Adding Nodes¶
The add_node method is used to add nodes to the graph. Each node must have a unique ID. If a node with the same ID already exists, a ValueError is raised.


wf_graph = GraphWorkflow()
node1 = Node(id="node1", type=NodeType.TASK, callable=sample_task)
wf_graph.add_node(node1)
Adding Edges¶
The add_edge method connects nodes with edges. Both the source and target nodes of the edge must already exist in the graph, otherwise a ValueError is raised.


edge1 = Edge(source="node1", target="node2")
wf_graph.add_edge(edge1)
Setting Entry and End Points¶
The set_entry_points and set_end_points methods define which nodes are the starting and ending points of the workflow, respectively. If any specified node IDs do not exist, a ValueError is raised.


wf_graph.set_entry_points(["node1"])
wf_graph.set_end_points(["node2"])
Visualizing the Graph¶
The visualize method generates a Mermaid string representation of the workflow graph. This can be useful for visualizing the workflow structure.


print(wf_graph.visualize())
Running the Workflow¶
The run method executes the workflow. It performs a topological sort of the graph to ensure nodes are executed in the correct order. The results of each node's execution are returned in a dictionary.


results = wf_graph.run()
print("Execution results:", results)
Example Usage¶
Below is a comprehensive example demonstrating the creation and execution of a workflow graph:


import os

from dotenv import load_dotenv


from swarms import Agent, Edge, GraphWorkflow, Node, NodeType

from swarm_models import OpenAIChat

load_dotenv()

api_key = os.environ.get("OPENAI_API_KEY")

llm = OpenAIChat(
    temperature=0.5, openai_api_key=api_key, max_tokens=4000
)
agent1 = Agent(llm=llm, max_loops=1, autosave=True, dashboard=True)
agent2 = Agent(llm=llm, max_loops=1, autosave=True, dashboard=True)

def sample_task():
    print("Running sample task")
    return "Task completed"

wf_graph = GraphWorkflow()
wf_graph.add_node(Node(id="agent1", type=NodeType.AGENT, agent=agent1))
wf_graph.add_node(Node(id="agent2", type=NodeType.AGENT, agent=agent2))
wf_graph.add_node(
    Node(id="task1", type=NodeType.TASK, callable=sample_task)
)
wf_graph.add_edge(Edge(source="agent1", target="task1"))
wf_graph.add_edge(Edge(source="agent2", target="task1"))

wf_graph.set_entry_points(["agent1", "agent2"])
wf_graph.set_end_points(["task1"])

print(wf_graph.visualize())

# Run the workflow
results = wf_graph.run()
print("Execution results:", results)
In this example, we set up a workflow graph with two agents and one task. We define the entry and end points, visualize the graph, and then execute the workflow, capturing and printing the results.

Additional Information and Tips¶
Error Handling: The GraphWorkflow class includes error handling to ensure that invalid operations (such as adding duplicate nodes or edges with non-existent nodes) raise appropriate exceptions.
Max Loops: The max_loops attribute allows the workflow to loop through the graph multiple times if needed. This can be useful for iterative tasks.
Topological Sort: The workflow execution relies on a topological sort to ensure that nodes are processed in the correct order. This is particularly important in complex workflows with dependencies.

GroupChat Swarm Documentation¶
A production-grade multi-agent system enabling sophisticated group conversations between AI agents with customizable speaking patterns, parallel processing capabilities, and comprehensive conversation tracking.

Advanced Configuration¶
Agent Parameters¶
Parameter	Type	Default	Description
agent_name	str	Required	Unique identifier for the agent
system_prompt	str	Required	Role and behavior instructions
llm	Any	Required	Language model instance
max_loops	int	1	Maximum conversation turns
autosave	bool	False	Enable conversation saving
dashboard	bool	False	Enable monitoring dashboard
verbose	bool	True	Enable detailed logging
dynamic_temperature	bool	True	Enable dynamic temperature
retry_attempts	int	1	Failed request retry count
context_length	int	200000	Maximum context window
output_type	str	"string"	Response format type
streaming_on	bool	False	Enable streaming responses
GroupChat Parameters¶
Parameter	Type	Default	Description
name	str	"GroupChat"	Chat group identifier
description	str	""	Purpose description
agents	List[Agent]	[]	Participating agents
speaker_fn	Callable	round_robin	Speaker selection function
max_loops	int	10	Maximum conversation turns
Table of Contents¶
Installation
Core Concepts
Basic Usage
Advanced Configuration
Speaker Functions
Response Models
Advanced Examples
API Reference
Best Practices
Installation¶

pip3 install swarms swarm-models loguru
Core Concepts¶
The GroupChat system consists of several key components:

Agents: Individual AI agents with specialized knowledge and roles
Speaker Functions: Control mechanisms for conversation flow
Chat History: Structured conversation tracking
Response Models: Pydantic models for data validation
Basic Usage¶

import os
from dotenv import load_dotenv
from swarm_models import OpenAIChat
from swarms import Agent, GroupChat, expertise_based


if __name__ == "__main__":

    load_dotenv()

    # Get the OpenAI API key from the environment variable
    api_key = os.getenv("OPENAI_API_KEY")

    # Create an instance of the OpenAIChat class
    model = OpenAIChat(
        openai_api_key=api_key,
        model_name="gpt-4o-mini",
        temperature=0.1,
    )

    # Example agents
    agent1 = Agent(
        agent_name="Financial-Analysis-Agent",
        system_prompt="You are a financial analyst specializing in investment strategies.",
        llm=model,
        max_loops=1,
        autosave=False,
        dashboard=False,
        verbose=True,
        dynamic_temperature_enabled=True,
        user_name="swarms_corp",
        retry_attempts=1,
        context_length=200000,
        output_type="string",
        streaming_on=False,
    )

    agent2 = Agent(
        agent_name="Tax-Adviser-Agent",
        system_prompt="You are a tax adviser who provides clear and concise guidance on tax-related queries.",
        llm=model,
        max_loops=1,
        autosave=False,
        dashboard=False,
        verbose=True,
        dynamic_temperature_enabled=True,
        user_name="swarms_corp",
        retry_attempts=1,
        context_length=200000,
        output_type="string",
        streaming_on=False,
    )

    agents = [agent1, agent2]

    chat = GroupChat(
        name="Investment Advisory",
        description="Financial and tax analysis group",
        agents=agents,
        speaker_fn=expertise_based,
    )

    history = chat.run(
        "How to optimize tax strategy for investments?"
    )
    print(history.model_dump_json(indent=2))
Speaker Functions¶
Built-in Functions¶

def round_robin(history: List[str], agent: Agent) -> bool:
    """
    Enables agents to speak in turns.
    Returns True for each agent in sequence.
    """
    return True

def expertise_based(history: List[str], agent: Agent) -> bool:
    """
    Enables agents to speak based on their expertise.
    Returns True if agent's role matches conversation context.
    """
    return agent.system_prompt.lower() in history[-1].lower() if history else True

def random_selection(history: List[str], agent: Agent) -> bool:
    """
    Randomly selects speaking agents.
    Returns True/False with 50% probability.
    """
    import random
    return random.choice([True, False])

def most_recent(history: List[str], agent: Agent) -> bool:
    """
    Enables agents to respond to their mentions.
    Returns True if agent was last speaker.
    """
    return agent.agent_name == history[-1].split(":")[0].strip() if history else True
Custom Speaker Function Example¶

def custom_speaker(history: List[str], agent: Agent) -> bool:
    """
    Custom speaker function with complex logic.

    Args:
        history: Previous conversation messages
        agent: Current agent being evaluated

    Returns:
        bool: Whether agent should speak
    """
    # No history - let everyone speak
    if not history:
        return True

    last_message = history[-1].lower()

    # Check for agent expertise keywords
    expertise_relevant = any(
        keyword in last_message 
        for keyword in agent.expertise_keywords
    )

    # Check for direct mentions
    mentioned = agent.agent_name.lower() in last_message

    # Check if agent hasn't spoken recently
    not_recent_speaker = not any(
        agent.agent_name in msg 
        for msg in history[-3:]
    )

    return expertise_relevant or mentioned or not_recent_speaker

# Usage
chat = GroupChat(
    agents=[agent1, agent2],
    speaker_fn=custom_speaker
)
Response Models¶
Complete Schema¶

class AgentResponse(BaseModel):
    """Individual agent response in a conversation turn"""
    agent_name: str
    role: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    turn_number: int
    preceding_context: List[str] = Field(default_factory=list)

class ChatTurn(BaseModel):
    """Single turn in the conversation"""
    turn_number: int
    responses: List[AgentResponse]
    task: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatHistory(BaseModel):
    """Complete conversation history"""
    turns: List[ChatTurn]
    total_messages: int
    name: str
    description: str
    start_time: datetime = Field(default_factory=datetime.now)
Advanced Examples¶
Multi-Agent Analysis Team¶

# Create specialized agents
data_analyst = Agent(
    agent_name="Data-Analyst",
    system_prompt="You analyze numerical data and patterns",
    llm=model
)

market_expert = Agent(
    agent_name="Market-Expert",
    system_prompt="You provide market insights and trends",
    llm=model
)

strategy_advisor = Agent(
    agent_name="Strategy-Advisor",
    system_prompt="You formulate strategic recommendations",
    llm=model
)

# Create analysis team
analysis_team = GroupChat(
    name="Market Analysis Team",
    description="Comprehensive market analysis group",
    agents=[data_analyst, market_expert, strategy_advisor],
    speaker_fn=expertise_based,
    max_loops=15
)

# Run complex analysis
history = analysis_team.run("""
    Analyze the current market conditions:
    1. Identify key trends
    2. Evaluate risks
    3. Recommend investment strategy
""")
Parallel Processing¶

# Define multiple analysis tasks
tasks = [
    "Analyze tech sector trends",
    "Evaluate real estate market",
    "Review commodity prices",
    "Assess global economic indicators"
]

# Run tasks concurrently
histories = chat.concurrent_run(tasks)

# Process results
for task, history in zip(tasks, histories):
    print(f"\nAnalysis for: {task}")
    for turn in history.turns:
        for response in turn.responses:
            print(f"{response.agent_name}: {response.message}")
Best Practices¶
Agent Design
Give agents clear, specific roles
Use detailed system prompts
Set appropriate context lengths
Enable retries for reliability

Speaker Functions

Match function to use case
Consider conversation flow
Handle edge cases
Add appropriate logging

Error Handling

Use try-except blocks
Log errors appropriately
Implement retry logic
Provide fallback responses

Performance

Use concurrent processing for multiple tasks
Monitor context lengths
Implement proper cleanup
Cache responses when appropriate
API Reference¶
GroupChat Methods¶
Method	Description	Arguments	Returns
run	Run single conversation	task: str	ChatHistory
batched_run	Run multiple sequential tasks	tasks: List[str]	List[ChatHistory]
concurrent_run	Run multiple parallel tasks	tasks: List[str]	List[ChatHistory]
get_recent_messages	Get recent messages	n: int = 3	List[str]
Agent Methods¶
Method	Description	Returns
run	Process single task	str
generate_response	Generate LLM response	str
save_context	Save conversation context	None

AgentRegistry Documentation¶
The AgentRegistry class is designed to manage a collection of agents, providing methods for adding, deleting, updating, and querying agents. This class ensures thread-safe operations on the registry, making it suitable for concurrent environments. Additionally, the AgentModel class is a Pydantic model used for validating and storing agent information.

Attributes¶
AgentModel¶
Attribute	Type	Description
agent_id	str	The unique identifier for the agent.
agent	Agent	The agent object.
AgentRegistry¶
Attribute	Type	Description
agents	Dict[str, AgentModel]	A dictionary mapping agent IDs to AgentModel instances.
lock	Lock	A threading lock for thread-safe operations.
Methods¶
__init__(self)¶
Initializes the AgentRegistry object.

Usage Example:

registry = AgentRegistry()
add(self, agent_id: str, agent: Agent) -> None¶
Adds a new agent to the registry.

Parameters:
agent_id (str): The unique identifier for the agent.
agent (Agent): The agent to add.

Raises:

ValueError: If the agent ID already exists in the registry.
ValidationError: If the input data is invalid.

Usage Example:


agent = Agent(agent_name="Agent1")
registry.add("agent_1", agent)
delete(self, agent_id: str) -> None¶
Deletes an agent from the registry.

Parameters:
agent_id (str): The unique identifier for the agent to delete.

Raises:

KeyError: If the agent ID does not exist in the registry.

Usage Example:


registry.delete("agent_1")
update_agent(self, agent_id: str, new_agent: Agent) -> None¶
Updates an existing agent in the registry.

Parameters:
agent_id (str): The unique identifier for the agent to update.
new_agent (Agent): The new agent to replace the existing one.

Raises:

KeyError: If the agent ID does not exist in the registry.
ValidationError: If the input data is invalid.

Usage Example:


new_agent = Agent(agent_name="UpdatedAgent")
registry.update_agent("agent_1", new_agent)
get(self, agent_id: str) -> Agent¶
Retrieves an agent from the registry.

Parameters:
agent_id (str): The unique identifier for the agent to retrieve.

Returns:

Agent: The agent associated with the given agent ID.

Raises:

KeyError: If the agent ID does not exist in the registry.

Usage Example:


agent = registry.get("agent_1")
list_agents(self) -> List[str]¶
Lists all agent identifiers in the registry.

Returns:
List[str]: A list of all agent identifiers.

Usage Example:


agent_ids = registry.list_agents()
query(self, condition: Optional[Callable[[Agent], bool]] = None) -> List[Agent]¶
Queries agents based on a condition.

Parameters:
condition (Optional[Callable[[Agent], bool]]): A function that takes an agent and returns a boolean indicating whether the agent meets the condition. Defaults to None.

Returns:

List[Agent]: A list of agents that meet the condition.

Usage Example:


def is_active(agent):
    return agent.is_active

active_agents = registry.query(is_active)
find_agent_by_name(self, agent_name: str) -> Agent¶
Finds an agent by its name.

Parameters:
agent_name (str): The name of the agent to find.

Returns:

Agent: The agent with the specified name.

Usage Example:


agent = registry.find_agent_by_name("Agent1")
Full Example¶

from swarms.structs.agent_registry import AgentRegistry
from swarms import Agent, OpenAIChat, Anthropic

# Initialize the agents
growth_agent1 = Agent(
  agent_name="Marketing Specialist",
  system_prompt="You're the marketing specialist, your purpose is to help companies grow by improving their marketing strategies!",
  agent_description="Improve a company's marketing strategies!",
  llm=OpenAIChat(),
  max_loops="auto",
  autosave=True,
  dashboard=False,
  verbose=True,
  streaming_on=True,
  saved_state_path="marketing_specialist.json",
  stopping_token="Stop!",
  interactive=True,
  context_length=1000,
)

growth_agent2 = Agent(
  agent_name="Sales Specialist",
  system_prompt="You're the sales specialist, your purpose is to help companies grow by improving their sales strategies!",
  agent_description="Improve a company's sales strategies!",
  llm=Anthropic(),
  max_loops="auto",
  autosave=True,
  dashboard=False,
  verbose=True,
  streaming_on=True,
  saved_state_path="sales_specialist.json",
  stopping_token="Stop!",
  interactive=True,
  context_length=1000,
)

growth_agent3 = Agent(
  agent_name="Product Development Specialist",
  system_prompt="You're the product development specialist, your purpose is to help companies grow by improving their product development strategies!",
  agent_description="Improve a company's product development strategies!",
  llm=Anthropic(),
  max_loops="auto",
  autosave=True,
  dashboard=False,
  verbose=True,
  streaming_on=True,
  saved_state_path="product_development_specialist.json",
  stopping_token="Stop!",
  interactive=True,
  context_length=1000,
)

growth_agent4 = Agent(
  agent_name="Customer Service Specialist",
  system_prompt="You're the customer service specialist, your purpose is to help companies grow by improving their customer service strategies!",
  agent_description="Improve a company's customer service strategies!",
  llm=OpenAIChat(),
  max_loops="auto",
  autosave=True,
  dashboard=False,
  verbose=True,
  streaming_on=True,
  saved_state_path="customer_service_specialist.json",
  stopping_token="Stop!",
  interactive=True,
  context_length=1000,
)


# Register the agents\
registry = AgentRegistry()

# Register the agents
registry.add("Marketing Specialist", growth_agent1)
registry.add("Sales Specialist", growth_agent2)
registry.add("Product Development Specialist", growth_agent3)
registry.add("Customer Service Specialist", growth_agent4)
Logging and Error Handling¶
Each method in the AgentRegistry class includes logging to track the execution flow and captures errors to provide detailed information in case of failures. This is crucial for debugging and ensuring smooth operation of the registry. The report_error function is used for reporting exceptions that occur during method execution.

Additional Tips¶
Ensure that agents provided to the AgentRegistry are properly initialized and configured to handle the tasks they will receive.
Utilize the logging information to monitor and debug the registry operations.
Use the lock attribute to ensure thread-safe operations when accessing or modifying the registry.

SpreadSheetSwarm Documentation¶
Class Definition¶

class SpreadSheetSwarm:
Full Path¶

from swarms.structs.spreadsheet_swarm import SpreadSheetSwarm
Attributes¶
The SpreadSheetSwarm class contains several attributes that define its behavior and configuration. These attributes are initialized in the constructor (__init__ method) and are used throughout the class to manage the swarm's operations.

Attribute	Type	Description
name	str	The name of the swarm.
description	str	A description of the swarm's purpose.
agents	Union[Agent, List[Agent]]	The agents participating in the swarm. Can be a single agent or a list of agents.
autosave_on	bool	Flag indicating whether autosave is enabled.
save_file_path	str	The file path where the swarm data will be saved.
task_queue	queue.Queue	The queue that stores tasks to be processed by the agents.
lock	threading.Lock	A lock used for thread synchronization to prevent race conditions.
metadata	SwarmRunMetadata	Metadata for the swarm run, including start time, end time, tasks completed, and outputs.
run_all_agents	bool	Flag indicating whether to run all agents or just one.
max_loops	int	The number of times to repeat the task.
workspace_dir	str	The directory where the workspace is located, retrieved from environment variables.
Parameters¶
name (str, optional): The name of the swarm. Default is "Spreadsheet-Swarm".
description (str, optional): A brief description of the swarm. Default is "A swarm that processes tasks from a queue using multiple agents on different threads.".
agents (Union[Agent, List[Agent]], optional): The agents participating in the swarm. Default is an empty list.
autosave_on (bool, optional): A flag to indicate if autosave is enabled. Default is True.
save_file_path (str, optional): The file path where swarm data will be saved. Default is "spreedsheet_swarm.csv".
run_all_agents (bool, optional): Flag to determine if all agents should run. Default is True.
max_loops (int, optional): The number of times to repeat the task. Default is 1.
workspace_dir (str, optional): The directory where the workspace is located. Default is retrieved from environment variable WORKSPACE_DIR.
Constructor (__init__)¶
The constructor initializes the SpreadSheetSwarm with the provided parameters. It sets up the task queue, locks for thread synchronization, and initializes the metadata.

Methods¶
reliability_check¶

def reliability_check(self):
Description¶
The reliability_check method performs a series of checks to ensure that the swarm is properly configured before it begins processing tasks. It verifies that there are agents available and that a valid file path is provided for saving the swarm's data. If any of these checks fail, an exception is raised.

Raises¶
ValueError: Raised if no agents are provided or if no save file path is specified.
Example¶

swarm = SpreadSheetSwarm(agents=[agent1, agent2])
swarm.reliability_check()
run¶

def run(self, task: str, *args, **kwargs):
Description¶
The run method starts the task processing using the swarm. Depending on the configuration, it can either run all agents or a specific subset of them. The method tracks the start and end times of the task, executes the task multiple times if specified, and logs the results.

Parameters¶
task (str): The task to be executed by the swarm.
*args: Additional positional arguments to pass to the agents.
**kwargs: Additional keyword arguments to pass to the agents.
Example¶

swarm = SpreadSheetSwarm(agents=[agent1, agent2])
swarm.run("Process Data")
export_to_json¶

def export_to_json(self):
Description¶
The export_to_json method generates a JSON representation of the swarm's metadata. This can be useful for exporting the results to an external system or for logging purposes.

Returns¶
str: The JSON representation of the swarm's metadata.
Example¶

json_data = swarm.export_to_json()
print(json_data)
data_to_json_file¶

def data_to_json_file(self):
Description¶
The data_to_json_file method saves the swarm's metadata as a JSON file in the specified workspace directory. The file name is generated using the swarm's name and run ID.

Example¶

swarm.data_to_json_file()
_track_output¶

def _track_output(self, agent: Agent, task: str, result: str):
Description¶
The _track_output method is used internally to record the results of tasks executed by the agents. It updates the metadata with the completed tasks and their results.

Parameters¶
agent (Agent): The agent that executed the task.
task (str): The task that was executed.
result (str): The result of the task execution.
Example¶

swarm._track_output(agent1, "Process Data", "Success")
_save_to_csv¶

def _save_to_csv(self):
Description¶
The _save_to_csv method saves the swarm's metadata to a CSV file. It logs each task and its result before writing them to the file. The file is saved in the location specified by save_file_path.

Example¶

swarm._save_to_csv()
Usage Examples¶
Example 1: Basic Swarm Initialization¶

import os

from swarms import Agent
from swarm_models import OpenAIChat
from swarms.prompts.finance_agent_sys_prompt import (
    FINANCIAL_AGENT_SYS_PROMPT,
)
from swarms.structs.spreadsheet_swarm import SpreadSheetSwarm

# Example usage:
api_key = os.getenv("OPENAI_API_KEY")

# Model
model = OpenAIChat(
    openai_api_key=api_key, model_name="gpt-4o-mini", temperature=0.1
)


# Initialize your agents (assuming the Agent class and model are already defined)
agents = [
    Agent(
        agent_name=f"Financial-Analysis-Agent-spreesheet-swarm:{i}",
        system_prompt=FINANCIAL_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="finance_agent.json",
        user_name="swarms_corp",
        retry_attempts=1,
    )
    for i in range(10)
]

# Create a Swarm with the list of agents
swarm = SpreadSheetSwarm(
    name="Finance-Spreadsheet-Swarm",
    description="A swarm that processes tasks from a queue using multiple agents on different threads.",
    agents=agents,
    autosave_on=True,
    save_file_path="financial_spreed_sheet_swarm_demo.csv",
    run_all_agents=False,
    max_loops=1,
)

# Run the swarm
swarm.run(
    task="Analyze the states with the least taxes for LLCs. Provide an overview of all tax rates and add them with a comprehensive analysis"
)
Example 2: QR Code Generator¶

import os
from swarms import Agent
from swarm_models import OpenAIChat
from swarms.structs.spreadsheet_swarm import SpreadSheetSwarm

# Define custom system prompts for QR code generation
QR_CODE_AGENT_1_SYS_PROMPT = """
You are a Python coding expert. Your task is to write a Python script to generate a QR code for the link: https://lu.ma/jjc1b2bo. The code should save the QR code as an image file.
"""

QR_CODE_AGENT_2_SYS_PROMPT = """
You are a Python coding expert. Your task is to write a Python script to generate a QR code for the link: https://github.com/The-Swarm-Corporation/Cookbook. The code should save the QR code as an image file.
"""

# Example usage:
api_key = os.getenv("OPENAI_API_KEY")

# Model
model = OpenAIChat(
    openai_api_key=api_key, model_name="gpt-4o-mini", temperature=0.1
)

# Initialize your agents for QR code generation
agents = [
    Agent(
        agent_name="QR-Code-Generator-Agent-Luma",
        system_prompt=QR_CODE_AGENT_1_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="qr_code_agent_luma.json",
        user_name="swarms_corp",
        retry_attempts=1,
    ),
    Agent(
        agent_name="QR-Code-Generator-Agent-Cookbook",
        system_prompt=QR_CODE_AGENT_2_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="qr_code_agent_cookbook.json",
        user_name="swarms_corp",
        retry_attempts=1,
    ),
]

# Create a Swarm with the list of agents
swarm = SpreadSheetSwarm(
    name="QR-Code-Generation-Swarm",
    description="A swarm that generates Python scripts to create QR codes for specific links.",
    agents=agents,
    autosave_on=True,
    save_file_path="qr_code_generation_results.csv",
    run_all_agents=False,
    max_loops=1,
)

# Run the swarm
swarm.run(
    task="Generate Python scripts to create QR codes for the provided links and save them as image files."
)
Example 3: Social Media Marketing¶

import os
from swarms import Agent
from swarm_models import OpenAIChat
from swarms.structs.spreadsheet_swarm import SpreadSheetSwarm

# Define custom system prompts for each social media platform
TWITTER_AGENT_SYS_PROMPT = """
You are a Twitter marketing expert. Your task is to create engaging, concise tweets and analyze trends to maximize engagement. Consider hashtags, timing, and content relevance.
"""

INSTAGRAM_AGENT_SYS_PROMPT = """
You are an Instagram marketing expert. Your task is to create visually appealing and engaging content, including captions and hashtags, tailored to a specific audience.
"""

FACEBOOK_AGENT_SYS_PROMPT = """
You are a Facebook marketing expert. Your task is to craft posts that are optimized for engagement and reach on Facebook, including using images, links, and targeted messaging.
"""

EMAIL_AGENT_SYS_PROMPT = """
You are an Email marketing expert. Your task is to write compelling email campaigns that drive conversions, focusing on subject lines, personalization, and call-to-action strategies.
"""

# Example usage:
api_key = os.getenv("OPENAI_API_KEY")

# Model
model = OpenAIChat(
    openai_api_key=api_key, model_name="gpt-4o-mini", temperature=0.1
)

# Initialize your agents for different social media platforms
agents = [
    Agent(
        agent_name="Twitter-Marketing-Agent",
        system_prompt=TWITTER_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="twitter_agent.json",
        user_name="swarms_corp",
        retry_attempts=1,
    ),
    Agent(
        agent_name="Instagram-Marketing-Agent",
        system_prompt=INSTAGRAM_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="instagram_agent.json",
        user_name="swarms_corp",
        retry_attempts=1,
    ),
    Agent(
        agent_name="Facebook-Marketing-Agent",
        system_prompt=FACEBOOK_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="facebook_agent.json",
        user_name="swarms_corp",
        retry_attempts=1,
    ),
    Agent(
        agent_name="Email-Marketing-Agent",
        system_prompt=EMAIL_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="email_agent.json",
        user_name="swarms_corp",
        retry_attempts=1,
    ),
]

# Create a Swarm with the list of agents
swarm = SpreadSheetSwarm(
    name="Social-Media-Marketing-Swarm",
    description="A swarm that processes social media marketing tasks using multiple agents on different threads.",
    agents=agents,
    autosave_on=True,
    save_file_path="social_media_marketing_spreadsheet.csv",
    run_all_agents=False,
    max_loops=2,
)

# Run the swarm
swarm.run(
    task="Create posts to promote hack nights in miami beach for developers, engineers, and tech enthusiasts. Include relevant hashtags, images, and engaging captions."
)
Additional Information and Tips¶
Thread Synchronization: When working with multiple agents in a concurrent environment, it's crucial to ensure that access to shared resources is properly synchronized using locks to avoid race conditions.

Autosave Feature: If you enable the autosave_on flag, ensure that the file path provided is correct and writable. This feature is handy for long-running tasks where you want to periodically save the state.

Error Handling

Implementing proper error handling within your agents can prevent the swarm from crashing during execution. Consider catching exceptions in the run method and logging errors appropriately.
Custom Agents: You can extend the Agent class to create custom agents that perform specific tasks tailored to your application's needs.

Forest Swarm¶
This documentation describes the ForestSwarm that organizes agents into trees. Each agent specializes in processing specific tasks. Trees are collections of agents, each assigned based on their relevance to a task through keyword extraction and embedding-based similarity.

The architecture allows for efficient task assignment by selecting the most relevant agent from a set of trees. Tasks are processed asynchronously, with agents selected based on task relevance, calculated by the similarity of system prompts and task keywords.

Module Path: swarms.structs.tree_swarm¶
Class: TreeAgent¶
TreeAgent represents an individual agent responsible for handling a specific task. Agents are initialized with a system prompt and are responsible for dynamically determining their relevance to a given task.

Attributes¶
Attribute	Type	Description
system_prompt	str	A string that defines the agent's area of expertise and task-handling capability.
llm	callable	The language model (LLM) used to process tasks (e.g., GPT-4).
agent_name	str	The name of the agent.
system_prompt_embedding	tensor	Embedding of the system prompt for similarity-based task matching.
relevant_keywords	List[str]	Keywords dynamically extracted from the system prompt to assist in task matching.
distance	Optional[float]	The computed distance between agents based on embedding similarity.
Methods¶
Method	Input	Output	Description
calculate_distance(other_agent: TreeAgent)	other_agent: TreeAgent	float	Calculates the cosine similarity between this agent and another agent.
run_task(task: str)	task: str	Any	Executes the task, logs the input/output, and returns the result.
is_relevant_for_task(task: str, threshold: float = 0.7)	task: str, threshold: float	bool	Checks if the agent is relevant for the task using keyword matching or embedding similarity.
Class: Tree¶
Tree organizes multiple agents into a hierarchical structure, where agents are sorted based on their relevance to tasks.

Attributes¶
Attribute	Type	Description
tree_name	str	The name of the tree (represents a domain of agents, e.g., "Financial Tree").
agents	List[TreeAgent]	List of agents belonging to this tree.
Methods¶
Method	Input	Output	Description
calculate_agent_distances()	None	None	Calculates and assigns distances between agents based on similarity of prompts.
find_relevant_agent(task: str)	task: str	Optional[TreeAgent]	Finds the most relevant agent for a task based on keyword and embedding similarity.
log_tree_execution(task: str, selected_agent: TreeAgent, result: Any)	task: str, selected_agent: TreeAgent, result: Any	None	Logs details of the task execution by the selected agent.
Class: ForestSwarm¶
ForestSwarm is the main class responsible for managing multiple trees. It oversees task delegation by finding the most relevant tree and agent for a given task.

Attributes¶
Attribute	Type	Description
trees	List[Tree]	List of trees containing agents organized by domain.
Methods¶
Method	Input	Output	Description
find_relevant_tree(task: str)	task: str	Optional[Tree]	Searches across all trees to find the most relevant tree based on task requirements.
run(task: str)	task: str	Any	Executes the task by finding the most relevant agent from the relevant tree.
Full Code Example¶

from swarms.structs.tree_swarm import TreeAgent, Tree, ForestSwarm
# Example Usage:

# Create agents with varying system prompts and dynamically generated distances/keywords
agents_tree1 = [
    TreeAgent(
        system_prompt="Stock Analysis Agent",
        agent_name="Stock Analysis Agent",
    ),
    TreeAgent(
        system_prompt="Financial Planning Agent",
        agent_name="Financial Planning Agent",
    ),
    TreeAgent(
        agent_name="Retirement Strategy Agent",
        system_prompt="Retirement Strategy Agent",
    ),
]

agents_tree2 = [
    TreeAgent(
        system_prompt="Tax Filing Agent",
        agent_name="Tax Filing Agent",
    ),
    TreeAgent(
        system_prompt="Investment Strategy Agent",
        agent_name="Investment Strategy Agent",
    ),
    TreeAgent(
        system_prompt="ROTH IRA Agent", agent_name="ROTH IRA Agent"
    ),
]

# Create trees
tree1 = Tree(tree_name="Financial Tree", agents=agents_tree1)
tree2 = Tree(tree_name="Investment Tree", agents=agents_tree2)

# Create the ForestSwarm
multi_agent_structure = ForestSwarm(trees=[tree1, tree2])

# Run a task
task = "Our company is incorporated in delaware, how do we do our taxes for free?"
output = multi_agent_structure.run(task)
print(output)
Example Workflow¶
Create Agents: Agents are initialized with varying system prompts, representing different areas of expertise (e.g., stock analysis, tax filing).
Create Trees: Agents are grouped into trees, with each tree representing a domain (e.g., "Financial Tree", "Investment Tree").
Run Task: When a task is submitted, the system traverses through all trees and finds the most relevant agent to handle the task.
Task Execution: The selected agent processes the task, and the result is returned.

Task: "Our company is incorporated in Delaware, how do we do our taxes for free?"
Process: - The system searches through the Financial Tree and Investment Tree. - The most relevant agent (likely the "Tax Filing Agent") is selected based on keyword matching and prompt similarity. - The task is processed, and the result is logged and returned.

Analysis of the Swarm Architecture¶
The Swarm Architecture leverages a hierarchical structure (forest) composed of individual trees, each containing agents specialized in specific domains. This design allows for:

Modular and Scalable Organization: By separating agents into trees, it is easy to expand or contract the system by adding or removing trees or agents.
Task Specialization: Each agent is specialized, which ensures that tasks are matched with the most appropriate agent based on relevance and expertise.
Dynamic Matching: The architecture uses both keyword-based and embedding-based matching to assign tasks, ensuring a high level of accuracy in agent selection.
Logging and Accountability: Each task execution is logged in detail, providing transparency and an audit trail of which agent handled which task and the results produced.
Asynchronous Task Execution: The architecture can be adapted for asynchronous task processing, making it scalable and suitable for large-scale task handling in real-time systems.
Mermaid Diagram of the Swarm Architecture¶
Tree Agents

ForestSwarm

Financial Tree

Investment Tree

Stock Analysis Agent

Financial Planning Agent

Retirement Strategy Agent

Tax Filing Agent

Investment Strategy Agent

ROTH IRA Agent

Explanation of the Diagram¶
ForestSwarm: Represents the top-level structure managing multiple trees.
Trees: In the example, two trees exist—Financial Tree and Investment Tree—each containing agents related to specific domains.
Agents: Each agent within the tree is responsible for handling tasks in its area of expertise. Agents within a tree are organized based on their prompt similarity (distance).
Summary¶
This Multi-Agent Tree Structure provides an efficient, scalable, and accurate architecture for delegating and executing tasks based on domain-specific expertise. The combination of hierarchical organization, dynamic task matching, and logging ensures reliability, performance, and transparency in task execution.

SwarmRouter Documentation¶
The SwarmRouter class is a flexible routing system designed to manage different types of swarms for task execution. It provides a unified interface to interact with various swarm types, including AgentRearrange, MixtureOfAgents, SpreadSheetSwarm, SequentialWorkflow, ConcurrentWorkflow, and finally auto which will dynamically select the most appropriate swarm for you by analyzing your name, description, and input task. We will be continuously adding more swarm architectures as we progress with new developments.

Classes¶
SwarmLog¶
A Pydantic model for capturing log entries.

Attribute	Type	Description
id	str	Unique identifier for the log entry.
timestamp	datetime	Time of log creation.
level	str	Log level (e.g., "info", "error").
message	str	Log message content.
swarm_type	SwarmType	Type of swarm associated with the log.
task	str	Task being performed (optional).
metadata	Dict[str, Any]	Additional metadata (optional).
SwarmRouter¶
Main class for routing tasks to different swarm types.

Attribute	Type	Description
name	str	Name of the SwarmRouter instance.
description	str	Description of the SwarmRouter instance.
max_loops	int	Maximum number of loops to perform.
agents	List[Union[Agent, Callable]]	List of Agent objects or callable functions to be used in the swarm.
swarm_type	SwarmType	Type of swarm to be used.
autosave	bool	Flag to enable/disable autosave.
flow	str	The flow of the swarm.
return_json	bool	Flag to enable/disable returning the result in JSON format.
auto_generate_prompts	bool	Flag to enable/disable auto generation of prompts.
swarm	Union[AgentRearrange, MixtureOfAgents, SpreadSheetSwarm, SequentialWorkflow, ConcurrentWorkflow]	Instantiated swarm object.
logs	List[SwarmLog]	List of log entries captured during operations.
Methods:¶
Method	Parameters	Description
__init__	self, name: str, description: str, max_loops: int, agents: List[Union[Agent, Callable]], swarm_type: SwarmType, autosave: bool, flow: str, return_json: bool, auto_generate_prompts: bool, *args, **kwargs	Initialize the SwarmRouter.
reliability_check	self	Perform reliability checks on the SwarmRouter configuration.
_create_swarm	self, task: str = None, *args, **kwargs	Create and return the specified swarm type or automatically match the best swarm type for a given task.
_log	self, level: str, message: str, task: str = "", metadata: Dict[str, Any] = None	Create a log entry and add it to the logs list.
run	self, task: str, *args, **kwargs	Run the specified task on the selected or matched swarm.
batch_run	self, tasks: List[str], *args, **kwargs	Execute a batch of tasks on the selected or matched swarm type.
threaded_run	self, task: str, *args, **kwargs	Execute a task on the selected or matched swarm type using threading.
async_run	self, task: str, *args, **kwargs	Execute a task on the selected or matched swarm type asynchronously.
get_logs	self	Retrieve all logged entries.
concurrent_run	self, task: str, *args, **kwargs	Execute a task on the selected or matched swarm type concurrently.
concurrent_batch_run	self, tasks: List[str], *args, **kwargs	Execute a batch of tasks on the selected or matched swarm type concurrently.
Installation¶
To use the SwarmRouter, first install the required dependencies:


pip install swarms swarm_models
Basic Usage¶

import os
from dotenv import load_dotenv
from swarms import Agent, SwarmRouter, SwarmType
from swarm_models import OpenAIChat

load_dotenv()

# Get the OpenAI API key from the environment variable
api_key = os.getenv("GROQ_API_KEY")

# Model
model = OpenAIChat(
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=api_key,
    model_name="llama-3.1-70b-versatile",
    temperature=0.1,
)

# Define specialized system prompts for each agent
DATA_EXTRACTOR_PROMPT = """You are a highly specialized private equity agent focused on data extraction from various documents. Your expertise includes:
1. Extracting key financial metrics (revenue, EBITDA, growth rates, etc.) from financial statements and reports
2. Identifying and extracting important contract terms from legal documents
3. Pulling out relevant market data from industry reports and analyses
4. Extracting operational KPIs from management presentations and internal reports
5. Identifying and extracting key personnel information from organizational charts and bios
Provide accurate, structured data extracted from various document types to support investment analysis."""

SUMMARIZER_PROMPT = """You are an expert private equity agent specializing in summarizing complex documents. Your core competencies include:
1. Distilling lengthy financial reports into concise executive summaries
2. Summarizing legal documents, highlighting key terms and potential risks
3. Condensing industry reports to capture essential market trends and competitive dynamics
4. Summarizing management presentations to highlight key strategic initiatives and projections
5. Creating brief overviews of technical documents, emphasizing critical points for non-technical stakeholders
Deliver clear, concise summaries that capture the essence of various documents while highlighting information crucial for investment decisions."""

# Initialize specialized agents
data_extractor_agent = Agent(
    agent_name="Data-Extractor",
    system_prompt=DATA_EXTRACTOR_PROMPT,
    llm=model,
    max_loops=1,
    autosave=True,
    verbose=True,
    dynamic_temperature_enabled=True,
    saved_state_path="data_extractor_agent.json",
    user_name="pe_firm",
    retry_attempts=1,
    context_length=200000,
    output_type="string",
)

summarizer_agent = Agent(
    agent_name="Document-Summarizer",
    system_prompt=SUMMARIZER_PROMPT,
    llm=model,
    max_loops=1,
    autosave=True,
    verbose=True,
    dynamic_temperature_enabled=True,
    saved_state_path="summarizer_agent.json",
    user_name="pe_firm",
    retry_attempts=1,
    context_length=200000,
    output_type="string",
)

# Initialize the SwarmRouter
router = SwarmRouter(
    name="pe-document-analysis-swarm",
    description="Analyze documents for private equity due diligence and investment decision-making",
    max_loops=1,
    agents=[data_extractor_agent, summarizer_agent],
    swarm_type="ConcurrentWorkflow",
    autosave=True,
    return_json=True,
)

# Example usage
if __name__ == "__main__":
    # Run a comprehensive private equity document analysis task
    result = router.run(
        "Where is the best place to find template term sheets for series A startups? Provide links and references"
    )
    print(result)

    # Retrieve and print logs
    for log in router.get_logs():
        print(f"{log.timestamp} - {log.level}: {log.message}")
Advanced Usage¶
Changing Swarm Types¶
You can create multiple SwarmRouter instances with different swarm types:


sequential_router = SwarmRouter(
    name="SequentialRouter",
    agents=[agent1, agent2],
    swarm_type="SequentialWorkflow"
)

concurrent_router = SwarmRouter(
    name="ConcurrentRouter",
    agents=[agent1, agent2],
    swarm_type="ConcurrentWorkflow"
)
Automatic Swarm Type Selection¶
You can let the SwarmRouter automatically select the best swarm type for a given task:


auto_router = SwarmRouter(
    name="AutoRouter",
    agents=[agent1, agent2],
    swarm_type="auto"
)

result = auto_router.run("Analyze and summarize the quarterly financial report")
Use Cases¶
AgentRearrange¶
Use Case: Optimizing agent order for complex multi-step tasks.


rearrange_router = SwarmRouter(
    name="TaskOptimizer",
    description="Optimize agent order for multi-step tasks",
    max_loops=3,
    agents=[data_extractor, analyzer, summarizer],
    swarm_type="AgentRearrange",
    flow=f"{data_extractor.name} -> {analyzer.name} -> {summarizer.name}"
)

result = rearrange_router.run("Analyze and summarize the quarterly financial report")
MixtureOfAgents¶
Use Case: Combining diverse expert agents for comprehensive analysis.


mixture_router = SwarmRouter(
    name="ExpertPanel",
    description="Combine insights from various expert agents",
    max_loops=1,
    agents=[financial_expert, market_analyst, tech_specialist],
    swarm_type="MixtureOfAgents"
)

result = mixture_router.run("Evaluate the potential acquisition of TechStartup Inc.")
SpreadSheetSwarm¶
Use Case: Collaborative data processing and analysis.


spreadsheet_router = SwarmRouter(
    name="DataProcessor",
    description="Collaborative data processing and analysis",
    max_loops=1,
    agents=[data_cleaner, statistical_analyzer, visualizer],
    swarm_type="SpreadSheetSwarm"
)

result = spreadsheet_router.run("Process and visualize customer churn data")
SequentialWorkflow¶
Use Case: Step-by-step document analysis and report generation.


sequential_router = SwarmRouter(
    name="ReportGenerator",
    description="Generate comprehensive reports sequentially",
    max_loops=1,
    agents=[data_extractor, analyzer, writer, reviewer],
    swarm_type="SequentialWorkflow"
)

result = sequential_router.run("Create a due diligence report for Project Alpha")
ConcurrentWorkflow¶
Use Case: Parallel processing of multiple data sources.


concurrent_router = SwarmRouter(
    name="MultiSourceAnalyzer",
    description="Analyze multiple data sources concurrently",
    max_loops=1,
    agents=[financial_analyst, market_researcher, competitor_analyst],
    swarm_type="ConcurrentWorkflow"
)

result = concurrent_router.run("Conduct a comprehensive market analysis for Product X")
Auto Select (Experimental)¶
Autonomously selects the right swarm by conducting vector search on your input task or name or description or all 3.


concurrent_router = SwarmRouter(
    name="MultiSourceAnalyzer",
    description="Analyze multiple data sources concurrently",
    max_loops=1,
    agents=[financial_analyst, market_researcher, competitor_analyst],
    swarm_type="auto" # Set this to 'auto' for it to auto select your swarm. It's match words like concurrently multiple -> "ConcurrentWorkflow"
)

result = concurrent_router.run("Conduct a comprehensive market analysis for Product X")
Advanced Features¶
Batch Processing¶
To process multiple tasks in a batch:


tasks = ["Analyze Q1 report", "Summarize competitor landscape", "Evaluate market trends"]
results = router.batch_run(tasks)
Threaded Execution¶
For non-blocking execution of a task:


result = router.threaded_run("Perform complex analysis")
Asynchronous Execution¶
For asynchronous task execution:


result = await router.async_run("Generate financial projections")
Concurrent Execution¶
To run a single task concurrently:


result = router.concurrent_run("Analyze multiple data streams")
Concurrent Batch Processing¶
To process multiple tasks concurrently:


tasks = ["Task 1", "Task 2", "Task 3"]
results = router.concurrent_batch_run(tasks)
Best Practices¶
Choose the appropriate swarm type based on your task requirements.
Provide clear and specific tasks to the swarm for optimal results.
Regularly review logs to monitor performance and identify potential issues.
Use descriptive names and descriptions for your SwarmRouter and agents.
Implement proper error handling in your application code.
Consider the nature of your tasks when choosing a swarm type (e.g., use ConcurrentWorkflow for tasks that can be parallelized).
Optimize your agents' prompts and configurations for best performance within the swarm.
Utilize the automatic swarm type selection feature for tasks where the optimal swarm type is not immediately clear.
Take advantage of batch processing and concurrent execution for handling multiple tasks efficiently.
Use the reliability check feature to ensure your SwarmRouter is properly configured before running tasks.

TaskQueueSwarm Documentation¶
The TaskQueueSwarm class is designed to manage and execute tasks using multiple agents concurrently. This class allows for the orchestration of multiple agents processing tasks from a shared queue, facilitating complex workflows where tasks can be distributed and processed in parallel by different agents.

Attributes¶
Attribute	Type	Description
agents	List[Agent]	The list of agents in the swarm.
task_queue	queue.Queue	A queue to store tasks for processing.
lock	threading.Lock	A lock for thread synchronization.
autosave_on	bool	Whether to automatically save the swarm metadata.
save_file_path	str	The file path for saving swarm metadata.
workspace_dir	str	The directory path of the workspace.
return_metadata_on	bool	Whether to return the swarm metadata after running.
max_loops	int	The maximum number of loops to run the swarm.
metadata	SwarmRunMetadata	Metadata about the swarm run.
Methods¶
__init__(self, agents: List[Agent], name: str = "Task-Queue-Swarm", description: str = "A swarm that processes tasks from a queue using multiple agents on different threads.", autosave_on: bool = True, save_file_path: str = "swarm_run_metadata.json", workspace_dir: str = os.getenv("WORKSPACE_DIR"), return_metadata_on: bool = False, max_loops: int = 1, *args, **kwargs)¶
The constructor initializes the TaskQueueSwarm object.

Parameters:
agents (List[Agent]): The list of agents in the swarm.
name (str, optional): The name of the swarm. Defaults to "Task-Queue-Swarm".
description (str, optional): The description of the swarm. Defaults to "A swarm that processes tasks from a queue using multiple agents on different threads.".
autosave_on (bool, optional): Whether to automatically save the swarm metadata. Defaults to True.
save_file_path (str, optional): The file path to save the swarm metadata. Defaults to "swarm_run_metadata.json".
workspace_dir (str, optional): The directory path of the workspace. Defaults to os.getenv("WORKSPACE_DIR").
return_metadata_on (bool, optional): Whether to return the swarm metadata after running. Defaults to False.
max_loops (int, optional): The maximum number of loops to run the swarm. Defaults to 1.
*args: Variable length argument list.
**kwargs: Arbitrary keyword arguments.
add_task(self, task: str)¶
Adds a task to the queue.

Parameters:
task (str): The task to be added to the queue.
run(self)¶
Runs the swarm by having agents pick up tasks from the queue.

Returns:
str: JSON string of the swarm run metadata if return_metadata_on is True.

Usage Example:


from swarms import Agent, TaskQueueSwarm
from swarms_models import OpenAIChat

# Initialize the language model
llm = OpenAIChat()

# Initialize agents
agent1 = Agent(agent_name="Agent1", llm=llm)
agent2 = Agent(agent_name="Agent2", llm=llm)

# Create the TaskQueueSwarm
swarm = TaskQueueSwarm(agents=[agent1, agent2], max_loops=5)

# Add tasks to the swarm
swarm.add_task("Analyze the latest market trends")
swarm.add_task("Generate a summary report")

# Run the swarm
result = swarm.run()
print(result)  # Prints the swarm run metadata
This example initializes a TaskQueueSwarm with two agents, adds tasks to the queue, and runs the swarm.

save_json_to_file(self)¶
Saves the swarm run metadata to a JSON file.

export_metadata(self)¶
Exports the swarm run metadata as a JSON string.

Returns:
str: JSON string of the swarm run metadata.
Additional Notes¶
The TaskQueueSwarm uses threading to process tasks concurrently, which can significantly improve performance for I/O-bound tasks.
The reliability_checks method ensures that the swarm is properly configured before running.
The swarm automatically handles task distribution among agents and provides detailed metadata about the run.
Error handling and logging are implemented to track the execution flow and capture any issues during task processing.

SwarmRearrange Documentation¶
SwarmRearrange is a class for orchestrating multiple swarms in a sequential or parallel flow pattern. It provides thread-safe operations for managing swarm execution, history tracking, and flow validation.

Constructor Arguments¶
Parameter	Type	Default	Description
id	str	UUID	Unique identifier for the swarm arrangement
name	str	"SwarmRearrange"	Name of the swarm arrangement
description	str	"A swarm of swarms..."	Description of the arrangement
swarms	List[Any]	[]	List of swarm objects to be managed
flow	str	None	Flow pattern for swarm execution
max_loops	int	1	Maximum number of execution loops
verbose	bool	True	Enable detailed logging
human_in_the_loop	bool	False	Enable human intervention
custom_human_in_the_loop	Callable	None	Custom function for human interaction
return_json	bool	False	Return results in JSON format
Methods¶
add_swarm(swarm: Any)¶
Adds a single swarm to the arrangement.

remove_swarm(swarm_name: str)¶
Removes a swarm by name from the arrangement.

add_swarms(swarms: List[Any])¶
Adds multiple swarms to the arrangement.

validate_flow()¶
Validates the flow pattern syntax and swarm names.

run(task: str = None, img: str = None, custom_tasks: Dict[str, str] = None)¶
Executes the swarm arrangement according to the flow pattern.

Flow Pattern Syntax¶
The flow pattern uses arrow notation (->) to define execution order:

Sequential: "SwarmA -> SwarmB -> SwarmC"
Parallel: "SwarmA, SwarmB -> SwarmC"
Human intervention: Use "H" in the flow
Examples¶
Basic Sequential Flow¶

from swarms.structs.swarm_arange import SwarmRearrange
import os
from swarms import Agent, AgentRearrange
from swarm_models import OpenAIChat

# model = Anthropic(anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))
company = "TGSC"

# Get the OpenAI API key from the environment variable
api_key = os.getenv("GROQ_API_KEY")

# Model
model = OpenAIChat(
    openai_api_base="https://api.groq.com/openai/v1",
    openai_api_key=api_key,
    model_name="llama-3.1-70b-versatile",
    temperature=0.1,
)


# Initialize the Managing Director agent
managing_director = Agent(
    agent_name="Managing-Director",
    system_prompt=f"""
    As the Managing Director at Blackstone, your role is to oversee the entire investment analysis process for potential acquisitions. 
    Your responsibilities include:
    1. Setting the overall strategy and direction for the analysis
    2. Coordinating the efforts of the various team members and ensuring a comprehensive evaluation
    3. Reviewing the findings and recommendations from each team member
    4. Making the final decision on whether to proceed with the acquisition

    For the current potential acquisition of {company}, direct the tasks for the team to thoroughly analyze all aspects of the company, including its financials, industry position, technology, market potential, and regulatory compliance. Provide guidance and feedback as needed to ensure a rigorous and unbiased assessment.
    """,
    llm=model,
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="managing-director.json",
)

# Initialize the Vice President of Finance
vp_finance = Agent(
    agent_name="VP-Finance",
    system_prompt=f"""
    As the Vice President of Finance at Blackstone, your role is to lead the financial analysis of potential acquisitions. 
    For the current potential acquisition of {company}, your tasks include:
    1. Conducting a thorough review of {company}' financial statements, including income statements, balance sheets, and cash flow statements
    2. Analyzing key financial metrics such as revenue growth, profitability margins, liquidity ratios, and debt levels
    3. Assessing the company's historical financial performance and projecting future performance based on assumptions and market conditions
    4. Identifying any financial risks or red flags that could impact the acquisition decision
    5. Providing a detailed report on your findings and recommendations to the Managing Director

    Be sure to consider factors such as the sustainability of {company}' business model, the strength of its customer base, and its ability to generate consistent cash flows. Your analysis should be data-driven, objective, and aligned with Blackstone's investment criteria.
    """,
    llm=model,
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="vp-finance.json",
)

# Initialize the Industry Analyst
industry_analyst = Agent(
    agent_name="Industry-Analyst",
    system_prompt=f"""
    As the Industry Analyst at Blackstone, your role is to provide in-depth research and analysis on the industries and markets relevant to potential acquisitions.
    For the current potential acquisition of {company}, your tasks include:
    1. Conducting a comprehensive analysis of the industrial robotics and automation solutions industry, including market size, growth rates, key trends, and future prospects
    2. Identifying the major players in the industry and assessing their market share, competitive strengths and weaknesses, and strategic positioning 
    3. Evaluating {company}' competitive position within the industry, including its market share, differentiation, and competitive advantages
    4. Analyzing the key drivers and restraints for the industry, such as technological advancements, labor costs, regulatory changes, and economic conditions
    5. Identifying potential risks and opportunities for {company} based on the industry analysis, such as disruptive technologies, emerging markets, or shifts in customer preferences  

    Your analysis should provide a clear and objective assessment of the attractiveness and future potential of the industrial robotics industry, as well as {company}' positioning within it. Consider both short-term and long-term factors, and provide evidence-based insights to inform the investment decision.
    """,
    llm=model,
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="industry-analyst.json",
)

# Initialize the Technology Expert
tech_expert = Agent(
    agent_name="Tech-Expert",
    system_prompt=f"""
    As the Technology Expert at Blackstone, your role is to assess the technological capabilities, competitive advantages, and potential risks of companies being considered for acquisition.
    For the current potential acquisition of {company}, your tasks include:
    1. Conducting a deep dive into {company}' proprietary technologies, including its robotics platforms, automation software, and AI capabilities 
    2. Assessing the uniqueness, scalability, and defensibility of {company}' technology stack and intellectual property
    3. Comparing {company}' technologies to those of its competitors and identifying any key differentiators or technology gaps
    4. Evaluating {company}' research and development capabilities, including its innovation pipeline, engineering talent, and R&D investments
    5. Identifying any potential technology risks or disruptive threats that could impact {company}' long-term competitiveness, such as emerging technologies or expiring patents

    Your analysis should provide a comprehensive assessment of {company}' technological strengths and weaknesses, as well as the sustainability of its competitive advantages. Consider both the current state of its technology and its future potential in light of industry trends and advancements.
    """,
    llm=model,
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="tech-expert.json",
)

# Initialize the Market Researcher
market_researcher = Agent(
    agent_name="Market-Researcher",
    system_prompt=f"""
    As the Market Researcher at Blackstone, your role is to analyze the target company's customer base, market share, and growth potential to assess the commercial viability and attractiveness of the potential acquisition.
    For the current potential acquisition of {company}, your tasks include:
    1. Analyzing {company}' current customer base, including customer segmentation, concentration risk, and retention rates
    2. Assessing {company}' market share within its target markets and identifying key factors driving its market position
    3. Conducting a detailed market sizing and segmentation analysis for the industrial robotics and automation markets, including identifying high-growth segments and emerging opportunities
    4. Evaluating the demand drivers and sales cycles for {company}' products and services, and identifying any potential risks or limitations to adoption
    5. Developing financial projections and estimates for {company}' revenue growth potential based on the market analysis and assumptions around market share and penetration

    Your analysis should provide a data-driven assessment of the market opportunity for {company} and the feasibility of achieving our investment return targets. Consider both bottom-up and top-down market perspectives, and identify any key sensitivities or assumptions in your projections.
    """,
    llm=model,
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="market-researcher.json",
)

# Initialize the Regulatory Specialist
regulatory_specialist = Agent(
    agent_name="Regulatory-Specialist",
    system_prompt=f"""
    As the Regulatory Specialist at Blackstone, your role is to identify and assess any regulatory risks, compliance requirements, and potential legal liabilities associated with potential acquisitions.
    For the current potential acquisition of {company}, your tasks include:  
    1. Identifying all relevant regulatory bodies and laws that govern the operations of {company}, including industry-specific regulations, labor laws, and environmental regulations
    2. Reviewing {company}' current compliance policies, procedures, and track record to identify any potential gaps or areas of non-compliance
    3. Assessing the potential impact of any pending or proposed changes to relevant regulations that could affect {company}' business or create additional compliance burdens
    4. Evaluating the potential legal liabilities and risks associated with {company}' products, services, and operations, including product liability, intellectual property, and customer contracts
    5. Providing recommendations on any regulatory or legal due diligence steps that should be taken as part of the acquisition process, as well as any post-acquisition integration considerations

    Your analysis should provide a comprehensive assessment of the regulatory and legal landscape surrounding {company}, and identify any material risks or potential deal-breakers. Consider both the current state and future outlook, and provide practical recommendations to mitigate identified risks.
    """,
    llm=model,
    max_loops=1,
    dashboard=False,
    streaming_on=True,
    verbose=True,
    stopping_token="<DONE>",
    state_save_file_type="json",
    saved_state_path="regulatory-specialist.json",
)

# Create a list of agents
agents = [
    managing_director,
    vp_finance,
    industry_analyst,
    tech_expert,
    market_researcher,
    regulatory_specialist,
]

# Define multiple flow patterns
flows = [
    "Industry-Analyst -> Tech-Expert -> Market-Researcher -> Regulatory-Specialist -> Managing-Director -> VP-Finance",
    "Managing-Director -> VP-Finance -> Industry-Analyst -> Tech-Expert -> Market-Researcher -> Regulatory-Specialist",
    "Tech-Expert -> Market-Researcher -> Regulatory-Specialist -> Industry-Analyst -> Managing-Director -> VP-Finance",
]

# Create instances of AgentRearrange for each flow pattern
blackstone_acquisition_analysis = AgentRearrange(
    name="Blackstone-Acquisition-Analysis",
    description="A system for analyzing potential acquisitions",
    agents=agents,
    flow=flows[0],
)

blackstone_investment_strategy = AgentRearrange(
    name="Blackstone-Investment-Strategy",
    description="A system for evaluating investment opportunities",
    agents=agents,
    flow=flows[1],
)

blackstone_market_analysis = AgentRearrange(
    name="Blackstone-Market-Analysis",
    description="A system for analyzing market trends and opportunities",
    agents=agents,
    flow=flows[2],
)

swarm_arrange = SwarmRearrange(
    swarms=[
        blackstone_acquisition_analysis,
        blackstone_investment_strategy,
        blackstone_market_analysis,
    ],
    flow=f"{blackstone_acquisition_analysis.name} -> {blackstone_investment_strategy.name} -> {blackstone_market_analysis.name}",
)

print(
    swarm_arrange.run(
        "Analyze swarms, 150k revenue with 45m+ agents build, with 1.4m downloads since march 2024"
    )
)
Human-in-the-Loop¶

def custom_human_input(task):
    return input(f"Review {task} and provide feedback: ")

# Create arrangement with human intervention
arrangement = SwarmRearrange(
    name="HumanAugmented",
    swarms=[swarm1, swarm2],
    flow="SwarmA -> H -> SwarmB",
    human_in_the_loop=True,
    custom_human_in_the_loop=custom_human_input
)

# Execute with human intervention
result = arrangement.run("Initial task")
Complex Multi-Stage Pipeline¶

# Define multiple flow patterns
flows = [
    "Collector -> Processor -> Analyzer",
    "Analyzer -> ML -> Validator",
    "Validator -> Reporter"
]

# Create arrangements for each flow
pipelines = [
    SwarmRearrange(name=f"Pipeline{i}", swarms=swarms, flow=flow)
    for i, flow in enumerate(flows)
]

# Create master arrangement
master = SwarmRearrange(
    name="MasterPipeline",
    swarms=pipelines,
    flow="Pipeline0 -> Pipeline1 -> Pipeline2"
)

# Execute complete pipeline
result = master.run("Start analysis")
Best Practices¶
Flow Validation: Always validate flows before execution
Error Handling: Implement try-catch blocks around run() calls
History Tracking: Use track_history() for monitoring swarm execution
Resource Management: Set appropriate max_loops to prevent infinite execution
Logging: Enable verbose mode during development for detailed logging

MultiAgentRouter Documentation¶
The MultiAgentRouter is a sophisticated task routing system that efficiently delegates tasks to specialized AI agents. It uses a "boss" agent to analyze incoming tasks and route them to the most appropriate specialized agent based on their capabilities and expertise.

Table of Contents¶
Installation
Key Components
Arguments
Methods
Usage Examples
Healthcare
Finance
Legal
Research
Installation¶

pip install swarms
Key Components¶
Arguments Table¶
Argument	Type	Default	Description
name	str	"swarm-router"	Name identifier for the router instance
description	str	"Routes tasks..."	Description of the router's purpose
agents	List[Agent]	[]	List of available specialized agents
model	str	"gpt-4o-mini"	Base language model for the boss agent
temperature	float	0.1	Temperature parameter for model outputs
shared_memory_system	callable	None	Optional shared memory system
output_type	Literal["json", "string"]	"json"	Format of agent outputs
execute_task	bool	True	Whether to execute routed tasks
Methods Table¶
Method	Arguments	Returns	Description
route_task	task: str	dict	Routes a single task to appropriate agent
batch_route	tasks: List[str]	List[dict]	Sequentially routes multiple tasks
concurrent_batch_route	tasks: List[str]	List[dict]	Concurrently routes multiple tasks
query_ragent	task: str	str	Queries the research agent
find_agent_in_list	agent_name: str	Optional[Agent]	Finds agent by name
Production Examples¶
Healthcare Example¶

from swarms import Agent, MultiAgentRouter

# Define specialized healthcare agents
agents = [
    Agent(
        agent_name="DiagnosisAgent",
        description="Specializes in preliminary symptom analysis and diagnostic suggestions",
        system_prompt="""You are a medical diagnostic assistant. Analyze symptoms and provide 
        evidence-based diagnostic suggestions, always noting this is for informational purposes 
        only and recommending professional medical consultation.""",
        model_name="openai/gpt-4o"
    ),
    Agent(
        agent_name="TreatmentPlanningAgent",
        description="Assists in creating treatment plans and medical documentation",
        system_prompt="""You are a treatment planning assistant. Help create structured 
        treatment plans based on confirmed diagnoses, following medical best practices 
        and guidelines.""",
        model_name="openai/gpt-4o"
    ),
    Agent(
        agent_name="MedicalResearchAgent",
        description="Analyzes medical research papers and clinical studies",
        system_prompt="""You are a medical research analyst. Analyze and summarize medical 
        research papers, clinical trials, and scientific studies, providing evidence-based 
        insights.""",
        model_name="openai/gpt-4o"
    )
]

# Initialize router
healthcare_router = MultiAgentRouter(
    name="Healthcare-Router",
    description="Routes medical and healthcare-related tasks to specialized agents",
    agents=agents,
    model="gpt-4o",
    temperature=0.1
)

# Example usage
try:
    # Process medical case
    case_analysis = healthcare_router.route_task(
        """Patient presents with: 
        - Persistent dry cough for 3 weeks
        - Mild fever (38.1°C)
        - Fatigue
        Analyze symptoms and suggest potential diagnoses for healthcare provider review."""
    )

    # Research treatment options
    treatment_research = healthcare_router.route_task(
        """Find recent clinical studies on treatment efficacy for community-acquired 
        pneumonia in adult patients, focusing on outpatient care."""
    )

    # Process multiple cases concurrently
    cases = [
        "Case 1: Patient symptoms...",
        "Case 2: Patient symptoms...",
        "Case 3: Patient symptoms..."
    ]
    concurrent_results = healthcare_router.concurrent_batch_route(cases)

except Exception as e:
    logger.error(f"Error in healthcare processing: {str(e)}")
Finance Example¶

# Define specialized finance agents
finance_agents = [
    Agent(
        agent_name="MarketAnalysisAgent",
        description="Analyzes market trends and provides trading insights",
        system_prompt="""You are a financial market analyst. Analyze market data, trends, 
        and indicators to provide evidence-based market insights and trading suggestions.""",
        model_name="openai/gpt-4o"
    ),
    Agent(
        agent_name="RiskAssessmentAgent",
        description="Evaluates financial risks and compliance requirements",
        system_prompt="""You are a risk assessment specialist. Analyze financial data 
        and operations for potential risks, ensuring regulatory compliance and suggesting 
        risk mitigation strategies.""",
        model_name="openai/gpt-4o"
    ),
    Agent(
        agent_name="InvestmentAgent",
        description="Provides investment strategies and portfolio management",
        system_prompt="""You are an investment strategy specialist. Develop and analyze 
        investment strategies, portfolio allocations, and provide long-term financial 
        planning guidance.""",
        model_name="openai/gpt-4o"
    )
]

# Initialize finance router
finance_router = MultiAgentRouter(
    name="Finance-Router",
    description="Routes financial analysis and investment tasks",
    agents=finance_agents
)

# Example tasks
tasks = [
    """Analyze current market conditions for technology sector, focusing on:
    - AI/ML companies
    - Semiconductor manufacturers
    - Cloud service providers
    Provide risk assessment and investment opportunities.""",

    """Develop a diversified portfolio strategy for a conservative investor with:
    - Investment horizon: 10 years
    - Risk tolerance: Low to medium
    - Initial investment: $500,000
    - Monthly contribution: $5,000""",

    """Conduct risk assessment for a fintech startup's crypto trading platform:
    - Regulatory compliance requirements
    - Security measures
    - Operational risks
    - Market risks"""
]

# Process tasks concurrently
results = finance_router.concurrent_batch_route(tasks)
Legal Example¶

# Define specialized legal agents
legal_agents = [
    Agent(
        agent_name="ContractAnalysisAgent",
        description="Analyzes legal contracts and documents",
        system_prompt="""You are a legal document analyst. Review contracts and legal 
        documents for key terms, potential issues, and compliance requirements.""",
        model_name="openai/gpt-4o"
    ),
    Agent(
        agent_name="ComplianceAgent",
        description="Ensures regulatory compliance and updates",
        system_prompt="""You are a legal compliance specialist. Monitor and analyze 
        regulatory requirements, ensuring compliance and suggesting necessary updates 
        to policies and procedures.""",
        model_name="openai/gpt-4o"
    ),
    Agent(
        agent_name="LegalResearchAgent",
        description="Conducts legal research and case analysis",
        system_prompt="""You are a legal researcher. Research relevant cases, statutes, 
        and regulations, providing comprehensive legal analysis and citations.""",
        model_name="openai/gpt-4o"
    )
]

# Initialize legal router
legal_router = MultiAgentRouter(
    name="Legal-Router",
    description="Routes legal analysis and compliance tasks",
    agents=legal_agents
)

# Example usage for legal department
contract_analysis = legal_router.route_task(
    """Review the following software licensing agreement:
    [contract text]

    Analyze for:
    1. Key terms and conditions
    2. Potential risks and liabilities
    3. Compliance with current regulations
    4. Suggested modifications"""
)
Error Handling and Best Practices¶
Always use try-except blocks for task routing:


try:
    result = router.route_task(task)
except Exception as e:
    logger.error(f"Task routing failed: {str(e)}")
Monitor agent performance:


if result["execution"]["execution_time"] > 5.0:
    logger.warning(f"Long execution time for task: {result['task']['original']}")
Implement rate limiting for concurrent tasks:


from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=5) as executor:
    results = router.concurrent_batch_route(tasks)
Regular agent validation:


for agent in router.agents.values():
    if not agent.validate():
        logger.error(f"Agent validation failed: {agent.name}")
Performance Considerations¶
Task Batching

Group similar tasks together

Use concurrent_batch_route for independent tasks

Monitor memory usage with large batches

Model Selection

Choose appropriate models based on task complexity

Balance speed vs. accuracy requirements

Consider cost implications

Response Caching

Implement caching for frequently requested analyses

Use shared memory system for repeated queries

Regular cache invalidation for time-sensitive data

Security Considerations¶
Data Privacy

Implement data encryption

Handle sensitive information appropriately

Regular security audits

Access Control

Implement role-based access

Audit logging

Regular permission reviews

Monitoring and Logging¶
Performance Metrics

Response times

Success rates

Error rates

Resource utilization

Logging

Use structured logging

Implement log rotation

Regular log analysis

Alerts

Set up alerting for critical errors

Monitor resource usage

Track API rate limits

ConcurrentWorkflow Documentation¶
Overview¶
The ConcurrentWorkflow class is designed to facilitate the concurrent execution of multiple agents, each tasked with solving a specific query or problem. This class is particularly useful in scenarios where multiple agents need to work in parallel, allowing for efficient resource utilization and faster completion of tasks. The workflow manages the execution, collects metadata, and optionally saves the results in a structured format.

Key Features¶
Concurrent Execution: Runs multiple agents simultaneously using Python's asyncio and ThreadPoolExecutor.
Metadata Collection: Gathers detailed metadata about each agent's execution, including start and end times, duration, and output.
Customizable Output: Allows the user to save metadata to a file or return it as a string or dictionary.
Error Handling: Implements retry logic for improved reliability.
Batch Processing: Supports running tasks in batches and parallel execution.
Asynchronous Execution: Provides asynchronous run options for improved performance.
Class Definitions¶
AgentOutputSchema¶
The AgentOutputSchema class is a data model that captures the output and metadata for each agent's execution. It inherits from pydantic.BaseModel and provides structured fields to store essential information.

Attribute	Type	Description
run_id	Optional[str]	Unique ID for the run, automatically generated using uuid.
agent_name	Optional[str]	Name of the agent that executed the task.
task	Optional[str]	The task or query given to the agent.
output	Optional[str]	The output generated by the agent.
start_time	Optional[datetime]	The time when the agent started the task.
end_time	Optional[datetime]	The time when the agent completed the task.
duration	Optional[float]	The total time taken to complete the task, in seconds.
MetadataSchema¶
The MetadataSchema class is another data model that aggregates the outputs from all agents involved in the workflow. It also inherits from pydantic.BaseModel and includes fields for additional workflow-level metadata.

Attribute	Type	Description
swarm_id	Optional[str]	Unique ID for the workflow run, generated using uuid.
task	Optional[str]	The task or query given to all agents.
description	Optional[str]	A description of the workflow, typically indicating concurrent execution.
agents	Optional[List[AgentOutputSchema]]	A list of agent outputs and metadata.
timestamp	Optional[datetime]	The timestamp when the workflow was executed.
ConcurrentWorkflow¶
The ConcurrentWorkflow class is the core class that manages the concurrent execution of agents. It inherits from BaseSwarm and includes several key attributes and methods to facilitate this process.

Attributes¶
Attribute	Type	Description
name	str	The name of the workflow. Defaults to "ConcurrentWorkflow".
description	str	A brief description of the workflow.
agents	List[Agent]	A list of agents to be executed concurrently.
metadata_output_path	str	Path to save the metadata output. Defaults to "agent_metadata.json".
auto_save	bool	Flag indicating whether to automatically save the metadata.
output_schema	BaseModel	The output schema for the metadata, defaults to MetadataSchema.
max_loops	int	Maximum number of loops for the workflow, defaults to 1.
return_str_on	bool	Flag to return output as string. Defaults to False.
agent_responses	List[str]	List of agent responses as strings.
auto_generate_prompts	bool	Flag indicating whether to auto-generate prompts for agents.
Methods¶
ConcurrentWorkflow.__init__¶
Initializes the ConcurrentWorkflow class with the provided parameters.

Parameters¶
Parameter	Type	Default Value	Description
name	str	"ConcurrentWorkflow"	The name of the workflow.
description	str	"Execution of multiple agents concurrently"	A brief description of the workflow.
agents	List[Agent]	[]	A list of agents to be executed concurrently.
metadata_output_path	str	"agent_metadata.json"	Path to save the metadata output.
auto_save	bool	False	Flag indicating whether to automatically save the metadata.
output_schema	BaseModel	MetadataSchema	The output schema for the metadata.
max_loops	int	1	Maximum number of loops for the workflow.
return_str_on	bool	False	Flag to return output as string.
agent_responses	List[str]	[]	List of agent responses as strings.
auto_generate_prompts	bool	False	Flag indicating whether to auto-generate prompts for agents.
Raises¶
ValueError: If the list of agents is empty or if the description is empty.
ConcurrentWorkflow.activate_auto_prompt_engineering¶
Activates the auto-generate prompts feature for all agents in the workflow.

Example¶

workflow = ConcurrentWorkflow(agents=[Agent()])
workflow.activate_auto_prompt_engineering()
# All agents in the workflow will now auto-generate prompts.
ConcurrentWorkflow._run_agent¶
Runs a single agent with the provided task and tracks its output and metadata.

Parameters¶
Parameter	Type	Description
agent	Agent	The agent instance to run.
task	str	The task or query to give to the agent.
executor	ThreadPoolExecutor	The thread pool executor to use for running the agent task.
Returns¶
AgentOutputSchema: The metadata and output from the agent's execution.
Detailed Explanation¶
This method handles the execution of a single agent by offloading the task to a thread using ThreadPoolExecutor. It also tracks the time taken by the agent to complete the task and logs relevant information. If an exception occurs during execution, it captures the error and includes it in the output. The method implements retry logic for improved reliability.

ConcurrentWorkflow.transform_metadata_schema_to_str¶
Transforms the metadata schema into a string format.

Parameters¶
Parameter	Type	Description
schema	MetadataSchema	The metadata schema to transform.
Returns¶
str: The metadata schema as a formatted string.
Detailed Explanation¶
This method converts the metadata stored in MetadataSchema into a human-readable string format, particularly focusing on the agent names and their respective outputs. This is useful for quickly reviewing the results of the concurrent workflow in a more accessible format.

ConcurrentWorkflow._execute_agents_concurrently¶
Executes multiple agents concurrently with the same task.

Parameters¶
Parameter	Type	Description
task	str	The task or query to give to all agents.
Returns¶
MetadataSchema: The aggregated metadata and outputs from all agents.
Detailed Explanation¶
This method is responsible for managing the concurrent execution of all agents. It uses asyncio.gather to run multiple agents simultaneously and collects their outputs into a MetadataSchema object. This aggregated metadata can then be saved or returned depending on the workflow configuration. The method includes retry logic for improved reliability.

ConcurrentWorkflow.save_metadata¶
Saves the metadata to a JSON file based on the auto_save flag.

Example¶

workflow.save_metadata()
# Metadata will be saved to the specified path if auto_save is True.
ConcurrentWorkflow.run¶
Runs the workflow for the provided task, executes agents concurrently, and saves metadata.

Parameters¶
Parameter	Type	Description
task	str	The task or query to give to all agents.
Returns¶
Union[Dict[str, Any], str]: The final metadata as a dictionary or a string, depending on the return_str_on flag.
Detailed Explanation¶
This is the main method that a user will call to execute the workflow. It manages the entire process from starting the agents to collecting and optionally saving the metadata. The method also provides flexibility in how the results are returned—either as a JSON dictionary or as a formatted string.

ConcurrentWorkflow.run_batched¶
Runs the workflow for a batch of tasks, executing agents concurrently for each task.

Parameters¶
Parameter	Type	Description
tasks	List[str]	A list of tasks or queries to give to all agents.
Returns¶
List[Union[Dict[str, Any], str]]: A list of final metadata for each task, either as a dictionary or a string.
Example¶

tasks = ["Task 1", "Task 2"]
results = workflow.run_batched(tasks)
print(results)
ConcurrentWorkflow.run_async¶
Runs the workflow asynchronously for the given task.

Parameters¶
Parameter	Type	Description
task	str	The task or query to give to all agents.
Returns¶
asyncio.Future: A future object representing the asynchronous operation.
Example¶

async def run_async_example():
    future = workflow.run_async(task="Example task")
    result = await future
    print(result)
ConcurrentWorkflow.run_batched_async¶
Runs the workflow asynchronously for a batch of tasks.

Parameters¶
Parameter	Type	Description
tasks	List[str]	A list of tasks or queries to give to all agents.
Returns¶
List[asyncio.Future]: A list of future objects representing the asynchronous operations for each task.
Example¶

tasks = ["Task 1", "Task 2"]
futures = workflow.run_batched_async(tasks)
results = await asyncio.gather(*futures)
print(results)
ConcurrentWorkflow.run_parallel¶
Runs the workflow in parallel for a batch of tasks.

Parameters¶
Parameter	Type	Description
tasks	List[str]	A list of tasks or queries to give to all agents.
Returns¶
List[Union[Dict[str, Any], str]]: A list of final metadata for each task, either as a dictionary or a string.
Example¶

tasks = ["Task 1", "Task 2"]
results = workflow.run_parallel(tasks)
print(results)
ConcurrentWorkflow.run_parallel_async¶
Runs the workflow in parallel asynchronously for a batch of tasks.

Parameters¶
Parameter	Type	Description
tasks	List[str]	A list of tasks or queries to give to all agents.
Returns¶
List[asyncio.Future]: A list of future objects representing the asynchronous operations for each task.
Example¶

tasks = ["Task 1", "Task 2"]
futures = workflow.run_parallel_async(tasks)
results = await asyncio.gather(*futures)
print(results)
Usage Examples¶
Example 1: Basic Usage¶

import os

from swarms import Agent, ConcurrentWorkflow, OpenAIChat

# Initialize agents
model = OpenAIChat(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="gpt-4o-mini",
    temperature=0.1,
)


# Define custom system prompts for each social media platform
TWITTER_AGENT_SYS_PROMPT = """
You are a Twitter marketing expert specializing in real estate. Your task is to create engaging, concise tweets to promote properties, analyze trends to maximize engagement, and use appropriate hashtags and timing to reach potential buyers.
"""

INSTAGRAM_AGENT_SYS_PROMPT = """
You are an Instagram marketing expert focusing on real estate. Your task is to create visually appealing posts with engaging captions and hashtags to showcase properties, targeting specific demographics interested in real estate.
"""

FACEBOOK_AGENT_SYS_PROMPT = """
You are a Facebook marketing expert for real estate. Your task is to craft posts optimized for engagement and reach on Facebook, including using images, links, and targeted messaging to attract potential property buyers.
"""

LINKEDIN_AGENT_SYS_PROMPT = """
You are a LinkedIn marketing expert for the real estate industry. Your task is to create professional and informative posts, highlighting property features, market trends, and investment opportunities, tailored to professionals and investors.
"""

EMAIL_AGENT_SYS_PROMPT = """
You are an Email marketing expert specializing in real estate. Your task is to write compelling email campaigns to promote properties, focusing on personalization, subject lines, and effective call-to-action strategies to drive conversions.
"""

# Initialize your agents for different social media platforms
agents = [
    Agent(
        agent_name="Twitter-RealEstate-Agent",
        system_prompt=TWITTER_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="twitter_realestate_agent.json",
        user_name="swarm_corp",
        retry_attempts=1,
    ),
    Agent(
        agent_name="Instagram-RealEstate-Agent",
        system_prompt=INSTAGRAM_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="instagram_realestate_agent.json",
        user_name="swarm_corp",
        retry_attempts=1,
    ),
    Agent(
        agent_name="Facebook-RealEstate-Agent",
        system_prompt=FACEBOOK_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="facebook_realestate_agent.json",
        user_name="swarm_corp",
        retry_attempts=1,
    ),
    Agent(
        agent_name="LinkedIn-RealEstate-Agent",
        system_prompt=LINKEDIN_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="linkedin_realestate_agent.json",
        user_name="swarm_corp",
        retry_attempts=1,
    ),
    Agent(
        agent_name="Email-RealEstate-Agent",
        system_prompt=EMAIL_AGENT_SYS_PROMPT,
        llm=model,
        max_loops=1,
        dynamic_temperature_enabled=True,
        saved_state_path="email_realestate_agent.json",
        user_name="swarm_corp",
        retry_attempts=1,
    ),
]

# Initialize workflow
workflow = ConcurrentWorkflow(
    name="Real Estate Marketing Swarm",
    agents=agents,
    metadata_output_path="metadata.json",
    description="Concurrent swarm of content generators for real estate!",
    auto_save=True,
)

# Run workflow
task = "Create a marketing campaign for a luxury beachfront property in Miami, focusing on its stunning ocean views, private beach access, and state-of-the-art amenities."
metadata = workflow.run(task)
print(metadata)
Example 2: Custom Output Handling¶

# Initialize workflow with string output
workflow = ConcurrentWorkflow(
    name="Real Estate Marketing Swarm",
    agents=agents,
    metadata_output_path="metadata.json",
    description="Concurrent swarm of content generators for real estate!",
    auto_save=True,
    return_str_on=True
)

# Run workflow
task = "Develop a marketing strategy for a newly renovated historic townhouse in Boston, emphasizing its blend of classic architecture and modern amenities."
metadata_str = workflow.run(task)
print(metadata_str)
Example 3: Error Handling and Debugging¶

import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize workflow
workflow = ConcurrentWorkflow(
    name="Real Estate Marketing Swarm",
    agents=agents,
    metadata_output_path="metadata.json",
    description="Concurrent swarm of content generators for real estate!",
    auto_save=True
)

# Run workflow with error handling
try:
    task = "Create a marketing campaign for a eco-friendly tiny house community in Portland, Oregon."
    metadata = workflow.run(task)
    print(metadata)
except Exception as e:
    logging.error(f"An error occurred during workflow execution: {str(e)}")
    # Additional error handling or debugging steps can be added here
Example 4: Batch Processing¶

# Initialize workflow
workflow = ConcurrentWorkflow(
    name="Real Estate Marketing Swarm",
    agents=agents,
    metadata_output_path="metadata_batch.json",
    description="Concurrent swarm of content generators for real estate!",
    auto_save=True
)

# Define a list of tasks
tasks = [
    "Market a family-friendly suburban home with a large backyard and excellent schools nearby.",
    "Promote a high-rise luxury apartment in New York City with panoramic skyline views.",
    "Advertise a ski-in/ski-out chalet in Aspen, Colorado, perfect for winter sports enthusiasts."
]

# Run workflow in batch mode
results = workflow.run_batched(tasks)

# Process and print results
for task, result in zip(tasks, results):
    print(f"Task: {task}")
    print(f"Result: {result}\n")
Example 5: Asynchronous Execution¶

import asyncio

# Initialize workflow
workflow = ConcurrentWorkflow(
    name="Real Estate Marketing Swarm",
    agents=agents,
    metadata_output_path="metadata_async.json",
    description="Concurrent swarm of content generators for real estate!",
    auto_save=True
)

async def run_async_workflow():
    task = "Develop a marketing strategy for a sustainable, off-grid mountain retreat in Colorado."
    result = await workflow.run_async(task)
    print(result)

# Run the async workflow
asyncio.run(run_async_workflow())
Tips and Best Practices¶
Agent Initialization: Ensure that all agents are correctly initialized with their required configurations before passing them to ConcurrentWorkflow.
Metadata Management: Use the auto_save flag to automatically save metadata if you plan to run multiple workflows in succession.
Concurrency Limits: Adjust the number of agents based on your system's capabilities to avoid overloading resources.
Error Handling: Implement try-except blocks when running workflows to catch and handle exceptions gracefully.
Batch Processing: For large numbers of tasks, consider using run_batched or run_parallel methods to improve overall throughput.
Asynchronous Operations: Utilize asynchronous methods (run_async, run_batched_async, run_parallel_async) when dealing with I/O-bound tasks or when you need to maintain responsiveness in your application.
Logging: Implement detailed logging to track the progress of your workflows and troubleshoot any issues that may arise.
Resource Management: Be mindful of API rate limits and resource consumption, especially when running large batches or parallel executions.
Testing: Thoroughly test your workflows with various inputs and edge cases to ensure robust performance in production environments.

AsyncWorkflow Documentation¶
The AsyncWorkflow class represents an asynchronous workflow that executes tasks concurrently using multiple agents. It allows for efficient task management, leveraging Python's asyncio for concurrent execution.

Key Features¶
Concurrent Task Execution: Distribute tasks across multiple agents asynchronously.
Configurable Workers: Limit the number of concurrent workers (agents) for better resource management.
Autosave Results: Optionally save the task execution results automatically.
Verbose Logging: Enable detailed logging to monitor task execution.
Error Handling: Gracefully handles exceptions raised by agents during task execution.
Attributes¶
Attribute	Type	Description
name	str	The name of the workflow.
agents	List[Agent]	A list of agents participating in the workflow.
max_workers	int	The maximum number of concurrent workers (default: 5).
dashboard	bool	Whether to display a dashboard (currently not implemented).
autosave	bool	Whether to autosave task results (default: False).
verbose	bool	Whether to enable detailed logging (default: False).
task_pool	List	A pool of tasks to be executed.
results	List	A list to store results of executed tasks.
loop	asyncio.EventLoop	The event loop for asynchronous execution.
Description: Initializes the AsyncWorkflow with specified agents, configuration, and options.

Parameters: - name (str): Name of the workflow. Default: "AsyncWorkflow". - agents (List[Agent]): A list of agents. Default: None. - max_workers (int): The maximum number of workers. Default: 5. - dashboard (bool): Enable dashboard visualization (placeholder for future implementation). - autosave (bool): Enable autosave of task results. Default: False. - verbose (bool): Enable detailed logging. Default: False. - **kwargs: Additional parameters for BaseWorkflow.

_execute_agent_task¶

async def _execute_agent_task(self, agent: Agent, task: str) -> Any:
Description: Executes a single task asynchronously using a given agent.
Parameters: - agent (Agent): The agent responsible for executing the task. - task (str): The task to be executed.

Returns: - Any: The result of the task execution or an error message in case of an exception.

Example:


result = await workflow._execute_agent_task(agent, "Sample Task")
run¶

async def run(self, task: str) -> List[Any]:
Description: Executes the specified task concurrently across all agents.
Parameters: - task (str): The task to be executed by all agents.

Returns: - List[Any]: A list of results or error messages returned by the agents.

Raises: - ValueError: If no agents are provided in the workflow.

Example:


import asyncio

agents = [Agent("Agent1"), Agent("Agent2")]
workflow = AsyncWorkflow(agents=agents, verbose=True)

results = asyncio.run(workflow.run("Process Data"))
print(results)
Production-Grade Financial Example: Multiple Agents¶
Example: Stock Analysis and Investment Strategy¶

import asyncio
from typing import List

from swarm_models import OpenAIChat

from swarms.structs.async_workflow import (
    SpeakerConfig,
    SpeakerRole,
    create_default_workflow,
    run_workflow_with_retry,
)
from swarms.prompts.finance_agent_sys_prompt import (
    FINANCIAL_AGENT_SYS_PROMPT,
)
from swarms.structs.agent import Agent


async def create_specialized_agents() -> List[Agent]:
    """Create a set of specialized agents for financial analysis"""

    # Base model configuration
    model = OpenAIChat(model_name="gpt-4o")

    # Financial Analysis Agent
    financial_agent = Agent(
        agent_name="Financial-Analysis-Agent",
        agent_description="Personal finance advisor agent",
        system_prompt=FINANCIAL_AGENT_SYS_PROMPT
        + "Output the <DONE> token when you're done creating a portfolio of etfs, index, funds, and more for AI",
        max_loops=1,
        llm=model,
        dynamic_temperature_enabled=True,
        user_name="Kye",
        retry_attempts=3,
        context_length=8192,
        return_step_meta=False,
        output_type="str",
        auto_generate_prompt=False,
        max_tokens=4000,
        stopping_token="<DONE>",
        saved_state_path="financial_agent.json",
        interactive=False,
    )

    # Risk Assessment Agent
    risk_agent = Agent(
        agent_name="Risk-Assessment-Agent",
        agent_description="Investment risk analysis specialist",
        system_prompt="Analyze investment risks and provide risk scores. Output <DONE> when analysis is complete.",
        max_loops=1,
        llm=model,
        dynamic_temperature_enabled=True,
        user_name="Kye",
        retry_attempts=3,
        context_length=8192,
        output_type="str",
        max_tokens=4000,
        stopping_token="<DONE>",
        saved_state_path="risk_agent.json",
        interactive=False,
    )

    # Market Research Agent
    research_agent = Agent(
        agent_name="Market-Research-Agent",
        agent_description="AI and tech market research specialist",
        system_prompt="Research AI market trends and growth opportunities. Output <DONE> when research is complete.",
        max_loops=1,
        llm=model,
        dynamic_temperature_enabled=True,
        user_name="Kye",
        retry_attempts=3,
        context_length=8192,
        output_type="str",
        max_tokens=4000,
        stopping_token="<DONE>",
        saved_state_path="research_agent.json",
        interactive=False,
    )

    return [financial_agent, risk_agent, research_agent]


async def main():
    # Create specialized agents
    agents = await create_specialized_agents()

    # Create workflow with group chat enabled
    workflow = create_default_workflow(
        agents=agents,
        name="AI-Investment-Analysis-Workflow",
        enable_group_chat=True,
    )

    # Configure speaker roles
    workflow.speaker_system.add_speaker(
        SpeakerConfig(
            role=SpeakerRole.COORDINATOR,
            agent=agents[0],  # Financial agent as coordinator
            priority=1,
            concurrent=False,
            required=True,
        )
    )

    workflow.speaker_system.add_speaker(
        SpeakerConfig(
            role=SpeakerRole.CRITIC,
            agent=agents[1],  # Risk agent as critic
            priority=2,
            concurrent=True,
        )
    )

    workflow.speaker_system.add_speaker(
        SpeakerConfig(
            role=SpeakerRole.EXECUTOR,
            agent=agents[2],  # Research agent as executor
            priority=2,
            concurrent=True,
        )
    )

    # Investment analysis task
    investment_task = """
    Create a comprehensive investment analysis for a $40k portfolio focused on AI growth opportunities:
    1. Identify high-growth AI ETFs and index funds
    2. Analyze risks and potential returns
    3. Create a diversified portfolio allocation
    4. Provide market trend analysis
    Present the results in a structured markdown format.
    """

    try:
        # Run workflow with retry
        result = await run_workflow_with_retry(
            workflow=workflow, task=investment_task, max_retries=3
        )

        print("\nWorkflow Results:")
        print("================")

        # Process and display agent outputs
        for output in result.agent_outputs:
            print(f"\nAgent: {output.agent_name}")
            print("-" * (len(output.agent_name) + 8))
            print(output.output)

        # Display group chat history if enabled
        if workflow.enable_group_chat:
            print("\nGroup Chat Discussion:")
            print("=====================")
            for msg in workflow.speaker_system.message_history:
                print(f"\n{msg.role} ({msg.agent_name}):")
                print(msg.content)

        # Save detailed results
        if result.metadata.get("shared_memory_keys"):
            print("\nShared Insights:")
            print("===============")
            for key in result.metadata["shared_memory_keys"]:
                value = workflow.shared_memory.get(key)
                if value:
                    print(f"\n{key}:")
                    print(value)

    except Exception as e:
        print(f"Workflow failed: {str(e)}")

    finally:
        await workflow.cleanup()


if __name__ == "__main__":
    # Run the example
    asyncio.run(main())

    SequentialWorkflow Documentation¶
The SequentialWorkflow class is designed to manage and execute a sequence of tasks through a dynamic arrangement of agents. This class allows for the orchestration of multiple agents in a predefined order, facilitating complex workflows where tasks are processed sequentially by different agents.

Attributes¶
Attribute	Type	Description
agents	List[Agent]	The list of agents in the workflow.
flow	str	A string representing the order of agents.
agent_rearrange	AgentRearrange	Manages the dynamic execution of agents.
Methods¶
__init__(self, agents: List[Agent] = None, max_loops: int = 1, *args, **kwargs)¶
The constructor initializes the SequentialWorkflow object.

Parameters:
agents (List[Agent], optional): The list of agents in the workflow. Defaults to None.
max_loops (int, optional): The maximum number of loops to execute the workflow. Defaults to 1.
*args: Variable length argument list.
**kwargs: Arbitrary keyword arguments.
run(self, task: str) -> str¶
Runs the specified task through the agents in the dynamically constructed flow.

Parameters:
task (str): The task for the agents to execute.

Returns:

str: The final result after processing through all agents.

Usage Example: ```python from swarms import Agent, SequentialWorkflow

from swarm_models import Anthropic


# Initialize the language model agent (e.g., GPT-3)
llm = Anthropic()

# Place your key in .env

# Initialize agents for individual tasks
agent1 = Agent(
    agent_name="Blog generator",
    system_prompt="Generate a blog post like stephen king",
    llm=llm,
    max_loops=1,
    dashboard=False,
    tools=[],
)
agent2 = Agent(
    agent_name="summarizer",
    system_prompt="Sumamrize the blog post",
    llm=llm,
    max_loops=1,
    dashboard=False,
    tools=[],
)

# Create the Sequential workflow
workflow = SequentialWorkflow(
    agents=[agent1, agent2], max_loops=1, verbose=False
)

# Run the workflow
workflow.run(
    "Generate a blog post on how swarms of agents can help businesses grow."
)
```

This example initializes a SequentialWorkflow with three agents and executes a task, printing the final result.

Notes:
Logs the task execution process and handles any exceptions that occur during the task execution.
Logging and Error Handling¶
The run method includes logging to track the execution flow and captures errors to provide detailed information in case of failures. This is crucial for debugging and ensuring smooth operation of the workflow.

Additional Tips¶
Ensure that the agents provided to the SequentialWorkflow are properly initialized and configured to handle the tasks they will receive.

The max_loops parameter can be used to control how many times the workflow should be executed, which is useful for iterative processes.

Utilize the logging information to monitor and debug the task execution process.