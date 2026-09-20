import subprocess
import json
import usb.core
import usb.util
import struct
import math

from vosk import Model, KaldiRecognizer

MODEL_PATH = "/home/sodigece/openai/vosk-model-small-en-gb-0.15"


# ---------------------------------------------------------------------------
# ReSpeaker XVF3800
# ---------------------------------------------------------------------------

respeaker = usb.core.find(
    idVendor=0x2886,
    idProduct=0x001A
)

if respeaker is None:
    raise RuntimeError("ReSpeaker XVF3800 not found")


# ---------------------------------------------------------------------------
# Vosk command vocabulary
# ---------------------------------------------------------------------------

commands = [
    "robot",
    "spenser",
    "lights",
    "on",
    "off",
    "turn",
    "switch",
    "move",
    "go",
    "forward",
    "backward",
    "left",
    "right",
    "stop",
    "halt",
    "talk",
    "conversation",
    "start",
    "the",
    "a",
    "[unk]"
]


# ---------------------------------------------------------------------------
# ReSpeaker direction
# ---------------------------------------------------------------------------

def get_direction():

    response = respeaker.ctrl_transfer(
        usb.util.CTRL_IN |
        usb.util.CTRL_TYPE_VENDOR |
        usb.util.CTRL_RECIPIENT_DEVICE,
        0,
        0x80 | 75,
        33,
        17,
        1000
    )

    angles = struct.unpack(
        "<ffff",
        bytes(response[1:17])
    )

    radians = angles[3]
    degrees = math.degrees(radians) % 360

    return degrees


# ---------------------------------------------------------------------------
# Vosk setup
# ---------------------------------------------------------------------------

model = Model(MODEL_PATH)

recognizer = KaldiRecognizer(
    model,
    16000,
    json.dumps(commands)
)

recognizer.SetWords(True)


# ---------------------------------------------------------------------------
# Microphone
# ---------------------------------------------------------------------------

mic = subprocess.Popen(
    [
        "arecord",
        "-D", "plughw:CARD=Array,DEV=0",
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        "-t", "raw"
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL
)


print("Robot command listener ready...")
print("Final results and confidence will be shown.")
print("Press Ctrl+C to stop.")


# ---------------------------------------------------------------------------
# Main command loop
# ---------------------------------------------------------------------------

try:

    while True:

        data = mic.stdout.read(2000)

        if recognizer.AcceptWaveform(data):

            result = json.loads(
                recognizer.Result()
            )

            text = result.get("text", "")
            words = result.get("result", [])

            if text and text != "[unk]":

                if words:

                    confidences = [
                        word["conf"]
                        for word in words
                    ]

                    average_confidence = (
                        sum(confidences)
                        / len(confidences)
                    )

                    direction = get_direction()

                    print(
                        f"COMMAND: {text}  "
                        f"CONFIDENCE: {average_confidence:.2f}  "
                        f"DIRECTION: {direction:.0f}°"
                    )


                    # -------------------------------------------------------
                    # Start AI conversation
                    # -------------------------------------------------------

                    if "robot" in text and "talk" in text:

                        print("Starting AI conversation...")

                        # Stop Vosk microphone capture first.
                        # This frees the ReSpeaker microphone for robot.py.
                        mic.terminate()
                        mic.wait()


                        # ---------------------------------------------------
                        # Play "Establishing AI link"
                        #
                        # Popen is deliberately used instead of run().
                        # This means Python DOES NOT wait for the WAV to
                        # finish before starting the OpenAI connection.
                        # ---------------------------------------------------




                        # ---------------------------------------------------
                        # Start OpenAI Live immediately
                        #
                        # The WAV above can continue playing while robot.py
                        # opens the WebSocket and starts the Live session.
                        # ---------------------------------------------------

                        subprocess.run(
                            [
                                "/home/sodigece/openai/env/bin/python",
                                "/home/sodigece/robot-github/robot.py"
                            ],
                            cwd="/home/sodigece/robot-github"
                        )

                        break


                else:

                    print(
                        f"COMMAND: {text}  "
                        f"CONFIDENCE: unknown"
                    )


except KeyboardInterrupt:

    print("\nStopped.")


finally:

    # mic may already have been stopped by "robot talk".
    if mic.poll() is None:
        mic.terminate()
