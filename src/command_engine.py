"""
Generic robot command interpretation engine.

PURPOSE
-------
This module converts recognised speech text into structured robot commands.

It is deliberately independent of the speech recogniser. Moonshine, Vosk,
or any future speech system can pass text into CommandEngine.parse().

Robot capabilities are defined in the JSON files in /commands rather than
being hard-coded into the speech recogniser. Eventually these command
definitions should live with the subsystem that owns the capability.

Example:

    "Spencer lights green"

becomes approximately:

    subject = lights
    action  = colour
    value   = green


CURRENT CONTEXT BEHAVIOUR
-------------------------
The engine remembers the subject of the last successfully matched command
for CONTEXT_SECONDS.

For example:

    "Spencer lights on"
    "blue"

If "blue" is spoken within the context period, the engine remembers that
"lights" was the previous subject and interprets it as:

    lights -> colour -> blue

A successful follow-up command resets the subject-context timer.


FUTURE CONTEXT / ATTENTION IMPROVEMENTS
---------------------------------------
The current context system is intentionally simple and should eventually
be expanded.

1. Wake-word attention and subject context should have SEPARATE timers.

   Wake words such as "Spencer" and "robot" indicate that the speaker is
   addressing the robot. This attention state is conceptually different
   from remembering that the current subject is "lights", "volume", etc.

   For example:

       "Spencer"
       ...short pause...
       "turn the lights on"

   should use wake-word attention independently from subject memory.


2. Replace the hard subject timeout with decaying confidence.

   Currently subject context exists at full strength until CONTEXT_SECONDS
   expires, then disappears completely.

   A future version should give recent context a gradually decreasing
   likelihood/confidence instead.

   Conceptually:

       immediately after command -> very strong subject evidence
       a few seconds later       -> strong evidence
       considerably later        -> weak evidence
       much later                -> effectively no evidence

   A sigmoid/logistic-style decay was discussed as one possible model.

   This would allow context to contribute evidence rather than acting as
   a simple on/off switch.


3. Context should ultimately be one source of evidence, not absolute truth.

   Future command interpretation may combine:
       - explicit subject words
       - wake-word / attention state
       - previous subject context
       - time since previous command
       - command vocabulary matches
       - speech recognition confidence
       - speaker identity
       - semantic/SLM interpretation

   Clear deterministic commands should still take priority where possible.


CURRENT DESIGN
--------------
For now, keep this module simple and deterministic. The purpose of the
current implementation is to establish a working command pipeline before
adding more sophisticated confidence and conversational-context handling.
"""
import json
import time
import re
from pathlib import Path
import math


PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMAND_DIRECTORY = PROJECT_ROOT / "commands"

CONTEXT_SECONDS = 10.0
ATTENTION_SECONDS = 45.0

WAKE_WORDS = ["robot", "spencer", "spenser"]

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}

QUESTION_STARTERS = [
    "what",
    "why",
    "who",
    "where",
    "when",
    "how",
    "which",
    "whose",
]

QUESTION_PHRASES = [
    "do you",
    "are you",
    "can you",
    "could you",
    "would you",
    "will you",
    "have you",
    "did you",
    "tell me",
    "explain",
]

def looks_like_question(words):
    """Detect obvious questions or conversational requests."""

    if not words:
        return False

    if words[0] in QUESTION_STARTERS:
        return True

    for phrase in QUESTION_PHRASES:
        if phrase_present(words, phrase):
            return True

    return False


def load_definitions():
    definitions = {}

    for filename in COMMAND_DIRECTORY.glob("*.json"):
        with filename.open() as file:
            definition = json.load(file)

        definitions[definition["subject"]] = definition

    return definitions


def phrase_present(words, phrase):
    """Return True if a phrase occurs consecutively in words."""

    target = phrase.split()
    size = len(target)

    for index in range(len(words) - size + 1):
        if words[index:index + size] == target:
            return True

    return False


