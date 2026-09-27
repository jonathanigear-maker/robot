import time

from src import arduino_comms
from src import respeaker
from src import moonshine
from src import audio_output

def main():
    print("Starting robot...")

    arduino_comms.start(show_serial=True)
    respeaker.start()
    moonshine.start()
    print("Robot running.")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping robot...")

        moonshine.stop()
        audio_output.stop_stream()
        respeaker.stop()
        arduino_comms.stop()


if __name__ == "__main__":
    main()