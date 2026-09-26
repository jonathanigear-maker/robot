void talkToRaspberryPI_old(){

if (Serial.available() >= 2) {
    uint8_t high_byte = Serial.read(); // Read the low byte
    uint8_t low_byte = Serial.read(); // Read the high byte
    uint16_t received_value = low_byte | (high_byte << 8);


  
    //uint16_t received_value;
    //Serial.readBytes((char *)&received_value, 2); // Read 2 bytes into the uint16_t variable
    // Process received value, e.g., print it



    if(received_value <180){
      //targetServo6 =  (int)(4.44*received_value + 100);
      //targetServo6  = constrain(targetServo6,50, 950);
      //int  duration = (int)abs(((160-xBlock)/3.2))*2
      //myArm.setPosition(6, targetServo6, 500, false);
      Serial.print("!Received values: ");
      Serial.println(received_value);
      if (received_value == 128){
        cute.play(S_HAPPY_SHORT);
        red = 255;
        blue = 0;
        green = 0;
        white = 0;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        neoEffect = 1; 
        neoEffects(); 
      }
      //Serial.print(", servo6 = ");
      //Serial.println(targetServo6);
      //delay(800);
    }
  }

}
