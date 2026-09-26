from dotenv import load_dotenv
from openai import OpenAI

from robot_functions import exit_ai_mode


load_dotenv()

client = OpenAI()


def handle_task(question, conversation_history=None):

    if conversation_history is None:
        conversation_history = []

    history_text = ""

    for turn in conversation_history:
        history_text += (
            f"{turn['role'].upper()}: "
            f"{turn['text']}\n"
        )

    prompt = f"""
Here is the recent conversation between the user and Robot:

{history_text}

The user's current request is:

USER: {question}

Answer the current request using the recent conversation for context where relevant.

Resolve references such as "it", "that", "the answer", "those",
and similar phrases from the conversation when possible.

You have access to web search and Robot application functions.

If the user's request requires a physical action, application action,
device control, or other real-world action, only claim that the action
has been performed if you successfully call an available function
that performs it.

If no suitable function is available, do not pretend or imply that
the action was performed. Instead, briefly tell the user that Robot
cannot perform that action yet.

Use web search when the question requires current, recent, changing,
or otherwise up-to-date information.

For questions that can be answered reliably without the web,
do not search unnecessarily.

If the user wants to end the AI conversation, leave AI mode,
return to local control, stop talking with the AI, or otherwise
finish the conversation, call exit_ai_mode.

Interpret this naturally. The user does not need to use a specific phrase.

Your answer will be passed back to a voice assistant and spoken aloud.

Keep normal answers short and conversational.
Usually answer in 1 to 3 sentences.
Do not use headings, bullet points, markdown, or long explanations.
Do not read URLs or citations aloud.
Give the useful answer directly.
"""

    response = client.responses.create(
        model="gpt-5.4",

        tools=[
            {
                "type": "web_search"
            },
            {
                "type": "function",
                "name": "exit_ai_mode",
                "description": (
                    "Exit the live AI conversation and return Robot "
                    "to its local Vosk command-listening mode."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                    "additionalProperties": False
                },
                "strict": True
            }
        ],

        tool_choice="auto",
        input=prompt
    )

    for item in response.output:

        if (
            item.type == "function_call"
            and item.name == "exit_ai_mode"
        ):
            return exit_ai_mode()

    return response.output_text
