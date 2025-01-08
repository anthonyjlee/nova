JSON structured generation
Outlines can make any open source model return a JSON object that follows a structure that is specified by the user. This is useful whenever we want the output of the model to be processed by code downstream: code does not understand natural language but rather the structured language it has been programmed to understand.

There are mostly two reasons why someone would want to get an output formatted as JSON from a LLM:

Parse the answer (e.g. with Pydantic), store it somewhere, return it to a user, etc.
Call a function with the result
Outlines has you covered in both cases! Indeed, to define the structure of the JSON you want the model to follow you can either provide a Pydantic model, or a function. No need to duplicate code!

Using Pydantic
Outlines can infer the structure of the output from a Pydantic model. The result is an instance of the model that contains the values returned by the LLM:


from pydantic import BaseModel

from outlines import models, generate


class User(BaseModel):
    name: str
    last_name: str
    id: int


model = models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = generate.json(model, User)
result = generator(
    "Create a user profile with the fields name, last_name and id"
)
print(result)
# User(name="John", last_name="Doe", id=11)
JSON and whitespaces

By default Outlines prevents the model from generating json with syntactic newlines, tabs, or multiple spaces. The default whitespace_pattern is r"[ ]?". Small models tend to enter an infinite repetition loop if the whitespace_pattern allows infinite spacing. If you would like to allow the model to generate multiple tabs, newlines, and spaces, you can set the whitespace pattern as follows:


generator = generate.json(model, User, whitespace_pattern=r"[\n\t ]*")
Performance

generation.json computes an index that helps Outlines guide generation. This can take some time, but only needs to be done once. If you want to generate several times with the same schema make sure that you only call generate.json once.

Custom types

Outlines provides custom Pydantic types so you do not have to write regular expressions for common types, such as phone numbers or zip codes.

Using a JSON Schema
Instead of a Pydantic model you can pass a string that represents a JSON Schema specification to generate.json:


from pydantic import BaseModel

from outlines import models
from outlines import generate

model = models.transformers("microsoft/Phi-3-mini-4k-instruct")

schema = """
{
  "title": "User",
  "type": "object",
  "properties": {
    "name": {"type": "string"},
    "last_name": {"type": "string"},
    "id": {"type": "integer"}
  },
  "required": ["name", "last_name", "id"]
}
"""

generator = generate.json(model, schema)
result = generator(
    "Create a user profile with the fields name, last_name and id"
)
print(result)
# User(name="John", last_name="Doe", id=11)
From a function's signature
Outlines can infer the structure of the output from the signature of a function. The result is a dictionary, and can be passed directly to the function using the usual dictionary expansion syntax **:


from outlines import models
from outlines import generate

def add(a: int, b: int):
    return a + b

model = models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = generate.json(model, add)
result = generator("Return two integers named a and b respectively. a is odd and b even.")

print(add(**result))
# 3
A great advantage of passing functions directly to specify the structure is that the structure of the LLM will change with the function's definition. No need to change the code at several places!



Named Entity Extraction is a fundamental problem in NLP. It involves identifying and categorizing named entities within a document: people, organization, dates, places, etc. It is usually the first step in a more complex NLP worklow. Here we will use the example of a pizza restaurant that receives orders via their website and need to identify the number and types of pizzas that are being ordered.

Getting LLMs to output the extracted entities in a structured format can be challenging. In this tutorial we will see how we can use Outlines' JSON-structured generation to extract entities from a document and return them in a valid JSON data structure 100% of the time.

