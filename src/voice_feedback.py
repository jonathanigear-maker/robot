import random
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOUNDS = PROJECT_ROOT / "sounds"


def command_accepted():
    """Play a random neutral command-accepted acknowledgement."""

    folder = SOUNDS / "command_accepted"

    choices = list(folder.glob("*.wav"))

    if not choices:
        print("VOICE: No command acknowledgement sounds found.")
        return None

    sound = random.choice(choices)

    print(f"VOICE: {sound.name}")

    process = subprocess.Popen(
        ["aplay", "-q", str(sound)]
    )

    return process

def big_brain_confirmation():
    """Play a random Big Brain confirmation question."""
    folder = SOUNDS / "query_openBigBrin"
    choices = list(folder.glob("*.wav"))

    if not choices:
        print("VOICE: No Big Brain confirmation sounds found.")
        return None

    sound = random.choice(choices)

    print(f"VOICE STARTED: {sound.name}")

    process = subprocess.Popen(
        ["aplay", "-q", str(sound)]
    )

    return process