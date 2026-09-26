import subprocess
import json

from vosk import Model, KaldiRecognizer

MODEL_PATH = "/home/sodigece/robot/models/vosk-model-small-en-gb-0.15"
SAMPLE_RATE = 16000

# Specialist robot vocabulary. Add important/unusual robot words here.
SPECIAL_WORDS = [
    "hey",
    "robot",
    "spenser",
    "spencer",
    "lights",
    "light",
    "motors",
    "motor",
    "lidar",
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

# Terminal colours:
GREEN = "\033[92m"   # specialist recognizer agrees
YELLOW = "\033[93m"  # specialist recognizer corrected full recognizer
RESET = "\033[0m"


def make_full_recognizer(model):
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.SetWords(True)
    return recognizer


def make_special_recognizer(model):
    recognizer = KaldiRecognizer(
        model,
        SAMPLE_RATE,
        json.dumps(SPECIAL_WORDS)
    )
    recognizer.SetWords(True)
    return recognizer


def start_microphone():
    return subprocess.Popen(
        [
            "arecord",
            "-D", "plughw:CARD=Array,DEV=0",
            "-f", "S16_LE",
            "-r", str(SAMPLE_RATE),
            "-c", "1",
            "-t", "raw"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )


def overlap(a, b):
    """Seconds of time overlap between two Vosk word results."""
    return max(0.0, min(a["end"], b["end"]) - max(a["start"], b["start"]))


def overlap_ratio(a, b):
    """Overlap relative to the shorter of the two words."""
    duration = min(a["end"] - a["start"], b["end"] - b["start"])
    if duration <= 0:
        return 0.0
    return overlap(a, b) / duration


def merge_words(full_words, special_words):
    """
    Start with the unrestricted Vosk result.

    A specialist word with strong timestamp overlap can either:
      * confirm the full recognizer's word (green), or
      * replace it (yellow).

    [unk] is never used as a replacement.
    """
    merged = [
        {
            "word": word["word"],
            "start": word["start"],
            "end": word["end"],
            "source": "full"
        }
        for word in full_words
    ]

    for specialist in special_words:
        specialist_word = specialist["word"]

        if specialist_word == "[unk]":
            continue

        best_index = None
        best_overlap = 0.0

        for index, full_word in enumerate(full_words):
            score = overlap_ratio(full_word, specialist)
            if score > best_overlap:
                best_overlap = score
                best_index = index

        # Require substantial overlap so nearby words are not accidentally replaced.
        if best_index is not None and best_overlap >= 0.50:
            original = merged[best_index]["word"]
            merged[best_index]["word"] = specialist_word

            if original == specialist_word:
                merged[best_index]["source"] = "confirmed"
            else:
                merged[best_index]["source"] = "corrected"

    return merged


def print_merged(full_result, special_result):
    full_words = full_result.get("result", [])
    special_words = special_result.get("result", [])

    if not full_words:
        return

    merged = merge_words(full_words, special_words)

    output = []

    for word in merged:
        text = word["word"]

        if word["source"] == "confirmed":
            text = f"{GREEN}{text}{RESET}"
        elif word["source"] == "corrected":
            text = f"{YELLOW}{text}{RESET}"

        output.append(text)

    print(" ".join(output))


print("Loading Vosk model...")
model = Model(MODEL_PATH)

full_recognizer = make_full_recognizer(model)
special_recognizer = make_special_recognizer(model)
mic = start_microphone()

print()
print("Dual Vosk test ready.")
print("Normal text  = full vocabulary Vosk")
print(f"{GREEN}Green{RESET}        = specialist recognizer agrees")
print(f"{YELLOW}Yellow{RESET}       = specialist recognizer changed the word")
print("Press Ctrl+C to stop.")
print()

try:
    while True:
        data = mic.stdout.read(2000)

        if not data:
            continue

        full_final = full_recognizer.AcceptWaveform(data)
        special_final = special_recognizer.AcceptWaveform(data)

        # Both recognizers receive exactly the same audio. Normally their final
        # utterance boundaries line up. Print when the full recognizer closes
        # an utterance, using the specialist's current final result too.
        if full_final:
            full_result = json.loads(full_recognizer.Result())

            if special_final:
                special_result = json.loads(special_recognizer.Result())
            else:
                # Force the specialist's current utterance result so we can
                # compare its timestamped words with the full result.
                special_result = json.loads(special_recognizer.FinalResult())

                # FinalResult closes that recognizer, so make a fresh specialist
                # recognizer for the next utterance.
                special_recognizer = make_special_recognizer(model)

            print_merged(full_result, special_result)

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    if mic.poll() is None:
        mic.terminate()