As always, we start with initializing the model. We will be using a quantized version of Mistal-7B-v0.1 (we're GPU poor):


import outlines

model = outlines.models.transformers("TheBloke/Mistral-7B-OpenOrca-AWQ", device="cuda")
And we will be using the following prompt template:


@outlines.prompt
def take_order(order):
    """You are the owner of a pizza parlor. Customers \
    send you orders from which you need to extract:

    1. The pizza that is ordered
    2. The number of pizzas

    # EXAMPLE

    ORDER: I would like one Margherita pizza
    RESULT: {"pizza": "Margherita", "number": 1}

    # OUTPUT INSTRUCTIONS

    Answer in valid JSON. Here are the different objects relevant for the output:

    Order:
        pizza (str): name of the pizza
        number (int): number of pizzas

    Return a valid JSON of type "Order"

    # OUTPUT

    ORDER: {{ order }}
    RESULT: """
We now define our data model using Pydantic:


from enum import Enum
from pydantic import BaseModel

class Pizza(str, Enum):
    margherita = "Margherita"
    pepperonni = "Pepperoni"
    calzone = "Calzone"

class Order(BaseModel):
    pizza: Pizza
    number: int
We can now define our generator and call it on several incoming orders:


orders = [
    "Hi! I would like to order two pepperonni pizzas and would like them in 30mins.",
    "Is it possible to get 12 margheritas?"
]
prompts = [take_order(order) for order in orders]

generator = outlines.generate.json(model, Order)

results = generator(prompts)
print(results)
# [Order(pizza=<Pizza.pepperonni: 'Pepperoni'>, number=2),
#  Order(pizza=<Pizza.margherita: 'Margherita'>, number=12)]
There are several ways you could improve this example:

Clients may order several types of pizzas.
Clients may order drinks as well.
If the pizza place has a delivery service we need to extract the client's address and phone number
Clients may specify the time for which they want the pizza. We could then check against a queuing system and reply to them with the estimated delivery time.
How would you change the Pydantic model to account for these use cases?

Generate a synthetic dating profile from a description
In this example we will see how we can use Outlines to generate synthetic data for a dating application. This example was originally contributed by Vibhor Kumar.


from dataclasses import dataclass
from enum import Enum

import torch
import transformers
from pydantic import BaseModel, conlist, constr

import outlines
Defining the profile with Pydantic
Here a dating profile will consist in a biography, a job, a list of interests and two question-answer pairs. The questions are written in advance by the team, and the users are asked to provide an answer:


class QuestionChoice(str, Enum):
    A = "The key to my heart is"
    B = "The first item on my bucket list is"
    C = "Perks of dating me"
    D = "Message me if you also love"
    E = "People would describe me as"
    F = "I can beat you in a game of"

@dataclass
class QuestionAnswer:
    question: QuestionChoice
    answer: str
Users need to provide a short biography, with a minimum of 10 and a maximum of 300 characters. The application also limits job descriptions to 50 characters. In addition to the question-answer pairs, the user is required to provide a list of between 1 and 5 interests:


class DatingProfile(BaseModel):
    bio: constr(str, min_length=10, max_length=300)
    job: constr(str, max_lengt=50)
    interests: conlist(str, min_length=1, max_length=5)  # type: ignore
    qna1: QuestionAnswer
    qna2: QuestionAnswer
Prompt template and examples
We will ask the model to generate profiles from a high-level description:


@dataclass
class Example:
    description: str
    profile: DatingProfile
We will use Outlines' prompt templating abilities to generate the prompt for us. This help clearly separate the general prompting logic from what is specific to an example.


@outlines.prompt
def dating_profile_prompt(description: str, examples: list[Example]):
    """
    You are a world-renowned matchmaker who understands the modern dating
    market. Your job is to generate dating app profiles for male clients
    interested in women based on a provided description. The profiles should be
    authentic, show off their strengths, and maximize their likelihood of
    getting matches on dating apps.  Here are some examples of past clients that
    you have successfully created profiles for:

    {% for example in examples %}
    Description:
    {{ example.description }}
    Profile:
    {{ example.profile }}
    {% endfor %}

    Here is the new client who you need to create a profile for:
    Description: {{ description }}
    Profile:
    """
We will provide the model with several few-shot examples:


samples: list[Example] = [
    Example(
        description="I'm an author and former professional soccer player living in Seattle who publishes popular fiction books. A typical day for me starts by hanging out with my cat, drinking a coffee, and reading as much as I can in a few hours. Then, I'll prepare a quick smoothie before starting to write for a few hours, take a break with soccer or running a few miles, and finally meet friends for dinner at a new, hip restaurant in the evening. Sometimes we go axe-throwing afterwards, or play poker, or watch a comedy show, or visit a dive bar. On my vacations, I travel extensively to countries South America, Europe, and Asia, with the goal of visiting them all!",
        profile=DatingProfile(
            bio="Adventurer, dreamer, author, and soccer enthusiast. Life’s too short to waste time so I make the most of each day by exploring new places and playing with my friends on the pitch. What’s your favorite way to get out and have fun?",
            job="Famous Soccer Player -> Famous Author",
            interests=["Soccer", "Travel", "Friends", "Books", "Fluffy Animals"],
            qna1=QuestionAnswer(
                question=QuestionChoice.B, answer="swim in all seven oceans!"
            ),
            qna2=QuestionAnswer(
                question=QuestionChoice.E,
                answer="fun-loving, adventurous, and a little bit crazy",
            ),
        ),
    ),
    Example(
        description="I run my company and build houses for a living. I'm a big fan of the outdoors and love to go hiking, camping, and fishing. I don't like video games, but do like to watch movies. My love language is home-cooked food, and I'm looking for someone who isn't afraid to get their hands dirty.",
        profile=DatingProfile(
            bio="If you're looking for a Montana man who loves to get outdoors and hunt, and who's in-tune with his masculinity then I'm your guy!",
            job="House Construction Manager / Entrepreneur",
            interests=["Hunting", "Hiking", "The outdoors", "Home-cooked food"],
            qna1=QuestionAnswer(question=QuestionChoice.A, answer="food made at home"),
            qna2=QuestionAnswer(
                question=QuestionChoice.C,
                answer="having a man in your life who can fix anything",
            ),
        ),
    ),
    Example(
        description="I run my own Youtube channel with 10M subscribers. I love working with kids, and my audience skews pretty young too. In my free time, I play Fortnite and Roblox. I'm looking for someone who is also a gamer and likes to have fun. I'm learning Japanese in my free time as well as how to cook.",
        profile=DatingProfile(
            bio="Easy on the eyes (find me on Youtube!) and great with kids. What more do you need?",
            job="Youtuber 10M+ subscribers",
            interests=["Kids", "Gaming", "Japanese"],
            qna1=QuestionAnswer(question=QuestionChoice.D, answer="anime and gaming!"),
            qna2=QuestionAnswer(question=QuestionChoice.F, answer="Fortnite, gg ez"),
        ),
    ),
]
Load the model
We will use Mosaic's MPT-7B model (requires 13GB of GPU memory) which can fit on a single GPU with a reasonable context window. We initialize it with Outlines:


config = transformers.AutoConfig.from_pretrained(
    "mosaicml/mpt-7b-8k-instruct", trust_remote_code=True
)
config.init_device = "meta"
model = outlines.models.transformers(
    model_name="mosaicml/mpt-7b-8k-instruct",
    device="cuda",
    model_kwargs={
        "config": config,
        "trust_remote_code": True,
        "torch_dtype": torch.bfloat16,
        "device_map": {"": 0},
    },
)
JSON-structured generation of profiles
We will now generate a dating profile from a textual description of oneself:


new_description = """I'm a laid-back lawyer who spends a lot of his free-time
gaming. I work in a corporate office, but ended up here after the start-up  I
cofounded got acquired, so still play ping pong with my cool coworkers every
day.  I have a bar at home where I make cocktails, which is great for
entertaining  friends. I secretly like to wear suits and get a new one tailored
every few  months. I also like weddings because I get to wear those suits, and
it's  a good excuse for a date. I watch the latest series because I'm paying,
with my hard-earned money, for every streaming service."""

prompt = dating_profile_prompt(new_description, samples)
profile = outlines.generate.json(model, DatingProfile)(prompt)
parsed_profile = DatingProfile.model_validate_json(profile)
Results
Here are a couple of results:


{
    "bio": """I'm an ambitious lawyer with a casual and fashionable style. I love
    games and sports, but my true passion is preparing refreshing cocktails at
    home and dressing to the nines at weddings. I'm currently looking for a woman
    to show a good time to and get a kiss on the opulent suit I just had made.
    Send resume to this inbox.""",
    "job": "Lawyer",
    "interests":
    [
        "Stylish guys",
        "Gaming",
        "Ping pong",
        "Cocktails",
        "Weddings"
    ],
    "qna1":
    {
        "question": "The first item on my bucket list is",
        "answer": "be married and have a family."
    },
    "qna2":
    {
        "question": "People would describe me as",
        "answer": "charming, stylish, and funny."
    }
}

{
    "bio": """I’m a sexy lawyer with time on my hands. I love to game and
    play ping pong, but the real reason you should swipe to the right
    is because I look great in a suit. Who doesn’t love a man in a
    suit? Just saying. Send me a message if you think it’s time to take
    your dating life to the next level.""",
    "job": "Lawyer",
    "interests":
    [
        "Gaming",
        "Ping Pong",
        "Tailored Suits",
        "Weddings",
        "Streaming Services"
    ],
    "qna1":
    {
        "question": "The first item on my bucket list is",
        "answer": "simulate space but stay alive for as long as possible"
    },
    "qna2":
    {
        "question": "People would describe me as",
        "answer": "easy-going, a little nerdy but with a mature essence"
    }
}Build perspective-taking agents with SimToM
Prompting strategies like Chain-of-Thought (CoT) can improve LLMs' reasoning capabilities. However, they underwhelm in tasks that require keeping track of inconsistent world states. SimToM proposes a simple, two-stage prompting framework for LLMs inspired by Simulation Theory. The authors showed that this approach outperforms zero-shot prompting and CoT on ToMI and BigToM, two benchmarks with Theory of Mind questions.

In this example, we will implement SimToM with a few lines of code using Outlines' prompt templating and structured generation capabilities.

How SimToM works
SimToM calls an LLM with two consecutive prompts:

Perspective-taking: The first prompt receives a story and a character. The goal is to understand the situation based on the character's point of view and filter out the rest of the story.
Question-Answering: The second prompt receives the character's point of view from the previous step and tasks the LLM to answer a question using that context.
Figure 2 in the paper

Outlines implementation
To implement SimToM with Outlines, we will need to:

Write the prompts with prompt functions.
Define the JSON object each prompt will return using Pydantic.
Generate responses with a Mistral model using the transformers integration.
Let's dive into it!

Using Prompt Functions
With Outlines, you can write your prompts as Python functions by adding the @outlines.prompt decorator. The prompt template is contained in their docstring, and their arguments correspond to variables used in the prompt.

The authors have shared their code, prompts and data in this GitHub repository. Below, we define in Outlines the prompts they used for the ToMI dataset:


import outlines


@outlines.prompt
def perspective_taking(story: str, character: str) -> None:
    """<s>[INST] The following is a sequence of events about some characters, that takes place in multiple locations.
    Your job is to output only the events that the specified character, {{character}}, knows about.

    Here are a few rules:
    1. A character knows about all events that they do.
    2. If a character is in a certain room/location, that character knows about all other events that happens in the room. This includes other characters leaving or exiting the location, the locations of objects in that location, and whether somebody moves an object to another place.
    3. If a character leaves a location, and is NOT in that location, they no longer know about any events that happen within that location. However, they can re-enter the location.

    Story: {{story}}
    What events does {{character}} know about? Only output the events according to the above rules, do not provide an explanation. [/INST]""" # noqa

@outlines.prompt
def simulation(events: list, name: str, question: str) -> None:
    """<s>[INST] {% for event in events %}
    {{event}}
    {% endfor %}
    You are {{name}}.
    Based on the above information, answer the following question:
    {{question}}
    You must choose one of the above choices, do not say there is not enough information. Answer with a single word, do not output anything else. [/INST]""" # noqa
JSON Structured Generation
Outlines guarantees that the LLM will return a valid JSON object, which we can specify as a Pydantic model.

We will need two Pydantic models for SimToM, one for each prompt:


from pydantic import BaseModel, Field
from typing import List


class PerspectiveTaking(BaseModel):
    """This is for the first prompt."""
    character: str = Field(description="The character we extract the events for.")
    events: List[str] = Field(description="All events that the character knows about.")


class Simulation(BaseModel):
    """This is for the second prompt."""
    answer: str
Calling an LLM
Let's try SimToM with an example from the ToMI dataset:


story = """
1 Aria entered the front_yard.
2 Aiden entered the front_yard.
3 The grapefruit is in the green_bucket.
4 Aria moved the grapefruit to the blue_container.
5 Aiden exited the front_yard.
6 Noah entered the playroom.
"""
question = "7 Where was the grapefruit at the beginning?"
character = "Aria"
We load Mistral-7B-Instruct-v0.3, create the prompt using the template we defined earlier, and generate a structured response. As a reminder, the goal of the first call is to get all the events a character, Aria, knows about.


# Load an LLM from Hugging Face
MODEL_NAME = "mistral-community/Mistral-7B-Instruct-v0.3"
model = outlines.models.transformers(MODEL_NAME, device="cuda")

perspective_prompt = perspective_taking(story=story, character=character)

# Call Mistral 7B with the first prompt
generator = outlines.generate.json(model, PerspectiveTaking)
perspective = generator(perspective_prompt)

print(perspective.model_dump())
# {'character': 'Aria', 'events': ['1 Aria entered the front_yard.', '3 The grapefruit is in the green_bucket.', '4 Aria moved the grapefruit to the blue_container.']}
Not bad! We will now generate the second prompt with those events.


sim_prompt = simulation(events=perspective.events, name=character, question=question)

# Call Mistral 7B with the second prompt
generator = outlines.generate.json(model, Simulation)
result = generator(sim_prompt)

print(result.model_dump())
# {'answer': 'green_bucket'}
And this is it! SimToM could be useful in agentic workflows, where agents must act based on what they know, not all available information. One caveat of SimToM is that the perspective-taking step may remove important information, leading to wrong results. As the authors note in their paper, it can feature as a simple and effective baseline for evaluating LLMs on Theory of Mind reasoning tasks.

Structured Generation Workflow: Generating Synthetic Phone Numbers
This is a condensed version of Coding for Structured Generation with LLMs.

For this example we're going to be building an LLM program to generate synthetic data in the form of realistic looking phone numbers for Washington State. Using an LLM for this task is a bit overkill since we could just as easily accomplish this with a tool like Faker, but this example still serves as a useful way to demonstrate a workflow for using structured generation.

Unstructured approach
Before diving into how to use structure generation for this task let's start with an unstructured example. We begin by loading our model:


import outlines

model_name = 'microsoft/Phi-3-mini-4k-instruct'
model = outlines.models.transformers(model_name)
Next we need a prompt for this model. Since we're focusing on structured generation, we won't be engaging in any form of "prompt hacking" and will be leaving this prompt untouched for the rest of this example.


tokenizer = AutoTokenizer.from_pretrained(model_name)

messages_phone = [
            {"role": "user", "content": """
            Please generate a realistic phone number for Washington State in the following format

            (555) 555-5555

            """}
]

# This allows us to properly format our prompt for
# Phi-3 Mini's 'Instruct' interface.
prompt_phone = tokenizer.apply_chat_template(messages_phone, tokenize=False)
With our prompt ready we can now generate 10 example phone numbers


phone_generator_unstruct = outlines.generate.text(model)
for _ in range(10):
    print(phone_generator_unstruct(prompt_phone,max_tokens=12))
I'd be happy to help you generate a realistic phone\ I cannot generate a real phone number as I'm just\ I'm an AI and don't have the ability\ Sure! Here is a randomly generated phone number in the format\ Here's a phone number that fits the format for a\ In Washington State, phone numbers typically have a three-dig\ Here are a few examples of phone numbers that could be considered\ I'd be happy to help generate a realistic phone number\ I'd be happy to help you generate a random phone\ Based on the format you provided, a realistic phone number for\

As we can see, none of these outputs are even phone numbers!

Let's see if we can improve this using structured generation.

The Structured Generation Workflow
In order to solve this problem we're going to introduce a Structured Generation Workflow outlined in this image:

"Visual of Structured Generation Workflow"

Let's step through this:

Real example
We start with a real example phone number, in this case for the Seattle Public Library, that we can use to verify the structure we are creating.


phone_number = "(206) 386-4636"
For a simple example like this, we'll just be using a single phone number, for more complex examples it can be helpful to have more examples.

Draft Structure
The next step in the process is for use to define a simple regex that we feel correctly models our real data.


phone_regex_1 = r'\([0-9]{3}\) [0-9]{3}-[0-9]{4}'
Next we need to validate this regex against our real data.

Validate by matching examples
Whenever writing non-trivial code with structured generation it is essential that you first validate the code against your real data example(s).

We'll start with a simple method of validation: just checking that our regex matches the data.


import re
re.match(phone_regex_1, phone_number)

# <re.Match object; span=(0, 14), match='(206) 386-4636'>
Now that we have a match, we can move on to generating structured output!

Generate Structure
We're ready to see if structured generation can make an improvement over our initial unstructured approach:


phone_generator_v1 = outlines.generate.regex(model, phone_regex_1)
for _ in range(10):
    print(phone_generator_v1(prompt_phone))
(206) 555-1234\ (206) 555-1234\ (206) 555-1234\ (206) 555-1234\ (206) 555-1234\ (206) 555-1234\ (206) 123-4567\ (206) 555-1234\ (206) 555-1234\ (206) 555-1234

At least we have phone numbers! But I think we can do better!

Inspect output
In this case the model did create phone numbers and, impressively, got the area code correct. So using structured generation did improve things. However these numbers are pretty boring. Let's improve that structure!

Iteration
We've walked through the loop once, so we can go quickly now through each iteration.

We start by improving our structure:


phone_regex_2 = r'\([0-9]{3}\) [2-46-9]{3}-[02-9]{4}'
Before rushing to another round of generation, let's validate this new regex. We'll add just a bit more sophistication over our last check:


re.match(phone_regex_2, phone_number)[0] == phone_number
# True
Now that we've validated, let's generate with this new regex!

phone_generator_v2 = outlines.generate.regex(model,
                                             phone_regex_2)
for _ in range(10):
    print(phone_generator_v2(prompt_phone))
(206) 867-5309\ (206) 666-7777\ (206) 444-3333\ (206) 444-3333\ (206) 943-2222\ (206) 323-6789\ (206) 444-3333\ (206) 867-5309\ (206) 466-2255\ (206) 222-3333

Better, but I don't like those repeated sequences. Like good software developers, let's iterate again!

Reiteration - with debugging
Here's a fancier regex that should give us more interesting results:


phone_regex_3_error = r'\([0-9]{3}\) [2-4][7-9][4-6]-[3-6][2-8][1-4]'
This looks good to me, but there's a subtle bug, that's why we always need to validate our structure against real data. This time we'll make our validator do a bit more work to verify the correct string is matched:


if not re.match(phone_regex_3_error, phone_number):
    print("Regex fails match")
else:
    matched_string = re.match(phone_regex_3_error, phone_number)[0]
    if matched_string == phone_number:
    print("Successful match")
    else:
    print(f"Error {matched_string} != {phone_number}")
This prints out:
Error (206) 386-463 != (206) 386-4636

Ah! We were missing the last digit, let's fix that and regenerate:


phone_regex_3_fixed = r'\([0-9]{3}\) [2-4][7-9][4-6]-[3-6][2-8][1-4][6-9]'
phone_generator_v3 = outlines.generate.regex(model,
                                             phone_regex_3_fixed)
for _ in range(10):
    print(phone_generator_v3(prompt_phone))
(206) 494-3216\ (206) 374-6218\ (206) 494-3337\ (206) 476-3216\ (206) 484-3548\ (206) 495-3218\ (206) 494-5517\ (206) 375-4636\ (206) 384-6216\ (206) 385-6218

Much better!

Now you've seen a quick example of the structured generation workflow that can be used at the basis for building and iteration on much larger structured generation tasks!

Serve with vLLM
Would rather not self-host?

If you want to get started quickly with JSON-structured generation you can call instead .json, a .txt API that guarantees valid JSON.

Outlines can be deployed as an LLM service using the vLLM inference engine and a FastAPI server. vLLM is not installed by default so will need to install Outlines with:


pip install outlines[serve]
You can then start the server with:


python -m outlines.serve.serve --model="microsoft/Phi-3-mini-4k-instruct"
This will by default start a server at http://127.0.0.1:8000 (check what the console says, though). Without the --model argument set, the OPT-125M model is used. The --model argument allows you to specify any model of your choosing.

To run inference on multiple GPUs you must pass the --tensor-parallel-size argument when initializing the server. For instance, to run inference on 2 GPUs:


python -m outlines.serve.serve --model="microsoft/Phi-3-mini-4k-instruct" --tensor-parallel-size 2
Alternative Method: Via Docker
You can install and run the server with Outlines' official Docker image using the command


docker run -p 8000:8000 outlinesdev/outlines --model="microsoft/Phi-3-mini-4k-instruct"
Querying Endpoint
You can then query the model in shell by passing a prompt and either

a JSON Schema specification or
a Regex pattern
with the schema or regex parameters, respectively, to the /generate endpoint. If both are specified, the schema will be used. If neither is specified, the generated text will be unconstrained.

For example, to generate a string that matches the schema {"type": "string"} (any string):


curl http://127.0.0.1:8000/generate \
    -d '{
        "prompt": "What is the capital of France?",
        "schema": {"type": "string", "maxLength": 5}
        }'
