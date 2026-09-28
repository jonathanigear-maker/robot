import serial
import threading
import time


SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600


# Persistent connection
_ser = None
_running = False
_reader_thread = None
_show_serial = True


def start(show_serial=True):
    """Open the Arduino connection and start the background reader."""

    global _ser, _running, _reader_thread, _show_serial

    _show_serial = show_serial

    print(f"ARDUINO: Opening {SERIAL_PORT}...")

    _ser = serial.Serial(
        SERIAL_PORT,
        BAUD_RATE,
        timeout=0.1
    )

    _running = True

    _reader_thread = threading.Thread(
        target=_serial_reader,
        daemon=True
    )

    _reader_thread.start()

    print("ARDUINO: Connected.")


def _serial_reader():
    """Continuously read messages coming from the Arduino."""

    while _running:
        try:
            if _ser.in_waiting:
                line = _ser.readline()

                text = line.decode(
                    "utf-8",
                    errors="replace"
                ).strip()

                if text and _show_serial:
                    print(f"ARDUINO: {text}")
            else:
                time.sleep(0.01)

        except serial.SerialException as e:
            print(f"ARDUINO ERROR: {e}")
            break


def send(command):
    """Send a text command to the Arduino."""

    if _ser is None or not _ser.is_open:
        print("ARDUINO ERROR: Serial connection is not open.")
        return

    message = f"{command}\n"

    _ser.write(message.encode("utf-8"))


def send_mouth_level(level):
    """Send speech amplitude, 0-255."""

    level = max(0, min(255, int(level)))

    send(f"MOUTH {level}")


def send_lights(hue, colour_brightness, white_brightness):
    """Set the RGBW rings. All values are 0-255."""

    hue = max(0, min(255, int(hue)))
    colour_brightness = max(0, min(255, int(colour_brightness)))
    white_brightness = max(0, min(255, int(white_brightness)))

    send(f"LIGHTS {hue} {colour_brightness} {white_brightness}")


def stop():
    """Stop Arduino communication and close the serial port."""

    global _running, _ser

    _running = False

    if _ser is not None and _ser.is_open:
        _ser.close()

    _ser = None

    print("ARDUINO: Disconnected.")