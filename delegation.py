from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


def handle_task(question, conversation_history=None):

    if conversation_history is None:
        conversation_history = []

    # Build recent conversation context
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

You have access to web search.

Use web search when the question requires current, recent, changing,
or otherwise up-to-date information.

For questions that can be answered reliably without the web,
do not search unnecessarily.

Your answer will be passed back to a voice assistant and spoken aloud.

Keep the answer short and conversational.
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
            }
        ],

        input=prompt
    )

    return response.output_text
