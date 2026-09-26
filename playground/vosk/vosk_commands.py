import subprocess
import json
import time
from pathlib import Path

from vosk import Model, KaldiRecognizer

FULL_MODEL_PATH = "/home/sodigece/robot/models/vosk-model-en-us-0.22-lgraph"
SPECIALIST_MODEL_PATH = "/home/sodigece/robot/models/vosk-model-small-en-gb-0.15"
SAMPLE_RATE = 16000
COMMAND_DIRECTORY = Path(__file__).parent / "commands"
CONTEXT_SECONDS = 15.0

WAKE_WORDS = ["robot", "spencer", "spenser"]

NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100
}


def load_definitions():
    definitions = {}

    for filename in COMMAND_DIRECTORY.glob("*.json"):
        with filename.open() as file:
            definition = json.load(file)

        definitions[definition["subject"]] = definition

    return definitions


def build_grammar(definitions):
    """
    Build constrained Vosk vocabulary entirely from the command JSON files.
    Device names, action parameters and suffixes are NOT hard-coded here.
    """
    grammar = set(WAKE_WORDS)

    for definition in definitions.values():
        for alias in definition.get("aliases", []):
            grammar.update(alias.split())

        for action in definition.get("actions", {}).values():
            for phrase in action.get("parameters", {}):
                grammar.update(phrase.split())

            numeric = action.get("number_parameter")
            if numeric:
                grammar.update(numeric["suffix"].split())
                grammar.update(NUMBER_WORDS.keys())

    grammar.add("[unk]")
    return sorted(grammar)


def phrase_present(words, phrase):
    """True if a one- or multi-word phrase occurs consecutively."""
    target = phrase.split()
    size = len(target)

    for index in range(len(words) - size + 1):
        if words[index:index + size] == target:
            return True

    return False


def parse_number(words):
    """Parse the simple 0-100 number vocabulary used by this test."""
    if not words:
        return None

    if words == ["hundred"] or words == ["one", "hundred"]:
        return 100

    if len(words) == 1:
        return NUMBER_WORDS.get(words[0])

    if len(words) == 2:
        first = NUMBER_WORDS.get(words[0])
        second = NUMBER_WORDS.get(words[1])

        if first in range(20, 100, 10) and second is not None and second < 10:
            return first + second

    return None


def find_number_before_suffix(words, suffix):
    suffix_words = suffix.split()
    size = len(suffix_words)

    for index in range(len(words) - size + 1):
        if words[index:index + size] != suffix_words:
            continue

        candidates = []

        for word in reversed(words[:index]):
            if word in NUMBER_WORDS:
                candidates.insert(0, word)
                if len(candidates) == 2:
                    break
            elif candidates:
                break

        return parse_number(candidates)

    return None


class CommandEngine:
    def __init__(self, definitions):
        self.definitions = definitions
        self.last_subject = None
        self.last_command_time = 0.0

    def recent_subject(self):
        if self.last_subject is None:
            return None

        if time.monotonic() - self.last_command_time > CONTEXT_SECONDS:
            return None

        return self.last_subject

    def find_explicit_subject(self, words):
        matches = []

        for subject, definition in self.definitions.items():
            if any(
                phrase_present(words, alias)
                for alias in definition.get("aliases", [])
            ):
                matches.append(subject)

        if len(matches) == 1:
            return matches[0]

        return None

    def find_action_matches(self, definition, words):
        matches = []

        for action_name, action in definition.get("actions", {}).items():

            for phrase, value in action.get("parameters", {}).items():
                if phrase_present(words, phrase):
                    matches.append({
                        "subject": definition["subject"],
                        "action": action_name,
                        "value": value,
                        "matched": phrase
                    })

            numeric = action.get("number_parameter")
            if numeric:
                value = find_number_before_suffix(words, numeric["suffix"])

                if (
                    value is not None
                    and numeric["min"] <= value <= numeric["max"]
                ):
                    matches.append({
                        "subject": definition["subject"],
                        "action": action_name,
                        "value": value,
                        "matched": f'{value} {numeric["suffix"]}'
                    })

        return matches

    def parse(self, text):
        words = [
            word for word in text.lower().split()
            if word != "[unk]" and word not in WAKE_WORDS
        ]

        explicit_subject = self.find_explicit_subject(words)
        subject = explicit_subject or self.recent_subject()

        if subject is None:
            return {
                "status": "not_deterministic",
                "heard": text
            }

        definition = self.definitions[subject]
        matches = self.find_action_matches(definition, words)

        # Deterministic means exactly one possible command.
        if len(matches) != 1:
            return {
                "status": "ambiguous",
                "heard": text,
                "subject": subject,
                "matches": matches
            }

        command = matches[0]
        command["status"] = "matched"
        command["subject_source"] = (
            "explicit" if explicit_subject else "context"
        )

        self.last_subject = subject
        self.last_command_time = time.monotonic()

        return command


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