To generate a string that matches the regex (-)?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][+-][0-9]+)? (a number):


curl http://127.0.0.1:8000/generate \
    -d '{
        "prompt": "What is Pi? Give me the first 15 digits: ",
        "regex": "(-)?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-][0-9]+)?"
        }'
Instead of curl, you can also use the requests library from another python program.

Please consult the vLLM documentation for details on additional request parameters. You can also read the code in case you need to customize the solution to your needs.

Serve with LM Studio
Would rather not self-host?

If you want to get started quickly with JSON-structured generation you can call instead .json, a .txt API that guarantees valid JSON.

LM Studio is an application that runs local LLMs. It flexibly mixes GPU and CPU compute in hardware-constrained environments.

As of LM Studio 0.3.4, it natively supports Outlines for structured text generation, using an OpenAI-compatible endpoint.

Setup
Install LM Studio by visiting their downloads page.
Enable the LM Studio server functionality.
Download a model.
Install Python dependencies.

pip install pydantic openai
Calling the server
By default, LM Studio will serve from http://localhost:1234. If you are serving on a different port or host, make sure to change the base_url argument in OpenAI to the relevant location.


class Testing(BaseModel):
    """
    A class representing a testing schema.
    """
    name: str
    age: int

openai_client = openai.OpenAI(
    base_url="http://0.0.0.0:1234/v1",
    api_key="dopeness"
)

