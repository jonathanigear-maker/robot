import math
import struct
import subprocess
import time
import wave

from piper import PiperVoice, SynthesisConfig


# ------------------------------------------------------------
# Piper settings
# ------------------------------------------------------------

MODEL = "en_US-danny-low.onnx"

# 1.0 = normal
# Higher = slower
# Lower = faster
syn_config = SynthesisConfig(
    length_scale=1.10
)


# ------------------------------------------------------------
# Robot voice effect
# ------------------------------------------------------------

CARRIER_1_HZ = 500
CARRIER_2_HZ = 750

DRY = 0.75
ROBOT = 0.35
VOLUME = 2.0

PITCH = 900


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


# ------------------------------------------------------------
# Load Piper
# ------------------------------------------------------------

print("Loading Piper...")

voice = PiperVoice.load(MODEL)

print("Piper ready.")


# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------

while True:

    text = input("Say: ")

    if text.lower() in ["quit", "exit"]:
        break

    start = time.perf_counter()


    # --------------------------------------------------------
    # Generate speech
    # --------------------------------------------------------

    with wave.open("piper_raw.wav", "wb") as wav_file:

        voice.synthesize_wav(
            text,
            wav_file,
            syn_config=syn_config
        )

    generated = time.perf_counter()


    # --------------------------------------------------------
    # Read generated audio
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # Apply robot effect
    # --------------------------------------------------------

    audio = robot_effect(
        audio,
        sample_rate
    )


    # --------------------------------------------------------
    # Play through SoX
    # --------------------------------------------------------

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
            "plughw:CARD=Array,DEV=0",

            "pitch", str(PITCH)
        ],

        stdin=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    speaker.communicate(audio)


    # --------------------------------------------------------
    # Timing
    # --------------------------------------------------------

    finished = time.perf_counter()

    print(
        f"Generated: {generated - start:.2f}s | "
        f"Total incl. playback: {finished - start:.2f}s"
    )