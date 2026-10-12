import serial
import threading
import time
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray
from geometry_msgs.msg import Point

SERIAL_PORT = "/dev/serial/by-id/usb-Arduino_LLC_Arduino_Nano_Every_BC560AB251544E5450202020FF0E3E0D-if00"
BAUD_RATE = 9600


# Persistent connection
_ser = None
_running = False
_reader_thread = None
_show_serial = True
_ros_node = None
_lidar_publisher = None
_servo_publisher = None
_vision_publisher = None

def publish_sensor(data):
    """Publish Arduino sensor data to ROS 2."""

    # --------------------------------------------------
    # 4x4 LiDAR - 16 distances in millimetres
    # --------------------------------------------------
    if data["type"] == "lidar" and _lidar_publisher is not None:
        msg = Int32MultiArray()
        msg.data = data["distances"]
        _lidar_publisher.publish(msg)

    # --------------------------------------------------
    # Servos - 6 raw servo positions
    # --------------------------------------------------
    elif data["type"] == "servos" and _servo_publisher is not None:
        msg = Int32MultiArray()
        msg.data = data["positions"]
        _servo_publisher.publish(msg)

    # --------------------------------------------------
    # HuskyLens - detected target centre X/Y
    # --------------------------------------------------
    elif data["type"] == "vision" and _vision_publisher is not None:
        msg = Point()
        msg.x = float(data["x"])
        msg.y = float(data["y"])
        msg.z = 0.0

        _vision_publisher.publish(msg)

def start(show_serial=True):
    """Open the Arduino connection and start the background reader."""

    global _ser, _running, _reader_thread, _show_serial, _ros_node, _lidar_publisher

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

def parse_message(text):
    """Convert an Arduino serial message into structured data."""

    parts = text.split()

    if not parts:
        return None

    message_type = parts[0]

    try:
        if message_type == "LIDAR" and len(parts) == 17:
            return {
                "type": "lidar",
                "distances": [int(v) for v in parts[1:]]
            }

        if message_type == "SERVOS" and len(parts) == 7:
            return {
                "type": "servos",
                "positions": [int(v) for v in parts[1:]]
            }

        if message_type == "VISION" and len(parts) == 3:
            return {
                "type": "vision",
                "x": int(parts[1]),
                "y": int(parts[2])
            }

    except ValueError:
        return None

    return None


def _serial_reader():
    """Continuously read messages coming from the Arduino."""

    global _ros_node, _lidar_publisher
    global _servo_publisher, _vision_publisher

    _ros_node = Node("spencer_arduino")

    # 4x4 LiDAR
    _lidar_publisher = _ros_node.create_publisher(
        Int32MultiArray,
        "/spencer/lidar_4x4",
        10
    )

    # Servo positions
    _servo_publisher = _ros_node.create_publisher(
        Int32MultiArray,
        "/spencer/servos",
        10
    )

    # HuskyLens vision
    _vision_publisher = _ros_node.create_publisher(
        Point,
        "/spencer/vision",
        10
    )

    print("ARDUINO: ROS 2 publishers ready.")

    
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


                if text:
                    data = parse_message(text)

                    if data is not None:
                        if _show_serial:
                            print(f"PARSED: {data}")
                        publish_sensor(data)

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
    """Stop Arduino communication and clean up ROS resources."""

    global _running, _ser, _reader_thread
    global _ros_node, _lidar_publisher
    global _servo_publisher, _vision_publisher
    print("ARDUINO: Stopping...")

    # Tell the serial reader to stop
    _running = False

    # Wait for the reader thread to finish
    if _reader_thread is not None:
        _reader_thread.join()
        _reader_thread = None

    # Close serial connection
    if _ser is not None and _ser.is_open:
        _ser.close()

    _ser = None

    # Destroy ROS node only after reader has stopped
    if _ros_node is not None:
        _ros_node.destroy_node()
        _ros_node = None
        _lidar_publisher = None

    print("ARDUINO: Disconnected.")