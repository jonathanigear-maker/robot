


void eyeMovement(){

  if (eyeOpen == true) {

   if (millis() - previousBlinkMillis >= blinkInterval) {
     previousBlinkMillis = millis();
     uint8_t doubleBlink = random(0,100);
      if  (doubleBlink < 20){      
            sendToLeftEye(4, eyeX, eyeY, 50);
            sendToRightEye(4, eyeX, eyeY, 50);
       delay(100);
            sendToLeftEye(4, eyeX, eyeY, 50);
            sendToRightEye(4, eyeX, eyeY, 50);
       delay(100);
       blinkInterval = random(1000,10000);
      }
     else{
            //bink animation
            sendToLeftEye(4, eyeX, eyeY, 50);
            sendToRightEye(4, eyeX, eyeY, 50);
            delay(150);
            blinkInterval = random(1000,10000);
    }
  }



    switch(eyeMode){
     case 1: //RandomMovement
     randomEyeMovement();
     break;

     case 2: //Followface
     trackingEyeMovement();
     //sendToLeftEye(1, eyeX, eyeY, eyeMovePeriod);
     //sendToRightEye(1, eyeX, eyeY, eyeMovePeriod);
     break; 
    }
  }
}


void randomEyeMovement() {
  unsigned long currentRandomEyeMillis = millis();
  uint32_t t = millis();
  int32_t dt = t - eyeTimeToNextMove; // mS elapsed since the last eye event

  if (currentRandomEyeMillis - previousRandomEyeMillis >= eyeMoveInterval) {
    previousRandomEyeMillis = currentRandomEyeMillis;
    eyeMoveInterval = random(1000,3000);
    eyeMovePeriod = random(0, 120); // scaler for how long it takes the eye to move.
    long dx, dy, d;
    do {
      eyeX =  random(-120, 120);
      eyeY = random(-120, 120);
    } 
    while (d = (eyeX * eyeX + eyeY * eyeY) > (lookingArea * lookingArea)); // Keep trying
   // Serial.print(eyeX);
   // Serial.print(" , ");
   // Serial.print(eyeY);
   // Serial.print(" , ");
   // Serial.print(eyeMovePeriod);
   // display_freeram();
    sendToLeftEye(1, eyeX, eyeY, eyeMovePeriod);
    sendToRightEye(1, eyeX, eyeY, eyeMovePeriod);
 }
}

void trackingEyeMovement() {
  unsigned long currentTrackingEyeMillis = millis();
  uint32_t t = millis();
  int32_t dt = t - eyeTimeToNextMove; // mS elapsed since the last eye event

  if (currentTrackingEyeMillis - previousTrackingEyeMillis >= eyeMoveInterval) {
    previousTrackingEyeMillis = currentTrackingEyeMillis;
    eyeMoveInterval = random(100,500);
    eyeMovePeriod = random(0, 120); // scaler for how long it takes the eye to move.
    sendToLeftEye(1, eyeX, eyeY, eyeMovePeriod);
    sendToRightEye(1, eyeX, eyeY, eyeMovePeriod);
 }
}

void sendToLeftEye(uint8_t command, int8_t x, int8_t y, int8_t t){
 Wire.beginTransmission(leftEye); // Replace with the actual slave address
 Wire.write(command); // Command
 Wire.write(x); // Send the x coordinate
 Wire.write(y); // Send the y coordinate
 Wire.write(t); // t
 int error = Wire.endTransmission(); // Send the data to the slave device with the specified address
 if (error > 1){ 
   playRandomSoundPattern();
   Serial.println(error); 
   Serial.println(millis());
   Wire.begin(); 
   Serial.print("I got a left eye error = ");
   Serial.println(error); 
   //Serial.println(error);
  }
}

void sendToRightEye(uint8_t command, int8_t x, int8_t y, int8_t t){
 Wire.beginTransmission(rightEye); // Replace with the actual slave address
 Wire.write(command); // Command
 Wire.write(x); // Send the x coordinate
 Wire.write(y); // Send the y coordinate
 Wire.write(t); // t
 int error = Wire.endTransmission(); // Send the data to the slave device with the specified address
 if (error >1 ){ 
   playRandomSoundPattern();
   Serial.println(error); 
   Serial.println(millis());
   Wire.begin(); 
   Serial.print("I got a right eye error = ");
   Serial.println(error); 
   //Serial.println(error);
  }
}
