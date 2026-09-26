import subprocess
import json
import time

from vosk import Model, KaldiRecognizer

FULL_MODEL_PATH = "/home/sodigece/robot/models/vosk-model-en-us-0.22-lgraph"
SPECIAL_MODEL_PATH = "/home/sodigece/robot/models/vosk-model-small-en-gb-0.15"
SAMPLE_RATE = 16000

# Specialist robot vocabulary. Add important/unusual robot words here.
SPECIAL_WORDS = [
    # Robot/address
    "robot", "spencer", "spenser",

    # Polite/common speech
    "please", "could", "would", "can", "you", "your",
    "the", "a", "an", "my", "me", "it", "to",
    "i", "want", "like", "make", "what", "why",
    "is", "are", "was", "and", "about",

    # Actions
    "turn", "switch", "move", "go", "stop", "halt",
    "start", "set", "change",

    # Devices
    "light", "lights", "motor", "motors", "lidar",

    # Directions/states
    "on", "off", "forward", "backward", "left", "right",

    # Colours
    "red", "green", "blue", "yellow", "white",
    "orange", "purple",

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

    Specialist can:
      * confirm the full recognizer's word (green)
      * replace it if specialist confidence is sufficiently stronger (yellow)

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

        # Require substantial timestamp overlap.
        if best_index is not None and best_overlap >= 0.50:

            original = merged[best_index]["word"]

            full_conf = full_words[best_index].get("conf", 0.0)
            special_conf = specialist.get("conf", 0.0)

            # Both recognizers heard the same word.
            if original == specialist_word:
                merged[best_index]["source"] = "confirmed"

            # Specialist heard something different.
            elif (
                special_conf > full_conf + 0.15
                or (full_conf < 0.60 and special_conf > 0.70)
            ):
                merged[best_index]["word"] = specialist_word
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


print("Loading full Vosk model...")
full_model = Model(FULL_MODEL_PATH)

print("Loading specialist Vosk model...")
special_model = Model(SPECIAL_MODEL_PATH)

full_recognizer = make_full_recognizer(full_model)
special_recognizer = make_special_recognizer(special_model)

mic = start_microphone()

print()
print("Dual Vosk test ready.")
print("Normal text  = full vocabulary Vosk")
print(f"{GREEN}Green{RESET}        = specialist recognizer agrees")
print(f"{YELLOW}Yellow{RESET}       = specialist recognizer changed the word")
print("Press Ctrl+C to stop.")
print()

full_total_time = 0.0
special_total_time = 0.0
chunk_count = 0


try:
    while True:
        data = mic.stdout.read(2000)

        if not data:
            continue

        # ---- Full recognizer timing ----
        start = time.perf_counter()
        full_final = full_recognizer.AcceptWaveform(data)
        full_time = time.perf_counter() - start

        # ---- Specialist recognizer timing ----
        start = time.perf_counter()
        special_final = special_recognizer.AcceptWaveform(data)
        special_time = time.perf_counter() - start

        # Accumulate processing time
        full_total_time += full_time
        special_total_time += special_time
        chunk_count += 1

        # Both recognizers receive exactly the same audio.
        if full_final:
            full_result = json.loads(full_recognizer.Result())

            if special_final:
                special_result = json.loads(special_recognizer.Result())
            else:
                special_result = json.loads(special_recognizer.FinalResult())
                special_recognizer = make_special_recognizer(special_model)

            if full_result.get("text", "").strip():

                # Each 2000-byte chunk contains:
                # 1000 samples / 16000 samples/sec = 0.0625 seconds
                audio_time = chunk_count * 0.0625

                total_processing = full_total_time + special_total_time

                print()
                print(f"Audio processed:        {audio_time:.2f} s")
                print(f"Full Vosk CPU time:     {full_total_time:.3f} s")
                print(f"Specialist CPU time:    {special_total_time:.3f} s")
                print(f"Combined Vosk CPU time: {total_processing:.3f} s")
                print(f"Final full chunk:       {full_time * 1000:.1f} ms")

                if total_processing < audio_time:
                    print(f"HEADROOM:               {audio_time - total_processing:.3f} s")
                else:
                    print(f"BEHIND REALTIME:        {total_processing - audio_time:.3f} s")

                print_merged(full_result, special_result)
                print()

            # Reset counters for next utterance
            full_total_time = 0.0
            special_total_time = 0.0
            chunk_count = 0

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    if mic.poll() is None:
        mic.terminate()