definitions = load_definitions()
grammar = build_grammar(definitions)

print("Loaded command subjects:", ", ".join(definitions))
print("Vosk grammar:")
print(" ".join(grammar))
print()

print("Loading full Vosk model...")
full_model = Model(FULL_MODEL_PATH)

print("Loading specialist Vosk model...")
specialist_model = Model(SPECIALIST_MODEL_PATH)

# Full recognizer: larger unrestricted model
full_recognizer = KaldiRecognizer(full_model, SAMPLE_RATE)
full_recognizer.SetWords(True)

# Specialist recognizer: small British model + JSON command grammar
specialist_recognizer = KaldiRecognizer(
    specialist_model,
    SAMPLE_RATE,
    json.dumps(grammar)
)

specialist_recognizer.SetWords(True)

engine = CommandEngine(definitions)
mic = start_microphone()

print("Generic deterministic command test ready.")
print("Press Ctrl+C to stop.")
print()

try:
    while True:
        data = mic.stdout.read(2000)

        if not data:
            continue

        # Time how long each recogniser takes to process this audio chunk.
        t0 = time.perf_counter()
        full_final = full_recognizer.AcceptWaveform(data)
        t1 = time.perf_counter()

        specialist_final = specialist_recognizer.AcceptWaveform(data)
        t2 = time.perf_counter()

        full_chunk_time = t1 - t0
        specialist_chunk_time = t2 - t1

        # Report unusually slow chunks immediately.
        # This helps us see whether either recogniser is falling behind
        # while audio is arriving.
        if full_chunk_time > 0.1 or specialist_chunk_time > 0.1:
            print(
                f"[CHUNK] full={full_chunk_time:.3f}s  "
                f"specialist={specialist_chunk_time:.3f}s"
            )

        # The full recogniser defines the utterance boundary for this test.
        if full_final:
            endpoint_time = time.perf_counter()

            # Time retrieval of the full result.
            result_start = time.perf_counter()
            full_result = json.loads(full_recognizer.Result())
            full_result_time = time.perf_counter() - result_start

            # Keep the specialist recogniser aligned with the same utterance.
            specialist_result_start = time.perf_counter()

            if specialist_final:
                specialist_result = json.loads(
                    specialist_recognizer.Result()
                )
            else:
                specialist_result = json.loads(
                    specialist_recognizer.FinalResult()
                )

            specialist_result_time = (
                time.perf_counter() - specialist_result_start
            )

            processing_after_endpoint = (
                time.perf_counter() - endpoint_time
            )

            full_text = full_result.get("text", "").strip()
            specialist_text = specialist_result.get("text", "").strip()

            if not full_text:
                continue

            print()
            print("HEARD (full):", full_text)
            print("SPECIALIST:", specialist_text or "<nothing>")

            print("\nTIMING:")
            print(
                f"  last full chunk:       "
                f"{full_chunk_time:.3f}s"
            )
            print(
                f"  last specialist chunk: "
                f"{specialist_chunk_time:.3f}s"
            )
            print(
                f"  full Result():          "
                f"{full_result_time:.3f}s"
            )
            print(
                f"  specialist result:      "
                f"{specialist_result_time:.3f}s"
            )
            print(
                f"  after endpoint total:   "
                f"{processing_after_endpoint:.3f}s"
            )

            print("\nFULL WORDS:")
            for word in full_result.get("result", []):
                print(
                    f'  {word["word"]:<15} '
                    f'conf={word.get("conf", 0.0):.3f} '
                    f'{word.get("start", 0.0):.2f}-'
                    f'{word.get("end", 0.0):.2f}'
                )

            print("\nSPECIALIST WORDS:")
            specialist_words = specialist_result.get("result", [])

            if specialist_words:
                for word in specialist_words:
                    print(
                        f'  {word["word"]:<15} '
                        f'conf={word.get("conf", 0.0):.3f} '
                        f'{word.get("start", 0.0):.2f}-'
                        f'{word.get("end", 0.0):.2f}'
                    )
            else:
                print("  <nothing>")

            # For now the command parser uses the specialist transcript.
            command = engine.parse(specialist_text)

            print("\nCOMMAND:")
            print(json.dumps(command, indent=2))

            if command["status"] == "matched":
                print("-> EXECUTE")
            else:
                print("-> SLM / further interpretation")

            print()

except KeyboardInterrupt:
    print("\nStopped.")

finally:
    if mic.poll() is None:
        mic.terminate()
