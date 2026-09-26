#define SOM 0xA1  // Start of message byte
#define EOM 0x55 // End of message byte

void talkToRaspberryPI() {
  if (Serial.available() >= 5) { // Minimum bytes required (SOM, Command, High byte, Low byte, EOM)
    uint8_t start_byte = Serial.read(); // Read the start of message byte
    
    // Check if the start byte is correct
    if (start_byte == SOM) {
      uint8_t command_byte = Serial.read(); // Read the command byte
      uint8_t high_byte = Serial.read(); // Read the high byte
      uint8_t low_byte = Serial.read(); // Read the low byte
      uint8_t end_byte = Serial.read(); // Read the end of message byte
      
      // Check if the end byte is correct
      if (end_byte == EOM) {
        uint16_t received_value = low_byte | (high_byte << 8);

        // Process the received value based on the command byte
        switch (command_byte) {
          case 0xB0:
            Serial.print(received_value);
            Serial.println("   = DIRECTION");
            myArm.setPosition(6, received_value, 500, false);
            // Perform action for command byte 0xB0
            break;

          case 0xB1:
            Serial.print(received_value);
            Serial.println("   = LASER ON!!");
            // Perform action for command byte 0xB1
            break;

          case 0xA5:
            mouthEffects(received_value);
            // Perform action for command byte 0xA5
            break;

            case 0xA6:
            Serial.print(high_byte);
            Serial.println("   = BRIGHTNESS");
            Serial.print(low_byte);
            Serial.println("   = HUE");
            // Perform action for command byte 0xA5
            break;

          default:
            Serial.println("Command byte is not recognized. Ignoring...");
            // Perform action for unrecognized command byte
            break;
        }
      } else {
        // If the end byte is incorrect, print an error
        Serial.println("Error: End of message byte incorrect. Message discarded.");
      }
    } else {
      // If the start byte is incorrect, print an error
      Serial.println("Error: Start of message byte incorrect. Message discarded.");
    }
  }
}