# Make a request to the local LM Studio server
response = openai_client.beta.chat.completions.parse(
    model="hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF",
    messages=[
        {"role": "system", "content": "You are like so good at whatever you do."},
        {"role": "user", "content": "My name is Cameron and I am 28 years old. What's my name and age?"}
    ],
    response_format=Testing
)
You should receive a ParsedChatCompletion[Testing] object back:


ParsedChatCompletion[Testing](
    id='chatcmpl-3hykyf0fxus7jc90k6gwlw',
    choices=[
        ParsedChoice[Testing](
            finish_reason='stop',
            index=0,
            logprobs=None,
            message=ParsedChatCompletionMessage[Testing](
                content='{ "age": 28, "name": "Cameron" }',
                refusal=None,
                role='assistant',
                function_call=None,
                tool_calls=[],
                parsed=Testing(name='Cameron', age=28)
            )
        )
    ],
    created=1728595622,
    model='lmstudio-community/Phi-3.1-mini-128k-instruct-GGUF/Phi-3.1-mini-128k-instruct-Q4_K_M.gguf',
    object='chat.completion',
    service_tier=None,
    system_fingerprint='lmstudio-community/Phi-3.1-mini-128k-instruct-GGUF/Phi-3.1-mini-128k-instruct-
Q4_K_M.gguf',
    usage=CompletionUsage(
        completion_tokens=17,
        prompt_tokens=47,
        total_tokens=64,
        completion_tokens_details=None,
        prompt_tokens_details=None
    )
)
You can retrieve your Testing object with