def parse_number(words):
    """Parse simple numbers from 0 to 100."""

    if not words:
        return None

    if words == ["hundred"] or words == ["one", "hundred"]:
        return 100

    if len(words) == 1:
        return NUMBER_WORDS.get(words[0])

    if len(words) == 2:
        first = NUMBER_WORDS.get(words[0])
        second = NUMBER_WORDS.get(words[1])

        if (
            first is not None
            and first in range(20, 100, 10)
            and second is not None
            and second < 10
        ):
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

    def __init__(self):
        self.definitions = load_definitions()

        self.last_subject = None
        self.pending_confirmation = None
        self.pending_confirmation_expires = None
        self.last_command_time = 0.0

        self.last_wake_time = 0.0

        print(
            "Loaded command subjects:",
            ", ".join(self.definitions)
        )

    def context_confidence(self):
            """
            Confidence in the remembered subject.

            Starts high immediately after a successful command
            and gradually falls as the context gets older.
            """

            if self.last_subject is None:
                return 0.0

            elapsed = time.monotonic() - self.last_command_time

            confidence = math.exp(-elapsed / 15.0)

            return round(confidence, 2)

    def attention_confidence(self):
        """
        Confidence that the user is still addressing the robot.

        Wake-word attention lasts longer than subject context.
        """

        if self.last_wake_time == 0.0:
            return 0.0

        elapsed = time.monotonic() - self.last_wake_time

        if elapsed > ATTENTION_SECONDS:
            return 0.0

        confidence = math.exp(-elapsed / 30.0)

        return round(confidence, 2)

    def confirmation_speech_finished(self):
        """Start the grace period after a confirmation question finishes speaking."""

        if self.pending_confirmation is not None:
            self.pending_confirmation_expires = time.monotonic() + 8.0

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
                        "matched": phrase,
                    })

            numeric = action.get("number_parameter")

            if numeric:

                value = find_number_before_suffix(
                    words,
                    numeric["suffix"]
                )

                if (
                    value is not None
                    and numeric["min"] <= value <= numeric["max"]
                ):

                    matches.append({
                        "subject": definition["subject"],
                        "action": action_name,
                        "value": value,
                        "matched": f'{value} {numeric["suffix"]}',
                    })

        return matches

    def parse(self, text):

        # Remove punctuation added by the speech recogniser.
        # For example: "lights." becomes "lights"
        # and "Spencer." becomes "Spencer".
        clean_text = re.sub(r"[^\w\s]", "", text.lower())

        all_words = clean_text.split()


        # Check whether the user is answering a pending question.
        # Check whether the user is answering a pending question.
        if self.pending_confirmation is not None:

            # Check whether the user is answering a pending question.
            if self.pending_confirmation is not None:

                # If the confirmation question has finished speaking,
                # check whether its 5-second grace period has expired.
                if (
                    self.pending_confirmation_expires is not None
                    and time.monotonic() > self.pending_confirmation_expires
                ):
                    self.pending_confirmation = None
                    self.pending_confirmation_expires = None

                elif any(
                    word in ["yes", "yeah", "yep", "sure", "okay", "ok"]
                    for word in all_words
                ):

                    command = self.pending_confirmation
                    self.pending_confirmation = None
                    self.pending_confirmation_expires = None

                    return {
                        "status": "matched",
                        "subject": command["subject"],
                        "action": command["action"],
                        "value": command["value"],
                        "matched": clean_text,
                        "subject_source": "confirmation",
                        "confidence": 1.0,
                        "attention_confidence": self.attention_confidence(),
                    }

                elif any(
                    word in ["no", "nope", "cancel"]
                    for word in all_words
                ):

                    self.pending_confirmation = None
                    self.pending_confirmation_expires = None

                    return {
                        "status": "confirmation_cancelled",
                        "heard": text,
                    }


        wake_detected = any(
            word in WAKE_WORDS
            for word in all_words
        )

        if wake_detected:
            self.last_wake_time = time.monotonic()

        words = [
            word
            for word in all_words
            if word not in WAKE_WORDS
        ]

        explicit_subject = self.find_explicit_subject(words)

        subject = explicit_subject or self.recent_subject()

        if subject is None:

            if wake_detected and looks_like_question(words):

                big_brain = self.definitions.get("big_brain")

                if big_brain:
                    fallback = big_brain.get("fallback", {})
                    confirmation = fallback.get("confirmation", {})
                    self.pending_confirmation = {
                        "subject": "big_brain",
                        "action": confirmation.get("action"),
                        "value": confirmation.get("parameter"),
                    }

                    return {
                        "status": "confirmation_required",
                        "heard": text,
                        "subject": "big_brain",
                        "action": confirmation.get("action"),
                        "value": confirmation.get("parameter"),
                        "prompt": confirmation.get("prompt"),
                    }

            return {
                "status": "not_deterministic",
                "heard": text,
            }

        definition = self.definitions[subject]

        matches = self.find_action_matches(
            definition,
            words
        )

       

        if len(matches) != 1:

            return {
                "status": "ambiguous",
                "heard": text,
                "subject": subject,
                "matches": matches,
            }

        command = matches[0]

        command["status"] = "matched"

        command["subject_source"] = (
            "explicit"
            if explicit_subject
            else "context"
        )

        # Explicitly naming the subject gives maximum confidence.
        # If the subject came from context, confidence decays
        # according to how old that context is.
        if explicit_subject:
            command["confidence"] = 1.0
        else:
            command["confidence"] = self.context_confidence()
        command["attention_confidence"] = self.attention_confidence()

        # A successful command refreshes the subject context.
        # Do this AFTER calculating confidence so that contextual
        # commands use the age of the previous command.
        self.last_subject = subject
        self.last_command_time = time.monotonic()

        return command