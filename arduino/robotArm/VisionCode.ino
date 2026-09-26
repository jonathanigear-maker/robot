
bool isPointInsideSquare(int x, int y) {
    int squareCenterX = 160;
    int squareCenterY = 120;
    int squareSize = 150;

    int minX = squareCenterX - squareSize / 2;
    int maxX = squareCenterX + squareSize / 2;
    int minY = squareCenterY - squareSize / 2;
    int maxY = squareCenterY + squareSize / 2;

    return (x >= minX && x <= maxX && y >= minY && y <= maxY);
}


void checkForFace() {
  if (!huskylens.request()) Serial.println(F("  Fail to request data from HUSKYLENS!"));
  else if(!huskylens.isLearned()) Serial.println(F("  Nothing learned!"));
  else if(!huskylens.available()) {//Serial.println(F("   No block or arrow appears on the screen!"));
     if (trigger = true){nothingInterestingTimer = millis();}
  eyeMode = 1;//random eye movements
  trigger = false;
  }
  else  {
   while (huskylens.available()) {
      HUSKYLENSResult result = huskylens.read();
      printResult(result);
    }    
  }
}



void printResult(HUSKYLENSResult result){
 
    if (result.command == COMMAND_RETURN_BLOCK){
            trigger = true;
            faceLastSeenTimer = millis();
        //Serial.println(String()+F("  x =")+result.xCenter+F(",y =")+result.yCenter+F(",ID=")+result.ID);
        
        xBlock = result.xCenter;
        yBlock = result.yCenter;
        //Serial.println(String()+F("  x =")+result.xCenter+F(",width =")+result.width+F(",ID=")+result.ID);
        lastVoiceCommand = millis();
        //DF2301Q.playByCMDID(1);

        if (isPointInsideSquare(result.xCenter, result.yCenter)) { 
        eyeMode = 2; //eyes in tracking mode
        eyeY = (int)(result.xCenter-160)/0.75;
        eyeX = (int)(result.yCenter-120)/0.75;
        //Serial.println(String()+F("  x =")+eyeY+F(",width =")+result.width+F(",ID=")+result.ID);
        if (faceRecognition == true){faceTrack();}
        if (tagRecognition == true){myArm.setPosition(situp, 4, 1000, false);}
        if (objectRecognition == true){
          Serial.println("I thugh i saw a puddy cat   ");
          Serial.print("CMDID = ");
          Serial.println(CMDID);}
        }
        else{
        eyeMode = 1; // random eye movements
        if (faceRecognition == true){faceTrack();}
        if (tagRecognition == true){myArm.setPosition(situp, 4, 1000, false);}
        if (objectRecognition == true){Serial.println("I thugh i saw a puddy cat also");}
        }
    }
    else if (result.command == COMMAND_RETURN_ARROW){
        Serial.println(String()+F("Arrow:xOrigin=")+result.xOrigin+F(",yOrigin=")+result.yOrigin+F(",xTarget=")+result.xTarget+F(",yTarget=")+result.yTarget+F(",ID=")+result.ID);
    }
    else{
        Serial.println("Object unknown!");
    }
}
