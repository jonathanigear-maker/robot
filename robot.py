"""
Robot - OpenAI Live voice conversation prototype
"""

import base64
import math
import struct
import subprocess
import threading
import time

from dotenv import load_dotenv
from openai import OpenAI
from delegation import handle_task


# ---------------------------------------------------------------------------
# Terminal colours
# ---------------------------------------------------------------------------

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"


# ---------------------------------------------------------------------------
# Robot voice effect
# ---------------------------------------------------------------------------

CARRIER_1_HZ = 500
CARRIER_2_HZ = 750
DRY = 0.75
ROBOT = 0.35
VOLUME = 2.0

robot_sample_position = 0


def robot_effect(audio):
    global robot_sample_position

    samples = struct.unpack(
        "<" + "h" * (len(audio) // 2),
        audio
    )

    output = []

    for sample in samples:

        t = robot_sample_position / 24000

        carrier1 = math.sin(
            2 * math.pi * CARRIER_1_HZ * t
        )

        carrier2 = math.sin(
            2 * math.pi * CARRIER_2_HZ * t
        )

        carrier = (
            (carrier1 * 0.65) +
            (carrier2 * 0.35)
        )

        if abs(sample) < 250:
            processed = sample * VOLUME
        else:
            processed = (
                (sample * DRY) +
                (sample * carrier * ROBOT)
            ) * VOLUME

        processed = max(
            -32768,
            min(32767, int(processed))
        )

        output.append(processed)

        robot_sample_position += 1

    return struct.pack(
        "<" + "h" * len(output),
        *output
    )


# ---------------------------------------------------------------------------
# OpenAI setup
# ---------------------------------------------------------------------------

load_dotenv()

client = OpenAI()


# ---------------------------------------------------------------------------
# Play startup message while connection opens
# ---------------------------------------------------------------------------

link_sound = subprocess.Popen([
    "aplay",
    "-D", "plughw:CARD=Array,DEV=0",
    "/home/sodigece/robot-github/ai_link_start.wav"
])


print("Opening Live connection...")
connect_start = time.perf_counter()


# ---------------------------------------------------------------------------
# Live connection
# ---------------------------------------------------------------------------

with client.live.connect() as connection:

    print(
        f"WebSocket opened in "
        f"{time.perf_counter() - connect_start:.2f}s"
    )


    # -----------------------------------------------------------------------
    # Start Live session
    # -----------------------------------------------------------------------

    connection.send({
        "type": "session.start",

        "session": {

            "model": "gpt-live-1",

            "audio": {
                "output": {
                    "voice": "ballad"
                }
            },

            "instructions": """
You are Robot, a small physical robot running on a Raspberry Pi.

Speak in British English, with the manner of a traditional British butler.

Your delivery should be calm, restrained and slightly dry.
Use relatively flat, controlled intonation.
Avoid excessive enthusiasm, excitement, or exaggerated emotional expression.
Do not sound completely emotionless: allow subtle warmth and occasional mild amusement.

Speak clearly and naturally, but keep your responses fairly concise and conversational.

Your personality is polite, capable, observant and slightly cheeky.
Your humour should be understated and dry rather than energetic or silly.
Occasionally make a subtle witty remark when appropriate.

You may occasionally use short robotic expressions such as:
"Affirmative."
"Processing."
"Systems nominal."
"Very good, sir."
"As you wish."
"Certainly."

Do not overuse these phrases or repeat them mechanically.

You know that you are a physical robot.
You are aware that you run on a Raspberry Pi.
Never pretend to be human.

Above all, remain composed. Even when something is exciting or surprising,
respond with the restrained manner of an unflappable British butler.
"""
        }
    })


    # -----------------------------------------------------------------------
    # Wait for Live session
    # -----------------------------------------------------------------------

    while True:

        event = connection.recv()

        if event.type == "session.started":

            print("Live session started!")

            # The WebSocket may connect before the startup announcement
            # has finished. Wait here so both WAV files never fight over
            # the ReSpeaker playback device.
            link_sound.wait()

            subprocess.run([
                "aplay",
                "-D", "plughw:CARD=Array,DEV=0",
                "/home/sodigece/robot-github/ai_link_ready.wav"
            ])

            break


    # -----------------------------------------------------------------------
    # Microphone
    # -----------------------------------------------------------------------

    mic = subprocess.Popen(
        [
            "arecord",
            "-D", "plughw:CARD=Array,DEV=0",
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

    speaker = subprocess.Popen(
        [
            "sox",
            "-t", "raw",
            "-r", "24000",
            "-e", "signed-integer",
            "-b", "16",
            "-c", "1",
            "-",
            "-t", "alsa",
            "plughw:CARD=Array,DEV=0",
            "pitch", "800"
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

        while True:

            audio = mic.stdout.read(4800)

            if not audio:
                break

            connection.send({
                "type": "session.input_audio.append",
                "audio": base64.b64encode(
                    audio
                ).decode("ascii")
            })


    mic_thread = threading.Thread(
        target=send_microphone,
        daemon=True
    )

    mic_thread.start()


    # -----------------------------------------------------------------------
    # Conversation state
    # -----------------------------------------------------------------------

    current_speaker = None

    # Text currently being spoken by the user.
    current_user_turn = ""

    # Text currently being spoken by Robot.
    current_robot_turn = ""

    # Previous completed turns.
    #
    # Example:
    #
    # [
    #     {"role": "user", "text": "How heavy is a donkey?"},
    #     {"role": "robot", "text": "Around 180 to 230 kilograms."}
    # ]
    conversation_history = []

    MAX_HISTORY_TURNS = 10


    # -----------------------------------------------------------------------
    # Store a completed turn
    # -----------------------------------------------------------------------

    def add_to_history(role, text):

        text = text.strip()

        if not text:
            return

        conversation_history.append({
            "role": role,
            "text": text
        })

        # Keep only the most recent turns.
        if len(conversation_history) > MAX_HISTORY_TURNS:
            del conversation_history[:-MAX_HISTORY_TURNS]


    # -----------------------------------------------------------------------
    # Delegation worker
    # -----------------------------------------------------------------------

    def run_delegation(
        question,
        delegation_id,
        history_snapshot
    ):

        try:

            answer = handle_task(
                question,
                history_snapshot
            )

            print()

            print(
                f"{YELLOW}"
                f"ANSWER: {answer}"
                f"{RESET}"
            )

            print(
                f"{YELLOW}"
                f"------------------"
                f"{RESET}"
            )

            print()

            connection.send({
                "type": "session.commentary.append",
                "delegation_id": delegation_id,
                "content": answer
            })

        except Exception as error:

            print()

            print(
                f"{RED}"
                f"DELEGATION ERROR: {error}"
                f"{RESET}"
            )


    # -----------------------------------------------------------------------
    # Receive events
    # -----------------------------------------------------------------------

    try:

        while True:

            event = connection.recv()


            # ---------------------------------------------------------------
            # Delegation
            # ---------------------------------------------------------------

            if event.type == "session.delegation.created":

                question = current_user_turn.strip()

                # Take a copy NOW.
                #
                # The delegation runs in another thread, so we don't want
                # later conversation changes altering the context while
                # GPT is processing the current request.
                history_snapshot = [
                    turn.copy()
                    for turn in conversation_history
                ]

                print()

                print(
                    f"{YELLOW}"
                    f"--- DELEGATION ---"
                    f"{RESET}"
                )

                print(
                    f"{YELLOW}"
                    f"QUESTION: {question}"
                    f"{RESET}"
                )

                delegation_thread = threading.Thread(
                    target=run_delegation,
                    args=(
                        question,
                        event.delegation.id,
                        history_snapshot
                    ),
                    daemon=True
                )

                delegation_thread.start()


            # ---------------------------------------------------------------
            # User transcript
            # ---------------------------------------------------------------

            elif event.type == "session.input_transcript.delta":

                # Robot was speaking and the user has now started.
                #
                # That gives us a boundary for the previous Robot turn.
                if current_speaker != "user":

                    if current_robot_turn.strip():

                        add_to_history(
                            "robot",
                            current_robot_turn
                        )

                        current_robot_turn = ""

                    print()

                    print(
                        f"{CYAN}YOU: {RESET}",
                        end="",
                        flush=True
                    )

                    current_speaker = "user"


                current_user_turn += event.delta

                print(
                    f"{CYAN}"
                    f"{event.delta}"
                    f"{RESET}",
                    end="",
                    flush=True
                )


            # ---------------------------------------------------------------
            # Robot audio
            # ---------------------------------------------------------------

            elif event.type == "session.output_audio.delta":

                audio = base64.b64decode(
                    event.delta
                )

                audio = robot_effect(audio)

                speaker.stdin.write(audio)
                speaker.stdin.flush()


            # ---------------------------------------------------------------
            # Robot transcript
            # ---------------------------------------------------------------

            elif event.type == "session.output_transcript.delta":

                # The user was speaking and Robot has now started.
                #
                # Store that user turn in conversation history.
                if current_speaker != "robot":

                    if current_user_turn.strip():

                        add_to_history(
                            "user",
                            current_user_turn
                        )

                    print()

                    print(
                        f"{GREEN}ROBOT: {RESET}",
                        end="",
                        flush=True
                    )

                    current_speaker = "robot"


                current_robot_turn += event.delta

                print(
                    f"{GREEN}"
                    f"{event.delta}"
                    f"{RESET}",
                    end="",
                    flush=True
                )


            # ---------------------------------------------------------------
            # API errors
            # ---------------------------------------------------------------

            elif event.type == "error":

                print()

                print(
                    f"{RED}"
                    f"ERROR: {event}"
                    f"{RESET}"
                )


    except KeyboardInterrupt:

        print()
        print()
        print("Stopping Robot...")


    finally:

        mic.terminate()
        speaker.terminate()


# ---------------------------------------------------------------------------
# Finished
# ---------------------------------------------------------------------------

print("Connection closed.")
