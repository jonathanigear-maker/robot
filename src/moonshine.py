import threading

from moonshine_voice import (
    Transcriber,
    get_model_for_language,
    LineCompleted,
)

from src import respeaker
from src.command_engine import CommandEngine
from src.voice_feedback import command_accepted, big_brain_confirmation
from src.big_brain import open as open_big_brain
from src import arduino_comms
from src import lights_functions
# ===========================================================================
# MOONSHINE - LOCAL SPEECH RECOGNITION
# ===========================================================================
#
# This module handles the robot's LOCAL speech recognition.
#
# IMPORTANT:
# Moonshine does NOT own or open the physical microphone.
#
# The ReSpeaker is opened once by src/respeaker.py. Audio blocks from that
# microphone are then distributed to whichever parts of the robot need them.
#
# Current audio path:
#
#       ReSpeaker hardware
#              │
#              ▼
#        respeaker.py
#              │
#              ▼
#        moonshine.py
#              │
#              ▼
#        CommandEngine
#
#
# Later the same ReSpeaker stream may also feed:
#
#       ├── Moonshine
#       ├── Big Brain / OpenAI
#       ├── VAD
#       └── direction-of-arrival processing
#
# This avoids different parts of the robot repeatedly opening and closing
# the microphone.
# ===========================================================================


# ---------------------------------------------------------------------------
# COMMAND ENGINE
# ---------------------------------------------------------------------------
#
# CommandEngine takes recognised text and decides whether it corresponds
# to one of the robot's deterministic commands.
#
# For example:
#
#       spoken words
#            ↓
#       "turn the laser on"
#            ↓
#       CommandEngine
#            ↓
#       structured command
#
# ---------------------------------------------------------------------------

engine = CommandEngine()


# ---------------------------------------------------------------------------
# MOONSHINE STATE
# ---------------------------------------------------------------------------
#
# These objects are created by start().
#
# They are deliberately NOT created when this module is imported.
# robot.py should control when each robot subsystem starts and stops.
# ---------------------------------------------------------------------------

_transcriber = None
_stream = None
_running = False
pending_big_brain_question = None


# ===========================================================================
# VOICE FEEDBACK
# ===========================================================================

def watch_voice_finished(process):
    """
    Wait for a spoken confirmation message to finish.

    Some commands cause the robot to ask the user for confirmation.

    CommandEngine needs to know when that spoken question has finished so
    that it can begin interpreting the user's next response as the answer.
    """

    if process is None:
        return

    process.join()

    print("VOICE FINISHED")

    engine.confirmation_speech_finished()


# ===========================================================================
# BIG BRAIN / OPENAI
# ===========================================================================

def switch_to_big_brain():
    """
    Start the Big Brain / OpenAI conversation system.

    OLD BEHAVIOUR
    -------------

    Moonshine previously owned the microphone itself, so this function had
    to do:

        close Moonshine microphone
        start Big Brain
        reopen Moonshine microphone

    NEW BEHAVIOUR
    -------------

    respeaker.py now owns the physical microphone permanently.

    Therefore Moonshine does NOT need to close the microphone here.

    Big Brain still needs to be refactored to consume audio from
    respeaker.py. Once that is done we will also control which consumer
    receives the audio while Big Brain is active.

    Eventually this will probably look conceptually like:

        Moonshine listening
              ↓
        "open big brain"
              ↓
        Moonshine paused
              ↓
        Big Brain receives ReSpeaker audio
              ↓
        Big Brain finishes
              ↓
        Moonshine resumed
    """

    print("MOONSHINE: Opening Big Brain...")
    print("PASSING TO BIG BRAIN:", repr(pending_big_brain_question))
    open_big_brain(pending_big_brain_question)

    print("MOONSHINE: Big Brain finished.")


# ===========================================================================
# COMMAND PROCESSING
# ===========================================================================

def heard_line(line):
    """
    Process one completed line of speech recognised by Moonshine.

    Moonshine supplies a TranscriptLine object.

    line.text contains the actual recognised words.
    """
    global pending_big_brain_question
    text = line.text

    # Ask CommandEngine what the recognised speech means.
    command = engine.parse(text)

    print()
    print("HEARD:  ", text)
    print("COMMAND:", command)
    print()

    # -----------------------------------------------------------------------
    # A normal command was successfully recognised.
    # -----------------------------------------------------------------------

    if command["status"] == "matched":

        # Big Brain is slightly different from normal robot commands because
        # it starts an interactive AI conversation.
        #
        # Run it in another thread so that this Moonshine callback can return
        # immediately rather than being blocked for the whole conversation.

        if (
            command["subject"] == "big_brain"
            and command["action"] == "open"
        ):
            threading.Thread(
                target=switch_to_big_brain,
                daemon=True,
            ).start()

        elif command["subject"] == "lights":
            lights_functions.handle(
                command["action"],
                command["value"],
            )
            command_accepted()

        else:
            command_accepted()

    # -----------------------------------------------------------------------
    # CommandEngine needs the user to confirm something.
    # -----------------------------------------------------------------------

    elif command["status"] == "confirmation_required":

        pending_big_brain_question = text
        print("PENDING BIG BRAIN QUESTION:", pending_big_brain_question)
        voice_process = big_brain_confirmation()

        # Wait for the spoken confirmation question to finish in another
        # thread. This prevents the Moonshine callback from blocking.
        threading.Thread(
            target=watch_voice_finished,
            args=(voice_process,),
            daemon=True,
        ).start()


