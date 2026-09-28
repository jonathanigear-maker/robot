import random
from pathlib import Path
from src.audio_output import play_wav_async

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

    return play_wav_async(sound)


def big_brain_confirmation():
    """Play an 'I don't know' response followed by a Big Brain question."""

    dont_know_folder = SOUNDS / "I_dont_know"
    big_brain_folder = SOUNDS / "query_openBigBrin"

    dont_know_choices = list(dont_know_folder.glob("*.wav"))
    big_brain_choices = list(big_brain_folder.glob("*.wav"))

    if not dont_know_choices or not big_brain_choices:
        print("VOICE: Missing Big Brain confirmation sounds.")
        return None

    dont_know_sound = random.choice(dont_know_choices)
    big_brain_sound = random.choice(big_brain_choices)

    # First part
    print(f"VOICE STARTED: {dont_know_sound.name}")
    thread = play_wav_async(dont_know_sound)
    thread.join()

    # Second part
    print(f"VOICE STARTED: {big_brain_sound.name}")
    return play_wav_async(big_brain_sound)