void checkForSound(){
  
    CMDID = 0;
    if (AIBool == false){
    CMDID = DF2301Q.getCMDID();
    // Serial.print("CMDID = ");
    // Serial.print(CMDID);
    }
switch(CMDID) {
    case 1: //Hey Robot
    digitalWrite(LED_BUILTIN, HIGH);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_CONNECTION);
        myArm.setPosition(lookfront, 6, 1000, false);
        lastVoiceCommand = millis();
              if (eyeOpen == false){
              eyeOpen=true;
              sendToLeftEye(3, 0, 0, 100);
              sendToRightEye(3, 0, 0, 100);
              }
    break;

    case 2: //Hello Robot
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_CONNECTION);
        myArm.setPosition(lookfront, 6, 1000, false);
        lastVoiceCommand = millis();
              if (eyeOpen == false){
              eyeOpen=true;             
              sendToLeftEye(3, 0, 0, 100);
              sendToRightEye(3, 0, 0, 100);
              }
        myArm.setPosition(1,600, 100, false);
    break;

            case 5:  //open beak
        digitalWrite(LED_BUILTIN, LOW);

        Serial.print("CMDID = ");
        Serial.println(CMDID);
        myArm.setPosition(1, 200, 100, false);
        //cute.play(S_HAPPY_SHORT);
    break;

        case 6:  //close beak
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        myArm.setPosition(1, 900, 100, false);
        cute.play(S_HAPPY_SHORT);
    break;

        case 7:  //laser on
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        huskylens.writeAlgorithm(ALGORITHM_OBJECT_RECOGNITION);
        myArm.setPosition(lookfront, 6, 1000, false);
        laserBool = true;
        lampBool = false;
        faceRecognition = false;
        tagRecognition = false;
        objectRecognition = true;
           sendToLeftEye(5, eyeX, eyeY, eyeMovePeriod);
           sendToRightEye(5, eyeX, eyeY, eyeMovePeriod);
        cute.play(S_HAPPY_SHORT);
    break;

            case 8:  //laser off
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        huskylens.writeAlgorithm(ALGORITHM_FACE_RECOGNITION);
        laserBool = false;
        lampBool = false;
        faceRecognition = true;
        tagRecognition = false;
        objectRecognition = false;
           sendToLeftEye(6, eyeX, eyeY, eyeMovePeriod);
           sendToRightEye(6, eyeX, eyeY, eyeMovePeriod);
        cute.play(S_HAPPY_SHORT);
    break;


    case 9:  //go to sleep
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        lampBool = false;
        strip.clear();
        strip.show();
        cute.play(S_FART3);
        lastVoiceCommand =  millis() + wakeTime*1000;
        nothingInteresting();
    break;

     case 10:  //lamp mode
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        tagRecognition = true;
        faceRecognition = false;
        lampBool = true;
        huskylens.writeAlgorithm(ALGORITHM_TAG_RECOGNITION);
        lampMode();
    break;

        case 22:  //go forward
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        servo6 = myArm.getPosition(6);
        targetServo6 =  (int)(servo6 + (20));
        targetServo6  = constrain(targetServo6,50, 950);
        myArm.setPosition(6, targetServo6, 200, false);
        cute.play(S_HAPPY_SHORT);
    break;


        case 25:  //Turn left ninety degrees
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        myArm.setPosition(lookleft, 6, 1000, false);
        cute.play(S_HAPPY_SHORT);
    break;

        case 26:  //Turn left forty-five degrees
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
    break;

        case 27:  //Turn left thirty degrees
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
    break;

        case 28:  //Turn right ninety degrees
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        myArm.setPosition(lookright, 6, 1000, false);
        cute.play(S_HAPPY_SHORT);
    break;

        case 29:  //Turn right forty-five degrees
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
    break;

        case 30:  //Turn right thirty degrees
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
    break;

        case 36:  //face recognition
        faceRecognition = true;
        tagRecognition = false;
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        huskylens.writeAlgorithm(ALGORITHM_FACE_RECOGNITION);
        cute.play(S_HAPPY_SHORT);
    break;

        case 37:  //Object Tracking
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
    break;

        case 38:  //Object Recognition
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
    break;

    case 40:  //Color recognition
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
    break;

    case 41:  //Tag Recognition
    digitalWrite(LED_BUILTIN, LOW);
        faceRecognition = false;
        tagRecognition = true;
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        huskylens.writeAlgorithm(ALGORITHM_TAG_RECOGNITION);
        cute.play(S_HAPPY_SHORT);
    break;

           case 92:  //Play music
    digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        //song();
    break;

    case 103:  //Turn on the light
        digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        //cute.play(S_HAPPY_SHORT);
        playRandomSoundPattern(); 
        strip.fill(neoColor);
        colorMode = 0;
        neoEffect = 0;
        strip.show(); 
        break;


    case 104:  //Turn off the light
      digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_SUPER_HAPPY);
        colorMode = 0;
        strip.clear();
        neoEffect = 2;
        strip.show();
    break;

    case 105:  //Brighten the light
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        if (brightness + 20 <= 255) {
        brightness += 20;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);        
          } else {
              brightness = 255;
                 neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
              strip.fill(neoColor);
              } 
        strip.show(); 
    break;

    case 106:  //Dim the light
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        if (brightness - 20 >= 20) {
        brightness -= 20;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
          } else {
            brightness = 20;
            neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
            strip.fill(neoColor);
              } 
        strip.show(); 
    break;

    case 107:  //adjust brightness to maximum
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        brightness = 255;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        strip.show(); 
    break;

    case 108:  //adjust brightness to minimum
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        brightness = 10;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        strip.show(); 
    break;   

        case 115:  //color mode
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        colorMode = random(1,2);
        
    break;

        case 116:  //Set to Red
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        red = 255;
        blue = 0;
        green = 0;
        white = 0;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        neoEffect = 1; 
        neoEffects();
        
    break;

        case 117:  //Set to Orange
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        red = 255;
        blue = 0;
        green = 50;
        white = 0;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        colorMode = 0;
        strip.show();
        neoEffect = 3; 
        neoEffects();
        
    break;

        case 118:  //Set to yellow
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        red = 255;
        blue = 0;
        green = 115;
        white = 0;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        colorMode = 0;
        strip.show(); 
    break;

      case 119:  //Set to Green
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        red = 0;
        blue = 0;
        green = 255;
        white = 0;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        colorMode = 0;
        strip.show(); 
    break;

        case 120:  //Set to Cyan
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        red = 0;
        blue = 255;
        green = 255;
        white = 0;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        colorMode = 0;
        strip.show(); 
    break;

      case 121:  //Set to Blue
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        red = 0;
        blue = 255;
        green = 0;
        white = 0;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        colorMode = 0;
        strip.show(); 
    break;

        case 122:  //Set to Purple
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);
        red = 188;
        blue = 188;
        green = 0;
        white = 0;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        colorMode = 0;
        strip.show(); 
    break;

          case 123:  //Set to White
        //digitalWrite(LED_BUILTIN, LOW);
        Serial.print("CMDID = ");
        Serial.println(CMDID);
        cute.play(S_HAPPY_SHORT);

        red = 0;
        blue = 0;
        green = 0;
        white = 255;
        neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
        strip.fill(neoColor);
        colorMode = 0;
        strip.show(); 
    break;

    default:

     if(0 != CMDID) {
     Serial.print("CMDID = ");
     Serial.println(CMDID);
     //cute.play(S_OHOOH);
    }
  }
  //noTone(speakerPin);   
}
