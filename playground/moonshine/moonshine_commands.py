import time
import threading
from moonshine_voice import MicTranscriber
from src.command_engine import CommandEngine
from src.voice_feedback import command_accepted, big_brain_confirmation
from src.big_brain import open as open_big_brain

engine = CommandEngine()

def watch_voice_finished(process):
    if process is None:
        return

    process.wait()

    print("VOICE FINISHED")
    engine.confirmation_speech_finished()

def switch_to_big_brain():
    # Give heard_line() time to return
    time.sleep(0.2)

    print("MOONSHINE: Releasing microphone...")
    mic.close()

    print("MOONSHINE: Microphone released.")

    open_big_brain()

    print("MOONSHINE: Reloading...")
    mic.load()
    mic.start()

    print("MOONSHINE: Listening again.")

def heard_line(line):
    text = line.text
    command = engine.parse(text)

    print()
    print("HEARD:  ", text)
    print("COMMAND:", command)
    print()

    if command["status"] == "matched":

        if (
            command["subject"] == "big_brain"
            and command["action"] == "open"
        ):
            threading.Thread(
                target=switch_to_big_brain,
                daemon=True,
            ).start()

        else:
            command_accepted()
    elif command["status"] == "confirmation_required":
        voice_process = big_brain_confirmation()

        threading.Thread(
            target=watch_voice_finished,
            args=(voice_process,),
            daemon=True,
        ).start()


mic = (
    MicTranscriber()
    .language("en")
    .update_interval(0.25)
    .options({
        "vad_window_duration": "0.25"
    })
    .on_line(heard_line)
)

print("Loading Moonshine...")
mic.load()

print("Listening...")
mic.start()

try:
    while True:
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")