import time
import rclpy

from src import arduino_comms
from src import respeaker
from src import moonshine
from src import audio_output
from rclpy.signals import SignalHandlerOptions

def main():
    print("Starting robot...")

    try:
        # Initialise ROS 2
        rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
        print("ROS 2 initialised.")

        # Start Spencer's systems
        arduino_comms.start(show_serial=False)
        respeaker.start()
        moonshine.start()

        print("Robot running.")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping robot...")

    finally:
        print("Shutting down Spencer...")

        # Stop microphone callbacks before closing Moonshine.
        respeaker.stop()

        # Now safe to release Moonshine's resources.
        moonshine.stop()

        audio_output.stop_stream()

        # Stop Arduino after modules that might send commands.
        arduino_comms.stop()

        if rclpy.ok():
            rclpy.shutdown()

        print("ROS 2 stopped.")
        print("Robot stopped.")


if __name__ == "__main__":
    main()