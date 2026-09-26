import subprocess
import json
import re
import time

from vosk import Model, KaldiRecognizer

MODEL_PATH = "/home/sodigece/openai/vosk-model-small-en-gb-0.15"
SAMPLE_RATE = 16000
CONTEXT_SECONDS = 15.0

# Deliberately constrained grammar for the deterministic lights experiment.
# "spenser" is included because the current Vosk tests have used that spelling;
# "spencer" is included as well.
GRAMMAR = [
    "robot", "spenser", "spencer",
    "light", "lights",
    "on", "off",
    "low", "medium", "high", "full",
    "red", "orange", "yellow", "green", "blue", "indigo", "violet",
    "warm", "cool", "white", "warmer", "cooler",
    "percent",
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
    "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
    "seventeen", "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty",
    "sixty", "seventy", "eighty", "ninety", "hundred",
    "[unk]"
]

COLOURS = {
    "red", "orange", "yellow", "green", "blue", "indigo", "violet"
}

BRIGHTNESS = {
    "low": 25,
    "medium": 50,
    "high": 75,
    "full": 100
}

ONES = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19
}

TENS = {
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90
}


def make_recognizer(model):
    recognizer = KaldiRecognizer(
        model,
        SAMPLE_RATE,
        json.dumps(GRAMMAR)
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


def words_to_number(words):
    """Return a number from simple Vosk number words, or None."""
    if not words:
        return None

    # This also makes the parser usable if Vosk ever returns digits.
    for word in words:
        if re.fullmatch(r"\d{1,3}", word):
            return int(word)

    if words == ["one", "hundred"] or words == ["hundred"]:
        return 100

    if len(words) == 1:
        if words[0] in ONES:
            return ONES[words[0]]
        if words[0] in TENS:
            return TENS[words[0]]

    if len(words) == 2 and words[0] in TENS and words[1] in ONES:
        return TENS[words[0]] + ONES[words[1]]

    return None


class LightCommandParser:
    def __init__(self):
        self.active_subject = None
        self.last_command_time = 0.0

    def context_is_live(self):
        return (
            self.active_subject == "lights"
            and (time.monotonic() - self.last_command_time) <= CONTEXT_SECONDS
        )

    def remember_lights(self):
        self.active_subject = "lights"
        self.last_command_time = time.monotonic()

    def parse(self, text):
        words = [word for word in text.lower().split() if word != "[unk]"]
        word_set = set(words)

        wake_word = bool({"robot", "spenser", "spencer"} & word_set)
        explicit_lights = bool({"light", "lights"} & word_set)
        using_context = not explicit_lights and self.context_is_live()

        # This test program only executes when the lights are explicitly named,
        # or when a recent lights command makes the subject deterministic.
        if not explicit_lights and not using_context:
            return None

        command = None

        if "off" in word_set:
            command = {
                "device": "lights",
                "action": "set_power",
                "value": "off"
            }

        elif "on" in word_set:
            command = {
                "device": "lights",
                "action": "set_power",
                "value": "on",
                "brightness": "last"
            }

        else:
            colours_found = [colour for colour in COLOURS if colour in word_set]

            if "warm" in word_set and "white" in word_set:
                command = {
                    "device": "lights",
                    "action": "set_color",
                    "value": "warm_white"
                }

            elif "cool" in word_set and "white" in word_set:
                command = {
                    "device": "lights",
                    "action": "set_color",
                    "value": "cool_white"
                }

            elif len(colours_found) == 1:
                command = {
                    "device": "lights",
                    "action": "set_color",
                    "value": colours_found[0]
                }

            elif "warmer" in word_set:
                command = {
                    "device": "lights",
                    "action": "adjust_color_temperature",
                    "direction": "warmer"
                }

            elif "cooler" in word_set:
                command = {
                    "device": "lights",
                    "action": "adjust_color_temperature",
                    "direction": "cooler"
                }

            else:
                brightness_found = [
                    name for name in BRIGHTNESS if name in word_set
                ]

                if len(brightness_found) == 1:
                    level = brightness_found[0]
                    command = {
                        "device": "lights",
                        "action": "set_brightness",
                        "value": BRIGHTNESS[level]
                    }

                elif "percent" in word_set:
                    percent_index = words.index("percent")
                    # Number words immediately before "percent" are enough.
                    number_words = []
                    for word in reversed(words[:percent_index]):
                        if word in ONES or word in TENS or word == "hundred" or word.isdigit():
                            number_words.insert(0, word)
                        elif number_words:
                            break

                    value = words_to_number(number_words)

                    if value is not None and 0 <= value <= 100:
                        command = {
                            "device": "lights",
                            "action": "set_brightness",
                            "value": value
                        }

        if command is None:
            return None

        command["wake_word"] = wake_word
        command["subject_source"] = "explicit" if explicit_lights else "context"
        self.remember_lights()
        return command


def execute_lights(command):
    """
    Test executor.

    For now this deliberately only prints the JSON that would be sent to the
    real light controller. Replace this function later with the hardware call.
    """
    print("EXECUTE:")
    print(json.dumps(command, indent=2))


print("Loading Vosk model...")
model = Model(MODEL_PATH)
recognizer = make_recognizer(model)
parser = LightCommandParser()
mic = start_microphone()

print()
print("Deterministic lights test ready.")
print(f"Lights context remains deterministic for {CONTEXT_SECONDS:.0f} seconds.")
print("Examples:")
print("  Spencer lights red")
print("  blue")
print("  medium")
print("  lights thirty seven percent")
print("  warmer")
print("Press Ctrl+C to stop.")
print()

try:
    while True:
        data = mic.stdout.read(2000)

        if not data:
            continue

        if recognizer.AcceptWaveform(data):
            result = json.loads(recognizer.Result())
            text = result.get("text", "").strip()

            if not text or text == "[unk]":
                continue

            print(f"HEARD: {text}")

            command = parser.parse(text)

            if command is not None:
                execute_lights(command)
            else:
                print("NO DETERMINISTIC LIGHT COMMAND")
                print("-> This is where the SLM would receive the utterance/context.")

            print()

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    if mic.poll() is None:
        mic.terminate()
