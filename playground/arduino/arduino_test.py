import serial
import time


# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

PORT = "/dev/ttyACM0"
BAUD = 9600

START_BYTE = 0xA1
END_BYTE = 0x55

MOUTH_COMMAND = 0xA5


# --------------------------------------------------
# SEND COMMAND
# --------------------------------------------------

def send_mouth(ser, value):

    high_byte = (value >> 8) & 0xFF
    low_byte = value & 0xFF

    packet = bytes([
        START_BYTE,
        MOUTH_COMMAND,
        high_byte,
        low_byte,
        END_BYTE
    ])

    ser.write(packet)

    print(f"PI -> ARDUINO: mouth = {value}")


# --------------------------------------------------
# OPEN ARDUINO
# --------------------------------------------------

print(f"Opening Arduino on {PORT}...")

ser = serial.Serial(
    PORT,
    BAUD,
    timeout=0.05
)

print("Port open.")
print("Waiting 5 seconds for Arduino startup...")

time.sleep(5)

print("Running - Ctrl+C to stop.\n")


# Mouth levels to cycle through
mouth_levels = [
    60,
    25,
    100,
    50,
    255,
    25,
    50,
    100
]

mouth_index = 0
last_mouth_time = time.time()


# --------------------------------------------------
# MAIN LOOP
# --------------------------------------------------

try:

    while True:

        # ------------------------------------------
        # PRINT ARDUINO OUTPUT
        # ------------------------------------------

        if ser.in_waiting:

            line = ser.readline()

            try:
                text = line.decode("utf-8").strip()
            except UnicodeDecodeError:
                text = repr(line)

            if text:
                print(f"ARDUINO -> PI: {text}")


        # ------------------------------------------
        # SEND MOUTH COMMAND EVERY SECOND
        # ------------------------------------------

        if time.time() - last_mouth_time >= 1:

            value = mouth_levels[mouth_index]

            send_mouth(ser, value)

            mouth_index += 1

            if mouth_index >= len(mouth_levels):
                mouth_index = 0

            last_mouth_time = time.time()


        time.sleep(0.01)


# --------------------------------------------------
# SHUTDOWN
# --------------------------------------------------

except KeyboardInterrupt:

    print("\nStopping...")

finally:

    send_mouth(ser, 0)

    ser.close()

    print("Serial port closed.")