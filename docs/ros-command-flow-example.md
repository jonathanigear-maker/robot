# ROS command flow example: "Go to sleep"

This is a deliberately simple example showing how a spoken command can travel through ROS and eventually reach the Arduino.

## Example flow

```text
"go to sleep"
    |
    v
Vosk / voice_node
    |
    | publishes "closed"
    v
/eyes/position
    |
    v
eye_controller
    |
    | publishes "EYES,STATE,SET,CLOSED"
    v
/arduino/command
    |
    v
arduino_controller
    |
    | USB serial
    v
Arduino
    |
    v
ESP32 eyes
```

This example uses `std_msgs/String` to make the data flow easy to understand. More structured ROS message types can be introduced later.

## 1. Voice node

The voice node receives recognized text from Vosk. For this simple example it recognizes the exact intent "go to sleep" and requests that the eyes close.

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class VoiceNode(Node):
    def __init__(self):
        super().__init__('voice_node')
        self.eye_publisher = self.create_publisher(
            String, '/eyes/position', 10
        )

    def process_vosk_text(self, text):
        print("Vosk heard:", text)

        if "go to sleep" in text:
            message = String()
            message.data = "closed"
            self.eye_publisher.publish(message)
```

Vosk does not need to know how the eyes are physically connected.

## 2. Eye controller

The eye controller owns the eye state. It receives requests and decides what command should ultimately be sent to the hardware.

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class EyeController(Node):
    def __init__(self):
        super().__init__('eye_controller')

        self.subscription = self.create_subscription(
            String,
            '/eyes/position',
            self.eye_callback,
            10
        )

        self.arduino_publisher = self.create_publisher(
            String,
            '/arduino/command',
            10
        )

    def eye_callback(self, message):
        print("Eye request:", message.data)

        if message.data == "closed":
            command = String()
            command.data = "EYES,STATE,SET,CLOSED"
            self.arduino_publisher.publish(command)

def main():
    rclpy.init()
    node = EyeController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## 3. Arduino interface/controller node

Only this node needs to own the USB serial connection. Other ROS nodes communicate with it through ROS rather than opening the serial port themselves.

```python
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial

class ArduinoController(Node):
    def __init__(self):
        super().__init__('arduino_controller')

        self.serial = serial.Serial(
            '/dev/ttyACM0',
            115200,
            timeout=0.1
        )

        self.subscription = self.create_subscription(
            String,
            '/arduino/command',
            self.command_callback,
            10
        )

    def command_callback(self, message):
        command = message.data
        print("Sending to Arduino:", command)
        self.serial.write((command + '\n').encode())

def main():
    rclpy.init()
    node = ArduinoController()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

## 4. Arduino

The Arduino receives one human-readable command per serial line.

```cpp
String serialMessage = "";

void setup() {
  Serial.begin(115200);
}

void loop() {
  if (Serial.available()) {
    serialMessage = Serial.readStringUntil('\n');
    processCommand(serialMessage);
  }
}

void processCommand(String message) {
  if (message == "EYES,STATE,SET,CLOSED") {
    closeEyes();
  }
}

void closeEyes() {
  Serial.println("Closing eyes");

  // Existing I2C command to the ESP32 eye controllers
  // will eventually go here.
}
```

## Why have a separate Arduino node?

It is possible for `eye_controller` to open the serial port directly. For a tiny robot that could work.

For this robot, however, many systems will need the Arduino: eyes, NeoPixels, encoder/button events, peripheral health, and eventually other hardware. A single `arduino_controller` (better thought of as an Arduino interface/bridge) can own the serial port and translate between ROS messages and the Arduino serial protocol.

That avoids multiple ROS nodes competing for one serial port and keeps hardware transport separate from behaviour.

## Future improvement: behaviours such as sleep

"Sleep" should eventually be treated as a robot-level behaviour rather than something Vosk or the eye controller has to understand.

A future flow could be:

```text
Vosk -> recognized speech
          |
          v
command / behaviour interpreter
          |
          | "sleep"
          v
behaviour controller
       /       |       \
      v        v        v
   eyes      LEDs      arm/head
   close      dim      sleep pose
```

Vosk's responsibility is speech recognition. A command/SLM layer interprets the words as an intent such as `sleep`. A behaviour controller can then coordinate the multiple subsystem requests needed for sleep. Each subsystem controller remains responsible for its own hardware and state.

This keeps responsibilities separated:

- Vosk: what words were spoken?
- SLM/command interpreter: what did the user mean?
- Behaviour controller: what robot-wide actions make up that behaviour?
- Eye/LED/arm controllers: what should their subsystem do?
- Arduino interface: how do ROS commands/events cross the USB serial link?
- Arduino: reliably operate the physical hardware.
