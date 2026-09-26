void queryTouch(){


        if(digitalRead(rightEyeTouchPin) == LOW) {
        if ((millis() - lastDebounceTime) > debounceDelay) {
          Serial.println("touched");
          lastDebounceTime = millis();
          if (queryShutDown == true){
             Serial.println("shutdown");
             queryShutDown == false;
          }
          else {
          if (eyeOpen == true){
              //close eye animation
              sendToLeftEye(2, 0, 0, 100);
              sendToRightEye(2, 0, 0, 100);
              Serial.println("closing eyes");
              lastVoiceCommand = millis()-wakeTime*1000;
              eyeOpen=false;
              delay(2000);
              
              return;
          }
          if (eyeOpen == false){  
              //open eye antimation           
              sendToLeftEye(3, 0, 0, 100);
              sendToRightEye(3, 0, 0, 100);
              lastVoiceCommand = millis() ;
              myArm.setPosition(lookfront, 6, 1000, false);
              eyeOpen=true;
              Serial.println("opening eyes");
              DF2301Q.playByCMDID(1);
              delay(1000);
              return;
          }
        }
        }
    }

}
