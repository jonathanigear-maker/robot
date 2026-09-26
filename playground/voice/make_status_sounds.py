from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import wave
import struct
import math
import subprocess
import os

load_dotenv()
client = OpenAI()


# ============================================================
# CHANGE ONLY THIS TO GENERATE A DIFFERENT SET OF SOUNDS
# ============================================================

INPUT_FILE = Path("/home/sodigece/robot/sounds/query_openBigBrin.md")


# ============================================================
# ROBOT VOICE SETTINGS
# ============================================================

CARRIER_1_HZ = 500
CARRIER_2_HZ = 750
DRY = 0.75
ROBOT = 0.35
VOLUME = 2.0

PITCH = 900


def robot_effect(audio):
    robot_sample_position = 0

    samples = struct.unpack(
        "<" + "h" * (len(audio) // 2),
        audio
    )

    output = []

    for sample in samples:
        t = robot_sample_position / 24000

        carrier1 = math.sin(2 * math.pi * CARRIER_1_HZ * t)
        carrier2 = math.sin(2 * math.pi * CARRIER_2_HZ * t)

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


# ============================================================
# READ PHRASES
# ============================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Cannot find input file: {INPUT_FILE}"
    )


# Folder name comes automatically from the input filename.
#
# command_accepted.md
#       ↓
# sounds/command_accepted/

OUTPUT_DIR = INPUT_FILE.parent / INPUT_FILE.stem
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


with INPUT_FILE.open("r", encoding="utf-8") as file:
    phrases = [
        line.strip()
        for line in file
        if line.strip()
    ]


print()
print(f"Input:  {INPUT_FILE}")
print(f"Output: {OUTPUT_DIR}")
print(f"Phrases found: {len(phrases)}")
print()


# ============================================================
# GENERATE EACH RECORDING
# ============================================================

for number, text in enumerate(phrases, start=1):

    filename = (
        OUTPUT_DIR /
        f"{INPUT_FILE.stem}_{number:02d}.wav"
    )

    print(
        f"[{number}/{len(phrases)}] "
        f"{filename.name}: {text}"
    )

    plain_file = OUTPUT_DIR / "_temp_plain.wav"
    robot_file = OUTPUT_DIR / "_temp_robot.wav"

    # Generate Ballad voice
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

    # Apply robot modulation
    with wave.open(str(plain_file), "rb") as wav:
        audio = wav.readframes(
            wav.getnframes()
        )

    processed = robot_effect(audio)

    with wave.open(str(robot_file), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(processed)

    # Final +900 cent pitch shift
    subprocess.run(
        [
            "sox",
            str(robot_file),
            str(filename),
            "pitch",
            str(PITCH),
        ],
        check=True,
    )

    os.remove(plain_file)
    os.remove(robot_file)


print()
print(
    f"Done. Created {len(phrases)} recordings "
    f"in {OUTPUT_DIR}"
)