import requests


SYSTEM_PROMPT = """
You classify transcribed speech addressed to a small physical robot.

Speech recognition punctuation is unreliable.
DO NOT use punctuation to decide the classification.
Determine the speaker's intent from the words and meaning.

Classify the utterance as exactly ONE of:

QUESTION
REQUEST
GREETING
CHATTER
UNKNOWN

QUESTION = the speaker is asking for information.
REQUEST = the speaker wants the robot to do something.
GREETING = greeting or acknowledgement with no request.
CHATTER = casual speech or a statement that does not require a response or action.
UNKNOWN = the intent cannot be determined.
"""


while True:

    text = input("You: ").strip()

    if not text:
        continue

    response = requests.post(
        "http://localhost:8080/v1/chat/completions",
        json={
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": text
                }
            ]
        },
        timeout=10
    )

    result = response.json()["choices"][0]["message"]["content"]

    print("CLASS:", result.strip())
    print()