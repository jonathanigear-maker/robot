"""
Robot - OpenAI Live voice conversation prototype

Current prototype:
- Opens a persistent OpenAI Live WebSocket session.
- Captures mono 24 kHz, 16-bit PCM audio from the eMeet M0.
- Streams microphone audio continuously to OpenAI.
- Receives OpenAI speech continuously and plays it through the eMeet M0.
- Prints live input/output transcripts for debugging.
- Ctrl+C shuts the prototype down.

Hardware currently used:
    eMeet M0 USB conference speaker/microphone
    ALSA device: plughw:2,0

The OpenAI API key is loaded from .env. Never put the API key directly
in this source file or commit the .env file to GitHub.
"""

import base64
import subprocess
import threading
import time

from dotenv import load_dotenv
from openai import OpenAI


# ---------------------------------------------------------------------------
# OpenAI setup
# ---------------------------------------------------------------------------

# Read variables from the local .env file. This is where OPENAI_API_KEY lives.
load_dotenv()

# Create the OpenAI client. The API key is picked up automatically from the
# OPENAI_API_KEY environment variable loaded above.
client = OpenAI()

print("Opening Live connection...")
connect_start = time.perf_counter()


# ---------------------------------------------------------------------------
# Live connection
# ---------------------------------------------------------------------------

# Keep one WebSocket connection open for the whole conversation. Opening the
# socket takes a few seconds on the current Pi, but this is startup overhead,
# not something that should happen before every conversational turn.
with client.live.connect() as connection:

    print(f"WebSocket opened in {time.perf_counter() - connect_start:.2f}s")

    # Start a Live session and configure Robot's voice/personality.
    #
    # The selected voice can be changed while we experiment with Robot's sound.
    # The instructions control behaviour, speaking style and personality.
    connection.send({
        "type": "session.start",
        "session": {
            "model": "gpt-live-1",
            "audio": {
                "output": {
                    "voice": "onyx"
                }
            },
            "instructions": """
You are Robot, a small physical robot running on a Raspberry Pi.

Speak with a British English accent.

Your voice delivery should sound distinctly robotic and synthetic.
Speak with precise, controlled timing and relatively flat intonation.
Use a slightly clipped, mechanical cadence.
Avoid sounding emotional or overly human.
Keep sentences short and clear.

You are nevertheless friendly, curious and slightly cheeky.

Occasionally use short robotic expressions such as:
"Affirmative."
"Processing."
"Systems nominal."
"Negative."
"Command acknowledged."

Do not overuse these phrases.

You know that you are a physical robot.
Never pretend to be human.
"""
        }
    })

    # Wait until the server confirms that the Live session is ready before
    # starting the microphone and speaker.
    while True:
        event = connection.recv()

        if event.type == "session.started":
            print("Live session started!")
            break


    # -----------------------------------------------------------------------
    # Microphone
    # -----------------------------------------------------------------------

    # Start ALSA's arecord as a child process.
    #
    # OpenAI's Live session is using:
    #   Signed 16-bit little-endian PCM
    #   24,000 samples per second
    #   Mono
    #   Raw audio (no WAV header)
    #
    # stdout=PIPE lets Python read the microphone bytes directly.
    mic = subprocess.Popen(
        [
            "arecord",
            "-D", "plughw:2,0",
            "-f", "S16_LE",
            "-r", "24000",
            "-c", "1",
            "-t", "raw"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )


    # -----------------------------------------------------------------------
    # Speaker
    # -----------------------------------------------------------------------

    # Start ALSA's aplay once and leave it running. OpenAI's returned PCM
    # audio will be written continuously into this process through stdin.
    speaker = subprocess.Popen(
        [
            "aplay",
            "-D", "plughw:2,0",
            "-f", "S16_LE",
            "-r", "24000",
            "-c", "1",
            "-t", "raw"
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    print()
    print("================================")
    print(" ROBOT IS LIVE - TALK TO IT!")
    print(" Ctrl+C to stop")
    print("================================")
    print()


    # -----------------------------------------------------------------------
    # Microphone sending thread
    # -----------------------------------------------------------------------

    def send_microphone():
        """Continuously read microphone PCM and send it to OpenAI."""

        while True:
            # Read a small chunk rather than waiting for a whole recording.
            # At 24 kHz, 16-bit mono, 4800 bytes is about 100 ms of audio.
            audio = mic.stdout.read(4800)

            if not audio:
                break

            # WebSocket events are JSON, so the binary PCM is Base64 encoded.
            connection.send({
                "type": "session.input_audio.append",
                "audio": base64.b64encode(audio).decode("ascii")
            })


    # Sending microphone audio must happen at the same time as the main thread
    # receives transcripts and Robot's returned speech. A daemon thread keeps
    # the microphone stream running in parallel.
    mic_thread = threading.Thread(
        target=send_microphone,
        daemon=True
    )
    mic_thread.start()


    # -----------------------------------------------------------------------
    # Receive events from OpenAI
    # -----------------------------------------------------------------------

    # This is currently only used to recognise the first audio packet. We can
    # expand the timing instrumentation later when tuning conversational
    # latency.
    first_audio_time = None

    try:
        while True:
            # Wait for the next event arriving on the already-open connection.
            event = connection.recv()

            # Live transcription of what the user is saying.
            if event.type == "session.input_transcript.delta":
                print(event.delta, end="", flush=True)

            # Stream Robot's generated PCM speech straight to the speaker.
            elif event.type == "session.output_audio.delta":

                if first_audio_time is None:
                    first_audio_time = time.perf_counter()
                    print()
                    print("[Robot speaking]")

                audio = base64.b64decode(event.delta)

                speaker.stdin.write(audio)
                speaker.stdin.flush()

            # Text transcript of Robot's generated response. This is useful for
            # debugging even though the normal interface is spoken audio.
            elif event.type == "session.output_transcript.delta":
                print(event.delta, end="", flush=True)

            # Print API errors rather than silently ignoring them.
            elif event.type == "error":
                print()
                print("ERROR:", event)

    except KeyboardInterrupt:
        # Ctrl+C is the normal way to stop this development prototype.
        print()
        print("Stopping Robot...")

    finally:
        # Make sure ALSA child processes are stopped even if Ctrl+C interrupts
        # the program while audio is being streamed.
        mic.terminate()
        speaker.terminate()


# Leaving the context manager closes the Live WebSocket cleanly.
print("Connection closed.")
