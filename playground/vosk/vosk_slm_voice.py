
import json
import math
import struct
import subprocess
import time
import wave

import requests
from piper import PiperVoice, SynthesisConfig
from vosk import Model, KaldiRecognizer


# ============================================================
# Settings
# ============================================================

VOSK_MODEL = "/home/sodigece/robot/models/vosk-model-en-us-0.22-lgraph"
SAMPLE_RATE = 16000

SLM_URL = "http://localhost:8080/v1/chat/completions"

PIPER_MODEL = "/home/sodigece/robot/voices/en_US-danny-low.onnx"

AUDIO_DEVICE = "plughw:CARD=Array,DEV=0"


# ============================================================
# Piper / robot voice settings
# ============================================================

syn_config = SynthesisConfig(
    length_scale=1.10
)

CARRIER_1_HZ = 500
CARRIER_2_HZ = 750

DRY = 0.75
ROBOT = 0.35
VOLUME = 2.0

PITCH = 900


# ============================================================
# Robot voice effect
# ============================================================

def robot_effect(audio, sample_rate):

    samples = struct.unpack(
        "<" + "h" * (len(audio) // 2),
        audio
    )

    output = []

    for position, sample in enumerate(samples):

        t = position / sample_rate

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

    return struct.pack(
        "<" + "h" * len(output),
        *output
    )


# ============================================================
# Speak
# ============================================================

def speak(text):

    start = time.perf_counter()

    with wave.open("piper_raw.wav", "wb") as wav_file:

        voice.synthesize_wav(
            text,
            wav_file,
            syn_config=syn_config
        )

    generated = time.perf_counter()

    with wave.open("piper_raw.wav", "rb") as wav_file:

        sample_rate = wav_file.getframerate()
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()

        audio = wav_file.readframes(
            wav_file.getnframes()
        )

    if channels != 1 or sample_width != 2:

        raise RuntimeError(
            "Expected mono 16-bit Piper audio"
        )

    audio = robot_effect(
        audio,
        sample_rate
    )

    speaker = subprocess.Popen(
        [
            "sox",

            "-t", "raw",
            "-r", str(sample_rate),
            "-e", "signed-integer",
            "-b", "16",
            "-c", "1",
            "-",

            "-t", "alsa",
            AUDIO_DEVICE,

            "pitch", str(PITCH)
        ],

        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    speaker.communicate(audio)

    finished = time.perf_counter()

    print(
        f"TTS generated: {generated - start:.2f}s | "
        f"TTS + playback: {finished - start:.2f}s"
    )


# ============================================================
# Ask local SLM
# ============================================================

def ask_slm(text):

    messages.append(
        {
            "role": "user",
            "content": text
        }
    )

    start = time.perf_counter()

    response = requests.post(
        SLM_URL,
        json={
            "messages": messages
        },
        timeout=60
    )

    response.raise_for_status()

    answer = (
        response.json()
        ["choices"][0]
        ["message"]
        ["content"]
        .strip()
    )

    elapsed = time.perf_counter() - start

    messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    print(
        f"SLM time: {elapsed:.2f}s"
    )

    return answer


# ============================================================
# Start microphone
# ============================================================

def start_microphone():

    return subprocess.Popen(
        [
            "arecord",

            "-D", AUDIO_DEVICE,

            "-f", "S16_LE",
            "-r", str(SAMPLE_RATE),
            "-c", "1",
            "-t", "raw"
        ],

        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )


# ============================================================
# Load everything
# ============================================================

print("Loading Vosk...")

vosk_model = Model(VOSK_MODEL)

recognizer = KaldiRecognizer(
    vosk_model,
    SAMPLE_RATE
)

recognizer.SetWords(True)

print("Vosk ready.")


print("Loading Piper...")

voice = PiperVoice.load(
    PIPER_MODEL
)

print("Piper ready.")


# ============================================================
# Conversation
# ============================================================

messages = [
    {
        "role": "system",
        "content": (
            "You are Spencer, the brain of a small physical robot. "
            "You are speaking aloud to your owner. "
            "Keep responses conversational and fairly short because "
            "everything you say will be spoken aloud."
        )
    }
]


# ============================================================
# Main loop
# ============================================================

mic = start_microphone()

print()
print("Spencer is listening.")
print("Press Ctrl+C to stop.")
print()


try:

    while True:

        data = mic.stdout.read(2000)

        if not data:
            continue

        if recognizer.AcceptWaveform(data):

            result = json.loads(
                recognizer.Result()
            )

            text = result.get(
                "text",
                ""
            ).strip()

            if not text:
                continue

            print()
            print("YOU:", text)

            overall_start = time.perf_counter()

            try:

                answer = ask_slm(text)

            except Exception as error:

                print(
                    "SLM ERROR:",
                    error
                )

                continue

            print("SPENCER:", answer)

            try:

                speak(answer)

            except Exception as error:

                print(
                    "VOICE ERROR:",
                    error
                )

            overall_time = (
                time.perf_counter()
                - overall_start
            )

            print(
                f"TOTAL response cycle: "
                f"{overall_time:.2f}s"
            )

            print()


except KeyboardInterrupt:

    print("\nStopped.")


finally:

    if mic.poll() is None:
        mic.terminate()
PY