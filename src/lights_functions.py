from src import arduino_comms


# ===========================================================================
# LIGHT STATE
# ===========================================================================

# Colour hues use the Arduino's 0-255 colour wheel.
COLOURS = {
    "red": 0,
    "orange": 21,
    "yellow": 42,
    "green": 85,
    "blue": 170,
    "indigo": 191,
    "violet": 213,
}

# Remember colour and white brightness separately.
_mode = "colour"
_hue = COLOURS["blue"]
_colour_brightness = 50
_white_brightness = 50
_power = False

BRIGHTNESS_STEP = 10


# ===========================================================================
# OUTPUT
# ===========================================================================

def _send():
    """Send the current light state to the Arduino."""

    if not _power:
        arduino_comms.send_lights(0, 0, 0)
        return

    if _mode == "white":
        white = round(_white_brightness * 255 / 100)
        arduino_comms.send_lights(0, 0, white)
        return

    colour = round(_colour_brightness * 255 / 100)
    arduino_comms.send_lights(_hue, colour, 0)


# ===========================================================================
# COMMAND HANDLING
# ===========================================================================

def handle(action, value):
    """Apply a lights command from CommandEngine."""

    global _mode
    global _hue
    global _colour_brightness
    global _white_brightness
    global _power

    if action == "power":
        if value == "on":
            _power = True
        elif value == "off":
            _power = False

    elif action == "colour":
        if value == "white":
            _mode = "white"
            _power = True

        elif value in COLOURS:
            _mode = "colour"
            _hue = COLOURS[value]
            _power = True

    elif action == "brightness":
        # Brightness applies to whichever type of light is currently active.
        if _mode == "white":
            current = _white_brightness
        else:
            current = _colour_brightness

        if value == "increase":
            current += BRIGHTNESS_STEP

        elif value == "decrease":
            current -= BRIGHTNESS_STEP

        else:
            # low/high/percent values arrive from CommandEngine as numbers.
            current = int(value)

        current = max(0, min(100, current))

        if _mode == "white":
            _white_brightness = current
        else:
            _colour_brightness = current

    _send()