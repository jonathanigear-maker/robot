from dotenv import load_dotenv
from openai import OpenAI
import wave
import struct
import math
import subprocess
import os

load_dotenv()
client = OpenAI()

# Same Robot effect settings as robot.py
CARRIER_1_HZ = 500
CARRIER_2_HZ = 750
DRY = 0.75
ROBOT = 0.35
VOLUME = 2.0


def robot_effect(audio):
    robot_sample_position = 0

    samples = struct.unpack("<" + "h" * (len(audio) // 2), audio)
    output = []

    for sample in samples:
        t = robot_sample_position / 24000

        carrier1 = math.sin(2 * math.pi * CARRIER_1_HZ * t)
        carrier2 = math.sin(2 * math.pi * CARRIER_2_HZ * t)
        carrier = (carrier1 * 0.65) + (carrier2 * 0.35)

        if abs(sample) < 250:
            processed = sample * VOLUME
        else:
            processed = (
                (sample * DRY) +
                (sample * carrier * ROBOT)
            ) * VOLUME

        processed = max(-32768, min(32767, int(processed)))
        output.append(processed)

        robot_sample_position += 1

    return struct.pack("<" + "h" * len(output), *output)


phrases = {
    "ai_link_start.wav": "Very good, sir. Establishing AI link.",
    "ai_link_ready.wav": "Link established. At your service.",
}


for filename, text in phrases.items():

    print(f"Creating {filename}...")

    plain_file = "temp_plain.wav"
    robot_file = "temp_robot.wav"

    # Generate the voice
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="ballad",
        input=text,
        response_format="wav",
        instructions=(
            "Speak in British English. Calm, restrained, traditional British "
            "butler manner. Slightly robotic and matter-of-fact. "
            "Do not sound enthusiastic."
        ),
    ) as response:
        response.stream_to_file(plain_file)

    # Apply our Python robot modulation
    with wave.open(plain_file, "rb") as wav:
        params = wav.getparams()
        audio = wav.readframes(wav.getnframes())

    processed = robot_effect(audio)

    with wave.open(robot_file, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(processed)

    # Apply the same +800 cent pitch shift used by robot.py
    subprocess.run(
        [
            "sox",
            robot_file,
            filename,
            "pitch",
            "800",
        ],
        check=True,
    )

    os.remove(plain_file)
    os.remove(robot_file)


print("Done.")