response.choices[0].message.parsed

Structured generation
The first step towards reliability of systems that include large language models is to ensure that there is a well-defined interface between their output and user-defined code. Outlines provides ways to control the generation of language models to make their output more predictable.

Multiple choices
You can reduce the completion to a choice between multiple possibilities:

import outlines

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

prompt = """You are a sentiment-labelling assistant.
Is the following review positive or negative?

Review: This restaurant is just awesome!
"""

generator = outlines.generate.choice(model, ["Positive", "Negative"])
answer = generator(prompt)
You can also pass these choices through en enum:

from enum import Enum

import outlines

class Sentiment(str, Enum):
    positive = "Positive"
    negative = "Negative"

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

prompt = """You are a sentiment-labelling assistant.
Is the following review positive or negative?

Review: This restaurant is just awesome!
"""

generator = outlines.generate.choice(model, Sentiment)
answer = generator(prompt)
Type constraint
You can instruct the model to only return integers or floats:

import outlines

model = outlines.models.transformers("WizardLM/WizardMath-7B-V1.1")

prompt = "<s>result of 9 + 9 = 18</s><s>result of 1 + 2 = "
answer = outlines.generate.format(model, int)(prompt)
print(answer)
# 3

prompt = "sqrt(2)="
generator = outlines.generate.format(model, float)
answer = generator(prompt, max_tokens=10)
print(answer)
# 1.41421356
Efficient regex-structured generation
Outlines also comes with fast regex-structured generation. In fact, the choice and format functions above all use regex-structured generation under the hood:

