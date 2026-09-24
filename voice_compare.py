import base64
import math
import os
import struct
import subprocess
import wave

from dotenv import load_dotenv
from openai import OpenAI
from piper import PiperVoice, SynthesisConfig


# ============================================================
# SETTINGS
# ============================================================

OUTPUT_DIR = "voice_comparison"

SENTENCES = [
    "Affirmative.",
    "All systems operational.",
    "I'm afraid the lidar is offline again.",
    "Well, that was entirely predictable."
]

# Piper
PIPER_MODEL = "en_US-danny-low.onnx"
DANNY_LENGTH_SCALE = 1.10
DANNY_PITCH = 900

# OpenAI Live
BALLAD_VOICE = "ballad"
BALLAD_PITCH = 800

# Robot effect
CARRIER_1_HZ = 500
CARRIER_2_HZ = 750
DRY = 0.75
ROBOT = 0.35
VOLUME = 2.0

# OpenAI Live audio is 24 kHz
BALLAD_SAMPLE_RATE = 24000


# ============================================================
# ROBOT EFFECT
# ============================================================

def robot_effect(audio, sample_rate):
    samples = struct.unpack("<" + "h" * (len(audio) // 2), audio)
    output = []

    for position, sample in enumerate(samples):
        t = position / sample_rate
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

    return struct.pack("<" + "h" * len(output), *output)


# ============================================================
# SAVE RAW PCM AS WAV
# ============================================================

def save_wav(filename, audio, sample_rate):
    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio)


# ============================================================
# APPLY ROBOT EFFECT + SOX PITCH
# ============================================================

def make_robot_wav(raw_audio, sample_rate, pitch, output_filename):
    processed = robot_effect(raw_audio, sample_rate)

    process = subprocess.Popen(
        [
            "sox",
            "-t", "raw",
            "-r", str(sample_rate),
            "-e", "signed-integer",
            "-b", "16",
            "-c", "1",
            "-",
            output_filename,
            "pitch", str(pitch)
        ],
        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    process.communicate(processed)

    if process.returncode != 0:
        raise RuntimeError("SoX processing failed")


# ============================================================
# DANNY / PIPER
# ============================================================

def generate_danny(voice, syn_config, text, number):
    print(f"  Danny: {text}")

    temporary_file = os.path.join(OUTPUT_DIR, "_danny_temp.wav")

    with wave.open(temporary_file, "wb") as wav_file:
        voice.synthesize_wav(text, wav_file, syn_config=syn_config)

    with wave.open(temporary_file, "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        audio = wav_file.readframes(wav_file.getnframes())

    raw_filename = os.path.join(
        OUTPUT_DIR,
        f"{number:02d}_danny_raw.wav"
    )
    robot_filename = os.path.join(
        OUTPUT_DIR,
        f"{number:02d}_danny_robot.wav"
    )

    save_wav(raw_filename, audio, sample_rate)
    make_robot_wav(
        audio,
        sample_rate,
        DANNY_PITCH,
        robot_filename
    )


# ============================================================
# BALLAD / OPENAI LIVE
# ============================================================

def generate_ballad(client, text, number):
    print(f"  Ballad: {text}")

    audio_chunks = []

    with client.live.connect() as connection:
        connection.send({
            "type": "session.start",
            "session": {
                "model": "gpt-live-1",
                "audio": {
                    "output": {
                        "voice": BALLAD_VOICE
                    }
                },
                "instructions": """
Speak exactly the text you are given.

Do not add anything before or after it.
Do not answer or comment on the text.
Simply speak it exactly as written.
"""
            }
        })

        while True:
            event = connection.recv()
            if event.type == "session.started":
                break

        connection.send({
            "type": "session.user_message",
            "content": text
        })

        while True:
            event = connection.recv()

            if event.type == "session.output_audio.delta":
                audio_chunks.append(base64.b64decode(event.delta))

            elif event.type == "session.output_audio.done":
                break

            elif event.type == "error":
                raise RuntimeError(f"OpenAI error: {event}")

    audio = b"".join(audio_chunks)

    raw_filename = os.path.join(
        OUTPUT_DIR,
        f"{number:02d}_ballad_raw.wav"
    )
    robot_filename = os.path.join(
        OUTPUT_DIR,
        f"{number:02d}_ballad_robot.wav"
    )

    save_wav(raw_filename, audio, BALLAD_SAMPLE_RATE)
    make_robot_wav(
        audio,
        BALLAD_SAMPLE_RATE,
        BALLAD_PITCH,
        robot_filename
    )


# ============================================================
# MAIN
# ============================================================

print()
print("================================")
print(" SPENSER VOICE COMPARISON")
print("================================")
print()

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("Loading Danny...")
piper_voice = PiperVoice.load(PIPER_MODEL)
piper_config = SynthesisConfig(length_scale=DANNY_LENGTH_SCALE)
print("Danny ready.")

load_dotenv()
client = OpenAI()

for number, text in enumerate(SENTENCES, start=1):
    print()
    print(f"Sentence {number}/{len(SENTENCES)}")

    generate_danny(
        piper_voice,
        piper_config,
        text,
        number
    )

    generate_ballad(
        client,
        text,
        number
    )

temporary_file = os.path.join(OUTPUT_DIR, "_danny_temp.wav")

if os.path.exists(temporary_file):
    os.remove(temporary_file)

print()
print("================================")
print(" FINISHED")
print("================================")
print()
print(f"WAV files saved in: {OUTPUT_DIR}/")
print()