# ===========================================================================
# MOONSHINE EVENTS
# ===========================================================================

def moonshine_event(event):
    """
    Receive transcription events from Moonshine.

    Moonshine can generate several different event types.

    At the moment we only care about LineCompleted, which means Moonshine
    has decided that a complete utterance has finished.

    Keeping this event handler separate makes it easy to add other event
    types later if we want them.
    """

    if isinstance(event, LineCompleted):
        heard_line(event.line)


# ===========================================================================
# AUDIO INPUT
# ===========================================================================

def add_audio(audio, sample_rate):
    """
    Receive one microphone audio block from respeaker.py.

    This function is registered as a ReSpeaker consumer by start().

    respeaker.py repeatedly calls:

        add_audio(audio, sample_rate)

    'audio' is currently a mono NumPy float32 array.

    'sample_rate' is currently 16000 Hz.

    We simply pass that block into Moonshine's streaming recogniser.
    """

    if not _running:
        return

    if _stream is None:
        return

    _stream.add_audio(audio, sample_rate)


# ===========================================================================
# START
# ===========================================================================

def start():
    """
    Start Moonshine speech recognition.

    This does NOT open the microphone.

    The ReSpeaker should already have been started by robot.py.
    """

    global _transcriber
    global _stream
    global _running

    # Protect against accidentally starting Moonshine twice.
    if _running:
        return

    print("MOONSHINE: Loading model...")

    # Ask Moonshine for its recommended English model.
    #
    # This preserves the behaviour of the old:
    #
    #       MicTranscriber().language("en")
    #
    # rather than hard-coding the model's location.
    model_path, model_arch = get_model_for_language("en")

    print(f"MOONSHINE: Model: {model_path}")

    # Create the actual Moonshine speech recogniser.
    #
    # vad_window_duration is copied from our previous MicTranscriber setup.
    _transcriber = Transcriber(
        str(model_path),
        model_arch,
        options={
            "vad_window_duration": "0.25",
        },
    )

    # Create a real-time transcription stream.
    #
    # The old MicTranscriber used:
    #
    #       update_interval(0.25)
    #
    # so we preserve that setting here.
    _stream = _transcriber.create_stream(
        update_interval=0.25,
    )

    # Listen for Moonshine transcription events.
    #
    # Previously MicTranscriber.on_line() did this for us internally.
    # Now that we are using the lower-level stream directly, we attach the
    # listener ourselves.
    _stream.add_listener(moonshine_event)
    _stream.start()
    # Mark Moonshine as active before audio starts arriving.
    _running = True

    # Tell respeaker.py that Moonshine wants microphone audio.
    #
    # From this point on, each captured audio block will eventually result in:
    #
    #       add_audio(audio, sample_rate)
    #
    respeaker.add_consumer(add_audio)

    print("MOONSHINE: Listening.")


# ===========================================================================
# STOP
# ===========================================================================

def stop():
    """
    Stop Moonshine speech recognition.

    This unregisters Moonshine from the shared ReSpeaker audio stream.

    It does NOT close the physical microphone. respeaker.py owns that and
    robot.py will stop it separately during shutdown.
    """

    global _transcriber
    global _stream
    global _running

    if not _running:
        return

    print("MOONSHINE: Stopping...")

    # Stop accepting new audio first.
    _running = False

    # Remove Moonshine from the ReSpeaker consumer list.
    respeaker.remove_consumer(add_audio)

    # Release Moonshine's streaming transcription resources.
    if _stream is not None:
        _stream.close()
        _stream = None

    # Release the loaded Moonshine model.
    if _transcriber is not None:
        _transcriber.close()
        _transcriber = None

    print("MOONSHINE: Stopped.")


def pause():
    """Temporarily stop sending microphone audio to Moonshine."""

    if not _running:
        return

    respeaker.remove_consumer(add_audio)

    print("MOONSHINE: Paused.")


def resume():
    """Resume sending microphone audio to Moonshine."""

    if not _running:
        return

    respeaker.add_consumer(add_audio)

    print("MOONSHINE: Listening.")