import outlines

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

prompt = "What is the IP address of the Google DNS servers? "

generator = outlines.generate.text(model)
unstructured = generator(prompt, max_tokens=30)

generator = outlines.generate.regex(
    model,
    r"((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)",
)
structured = generator(prompt, max_tokens=30)

print(unstructured)
# What is the IP address of the Google DNS servers?
#
# Passive DNS servers are at DNS servers that are private.
# In other words, both IP servers are private. The database
# does not contain Chelsea Manning

print(structured)
# What is the IP address of the Google DNS servers?
# 2.2.6.1
Unlike other libraries, regex-structured generation in Outlines is almost as fast as non-structured generation.

Efficient JSON generation following a Pydantic model
Outlines allows to guide the generation process so the output is guaranteed to follow a JSON schema or Pydantic model:

from enum import Enum
from pydantic import BaseModel, constr

import outlines
import torch


class Weapon(str, Enum):
    sword = "sword"
    axe = "axe"
    mace = "mace"
    spear = "spear"
    bow = "bow"
    crossbow = "crossbow"


class Armor(str, Enum):
    leather = "leather"
    chainmail = "chainmail"
    plate = "plate"


class Character(BaseModel):
    name: constr(max_length=10)
    age: int
    armor: Armor
    weapon: Weapon
    strength: int


