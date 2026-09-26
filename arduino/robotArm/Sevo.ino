void servoMovement()
{
 headTilt();
 laserMode();
}


void headTilt()
{
 if (eyeOpen == true){
   if (faceRecognition == true){
     if (millis() - previousTiltMillis >= tiltInterval) {
       previousTiltMillis = millis();
       tiltInterval = random(1000,5000);
       tiltAngle = random(450,550);
       myArm.setPosition(2,tiltAngle, 100, false);
       if (trigger == false){
         servo6 = myArm.getPosition(6);
         Serial.print("servo6 = ");
         Serial.println(servo6);
         int movement = random(-200,200);
         targetServo6 =  (int)(servo6 + movement);
         //Serial.println(targetServo6);
         targetServo6  = constrain(targetServo6,50, 950);
         int speed = abs(movement)*5;
         myArm.setPosition(6, targetServo6, speed, false);
         servo3 = myArm.getPosition(3);
         int movementServo3 = random(100,400);
         targetServo3 =  (int)(movementServo3);
         Serial.print("servo3 = ");
         Serial.println(servo3);
         targetServo3  = constrain(targetServo3,100, 400);
         //int speed = abs(movement)*5;
         myArm.setPosition(3, targetServo3, 500, false);
       }
     }  
   }
 }
 else {myArm.setPosition(2,500, 100, false);}
}

void faceTrack(){
  servo6 = myArm.getPosition(6);
  servo3 = myArm.getPosition(3);

  //Serial.print("tracking face      = ");
  
 if (servo6 >0 && servo3 >0){
     //Serial.print("Servo positions      = ");
     //Serial.print(servo6);
     //Serial.print(" , ");
     //Serial.println(servo3);
   targetServo6 =  (int)(servo6 + (160-xBlock));
   targetServo6  = constrain(targetServo6,50, 950);
   targetServo3 =  (int)(servo3 + (120-yBlock));
   targetServo3  = constrain(targetServo3,50, 950);
  
   int  duration = (int)abs(((160-xBlock)/3.2))*2;

   //Serial.print("Servo target positions = ");
   //Serial.print(targetServo6);
   //Serial.print(" , ");
   //Serial.print(targetServo3);
   //Serial.print(" , ");
   //Serial.println(duration);

  myArm.setPosition(6, targetServo6, 200, false);
  myArm.setPosition(3, targetServo3, 200, false);
  } 
}

void lampMode(){
xArmServo lamp [] = {{2, 500}, //this is the head rotation servo
                     {3, 50},
                     {4, 500},
                     {5, 450}};//this is 25 kg  servo
myArm.setPosition(lamp, 4, 1000, false);

}

void laserMode(){
   if (laserBool == true){

    if (millis() - previousTiltMillis >= tiltInterval) {
    previousTiltMillis = millis();
    tiltInterval = random(1000,5000);
      
     servo6 = myArm.getPosition(6);
     int movement = random(50,950);
     //targetServo6 =  (int)(servo6 + movement);
     //Serial.println(targetServo6);
     targetServo6  = constrain(movement,50, 950);
    //int speed = abs(movement)*5;
     myArm.setPosition(6, targetServo6, 2000, false);

     servo3 = myArm.getPosition(3);
     int movementServo3 = random(50,200);
     targetServo3 =  (int)(movementServo3);
     Serial.print("Servo 3  position = ");
     Serial.println(servo3);
     targetServo3  = constrain(targetServo3,100, 400);
     //int speed = abs(movement)*5;
     myArm.setPosition(3, targetServo3, 500, false);

    }
   }  
    

}
