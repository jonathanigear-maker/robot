void nothingInteresting(){

if (millis() - lastVoiceCommand > wakeTime*1000){
 // DF2301Q.playByCMDID(1);
    //sendToLeftEye(2, 120, 120, 100);
    //sendToRightEye(2, 120, 120, 100);
if (lampBool == false && laserBool == false && eyeOpen == true){
          xArmServo sleep[] = {{1, 600}, //this is the claw servo
                     {2, 500},
                     {3, 100},
                     {4, 900},
                     {5, 950},
                     {6, 500}};//this is the rotation servo
                     myArm.setPosition(sleep, 6, 1000, false);
    sendToLeftEye(2, 120, 120, 100);
    sendToRightEye(2, 120, 120, 100);
    eyeOpen = false;
    Serial.println("closing eyes cos of timer");
    Serial.println("sleepingnow");
 
 }
}
}