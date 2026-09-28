from src import openai_realtime
from src import moonshine


def open(question=None):
    """Open the online OpenAI real-time voice conversation."""

    print("BIG BRAIN: Opening...")

    moonshine.pause()

    try:
        openai_realtime.open(question)

    finally:
        moonshine.resume()

    print("BIG BRAIN: Closed.")