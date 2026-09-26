import math
import struct
import subprocess
import wave


# ==========================================
# SETTINGS — fiddle with these
# ==========================================

INPUT = "/home/sodigece/robot/playground/voice/voice_comparison/04_onyx_raw.wav"
OUTPUT = "/home/sodigece/robot/playground/voice/voice_comparison/onyx_test.wav"

PITCH = 1000
TEMPO = 1.30

# Keep Spenser's existing robot effect
CARRIER_1_HZ = 500
CARRIER_2_HZ = 750
DRY = 0.75
ROBOT = 0.35
VOLUME = 2.0


# ==========================================
# ROBOT EFFECT
# ==========================================

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
            carrier1 * 0.65 +
            carrier2 * 0.35
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


# ==========================================
# LOAD RAW WAV
# ==========================================

with wave.open(INPUT, "rb") as wav_file:

    sample_rate = wav_file.getframerate()

    audio = wav_file.readframes(
        wav_file.getnframes()
    )


# ==========================================
# ROBOTISE
# ==========================================

processed = robot_effect(
    audio,
    sample_rate
)


# ==========================================
# PITCH + TEMPO
# ==========================================

process = subprocess.Popen(
    [
        "sox",

        "-t", "raw",
        "-r", str(sample_rate),
        "-e", "signed-integer",
        "-b", "16",
        "-c", "1",
        "-",

        OUTPUT,

        "pitch", str(PITCH),
        "tempo", str(TEMPO)
    ],

    stdin=subprocess.PIPE
)

process.communicate(processed)

if process.returncode != 0:
    raise RuntimeError("SoX processing failed")


print()
print("Created:", OUTPUT)
print("Pitch:", PITCH)
print("Tempo:", TEMPO)
print()