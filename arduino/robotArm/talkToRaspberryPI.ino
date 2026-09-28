// ============================================================================
// RASPBERRY PI SERIAL COMMUNICATION
// ============================================================================
// Commands are plain ASCII terminated by newline.
//
// MOUTH 200
// LIGHT 30 180 100
// DIRECTION 135
// LASER 1
//
// LIGHT <hue> <colour brightness> <white brightness>
// Light values are 0-255.
// Hue 0-255 represents the full colour wheel.

void talkToRaspberryPI() {

  if (Serial.available() == 0) {
    return;
  }

  // Read one complete command and remove trailing spaces / CR
  String command = Serial.readStringUntil('\n');
  command.trim();

  if (command.length() == 0) {
    return;
  }

  // --------------------------------------------------------------------------
  // MOUTH <level>
  // --------------------------------------------------------------------------
  if (command.startsWith("MOUTH ")) {
    int value = command.substring(6).toInt();
    value = constrain(value, 0, 65535);

    mouthEffects(value);

    return;
  }

  // --------------------------------------------------------------------------
  // LIGHT <hue> <colour brightness> <white brightness>
  // --------------------------------------------------------------------------
  if (command.startsWith("LIGHTS ")) {
    int hue;
    int colourBrightness;
    int whiteBrightness;

    int result = sscanf(
      command.c_str(),
      "LIGHTS %d %d %d",
      &hue,
      &colourBrightness,
      &whiteBrightness
    );

    if (result != 3) {
      Serial.println("ERROR: LIGHTS requires 3 values");
      return;
    }

    hue = constrain(hue, 0, 255);
    colourBrightness = constrain(colourBrightness, 0, 255);
    whiteBrightness = constrain(whiteBrightness, 0, 255);

    // Convert 0-255 hue to 0-360 degrees
    float hueDegrees = ((float)hue / 255.0) * 360.0;

    // Convert hue to RGB
    HSVtoRGB(
      hueDegrees,
      100.0,
      100.0,
      red,
      green,
      blue
    );

    // Apply colour brightness
    red   = ((uint16_t)red   * colourBrightness) / 255;
    green = ((uint16_t)green * colourBrightness) / 255;
    blue  = ((uint16_t)blue  * colourBrightness) / 255;
    white = whiteBrightness;

    // Set RGBW colour and turn solid light effect on
    neoColor = strip.Color(red, green, blue, white);
    neoEffect = 1;

    Serial.print("LIGHTS hue=");
    Serial.print(hue);
    Serial.print(" colour=");
    Serial.print(colourBrightness);
    Serial.print(" white=");
    Serial.println(whiteBrightness);
    return;
  }

  // --------------------------------------------------------------------------
  // DIRECTION <angle>
  // --------------------------------------------------------------------------
  if (command.startsWith("DIRECTION ")) {
    int value = command.substring(10).toInt();

    Serial.print("DIRECTION ");
    Serial.println(value);

    myArm.setPosition(6, value, 500, false);
    return;
  }

  // --------------------------------------------------------------------------
  // LASER <0/1>
  // Currently only reports command, matching old behaviour.
  // --------------------------------------------------------------------------
  if (command.startsWith("LASER ")) {
    int value = command.substring(6).toInt();

    Serial.print("LASER ");
    Serial.println(value);
    return;
  }

  // Unknown command
  Serial.print("ERROR: Unknown command: ");
  Serial.println(command);
}