model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")

# Construct structured sequence generator
generator = outlines.generate.json(model, Character)

# Draw a sample
seed = 789001

character = generator("Give me a character description", seed=seed)

print(repr(character))
# Character(name='Anderson', age=28, armor=<Armor.chainmail: 'chainmail'>, weapon=<Weapon.sword: 'sword'>, strength=8)

character = generator("Give me an interesting character description")

print(repr(character))
# Character(name='Vivian Thr', age=44, armor=<Armor.plate: 'plate'>, weapon=<Weapon.crossbow: 'crossbow'>, strength=125)
The method works with union types, optional types, arrays, nested schemas, etc. Some field constraints are not supported yet, but everything else should work.

Efficient JSON generation following a JSON Schema
Sometimes you just want to be able to pass a JSON Schema instead of a Pydantic model. We've got you covered:

import outlines

schema = '''{
    "title": "Character",
    "type": "object",
    "properties": {
        "name": {
            "title": "Name",
            "maxLength": 10,
            "type": "string"
        },
        "age": {
            "title": "Age",
            "type": "integer"
        },
        "armor": {"$ref": "#/definitions/Armor"},
        "weapon": {"$ref": "#/definitions/Weapon"},
        "strength": {
            "title": "Strength",
            "type": "integer"
        }
    },
    "required": ["name", "age", "armor", "weapon", "strength"],
    "definitions": {
        "Armor": {
            "title": "Armor",
            "description": "An enumeration.",
            "enum": ["leather", "chainmail", "plate"],
            "type": "string"
        },
        "Weapon": {
            "title": "Weapon",
            "description": "An enumeration.",
            "enum": ["sword", "axe", "mace", "spear", "bow", "crossbow"],
            "type": "string"
        }
    }
}'''

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
generator = outlines.generate.json(model, schema)
character = generator("Give me a character description")
Using context-free grammars to guide generation
Formal grammars rule the world, and Outlines makes them rule LLMs too. You can pass any context-free grammar in the EBNF format and Outlines will generate an output that is valid to this grammar:

import outlines

arithmetic_grammar = """
    ?start: expression

    ?expression: term (("+" | "-") term)*

    ?term: factor (("*" | "/") factor)*

    ?factor: NUMBER
           | "-" factor
           | "(" expression ")"

    %import common.NUMBER
"""

model = outlines.models.transformers("WizardLM/WizardMath-7B-V1.1")
generator = outlines.generate.cfg(model, arithmetic_grammar)
sequence = generator("Alice had 4 apples and Bob ate 2. Write an expression for Alice's apples:")

print(sequence)
# (8-2)
This was a very simple grammar, and you can use outlines.generate.cfg to generate syntactically valid Python, SQL, and much more than this. Any kind of structured text, really. All you have to do is search for "X EBNF grammar" on the web, and take a look at the Outlines grammars module.

Open functions
Outlines can infer the structure of the output from the signature of a function. The result is a dictionary, and can be passed directly to the function using the usual dictionary expansion syntax **:

import outlines


def add(a: int, b: int):
    return a + b

model = outlines.models.transformers("WizardLM/WizardMath-7B-V1.1")
generator = outlines.generate.json(model, add)
result = generator("Return json with two integers named a and b respectively. a is odd and b even.")

print(add(**result))
# 3
A great advantage of passing functions directly to specify the structure is that the structure of the LLM will change with the function's definition. No need to change the code at several places!

You can also embed various functions into an enum to generate params:

from enum import Enum
from functools import partial

import outlines


def add(a: int, b: int) -> int:
    return a + b

def mul(c: float, d: float) -> float:
    return c * d

class Operation(Enum):
    add = partial(add)
    mul = partial(mul)

model = outlines.models.transformers("WizardLM/WizardMath-7B-V1.1")
generator = outlines.generate.json(model, add)
result = generator("Return json with two float named c and d respectively. c is negative and d greater than 1.0.")

print(result)
# {'c': -3.14, 'd': 1.5}
Prompting
Building prompts can get messy. Outlines makes it easier to write and manage prompts by encapsulating templates inside "template functions".

These functions make it possible to neatly separate the prompt logic from the general program logic; they can be imported from other modules and libraries.

Template functions require no superfluous abstraction, they use the Jinja2 templating engine to help build complex prompts in a concise manner:

import outlines

examples = [
    ("The food was disgusting", "Negative"),
    ("We had a fantastic night", "Positive"),
    ("Recommended", "Positive"),
    ("The waiter was rude", "Negative")
]

@outlines.prompt
def labelling(to_label, examples):
    """You are a sentiment-labelling assistant.

    {% for example in examples %}
    {{ example[0] }} // {{ example[1] }}
    {% endfor %}
    {{ to_label }} //
    """

model = outlines.models.transformers("microsoft/Phi-3-mini-4k-instruct")
prompt = labelling("Just awesome", examples)
answer = outlines.generate.text(model)(prompt, max_tokens=100)