
void buttonPress(){

 uint8_t buttons = neokey.read();
  for (int i=0; i< neokey.pixels.numPixels(); i++) {
      neokey.pixels.setPixelColor(i, 0x00FF00);
  }  

  
  if (buttons & (1<<0)) { 
    if (buttonAPressActive == false){
        buttonAStartTime = millis();
        buttonAPressActive = true;
    }
    else {
        unsigned long buttonADuration = millis() - buttonAStartTime; 
        if (millis() - buttonAStartTime >3000){
           buttonALongHold();
           //call_buttonA long press function
        }
    }   
  } else {
        neokey.pixels.setPixelColor(0, 0xFF0000);
        if (buttonAPressActive == true){
           buttonAPressActive =  false;
           unsigned long buttonADuration = millis() - buttonAStartTime;
           if (buttonADuration < 500) {buttonAShortPress();}
           else if (buttonADuration < 3000) {buttonAMediumPress();}
           else {buttonALongRelease();}     
        }
  }

  if (buttons & (1<<1)) { 
    if (buttonBPressActive == false){
        buttonBStartTime = millis();
        buttonBPressActive = true;
    }
    else {
        unsigned long buttonBDuration = millis() - buttonBStartTime; 
        if (millis() - buttonBStartTime >3000){
           buttonBLongHold();
        }
    }   
  } else {
        neokey.pixels.setPixelColor(1, 0xFFFF00);
        if (buttonBPressActive == true){
           buttonBPressActive =  false;
           unsigned long buttonBDuration = millis() - buttonBStartTime;
           if (buttonBDuration < 500) {buttonBShortPress();}
           else if (buttonBDuration < 3000) {buttonBMediumPress();}
           else {buttonBLongRelease();}     
        }
  }


  if (buttons & (1<<2)) { 
    if (buttonCPressActive == false){
        buttonCStartTime = millis();
        buttonCPressActive = true;
    }
    else {
        unsigned long buttonCDuration = millis() - buttonCStartTime; 
        if (millis() - buttonCStartTime >3000){
           buttonCLongHold();
        }
    }   
  } else {
        neokey.pixels.setPixelColor(2, 0x0000FF);
        if (buttonCPressActive == true){
           buttonCPressActive =  false;
           unsigned long buttonCDuration = millis() - buttonCStartTime;
           if (buttonCDuration < 500) {buttonCShortPress();}
           else if (buttonCDuration < 3000) {buttonCMediumPress();}
           else {buttonCLongRelease();}     
        }
  }


  if (buttons & (1<<3)) { 
    if (buttonDPressActive == false){
        buttonDStartTime = millis();
        buttonDPressActive = true;
    }
    else {
        unsigned long buttonDDuration = millis() - buttonDStartTime; 
        if (millis() - buttonDStartTime >3000){
           buttonDLongHold();
        }
    }   
  } else {
        neokey.pixels.setPixelColor(3, 0x8A2BE2);
        if (buttonDPressActive == true){
           buttonDPressActive =  false;
           unsigned long buttonDDuration = millis() - buttonDStartTime;
           if (buttonDDuration < 500) {buttonDShortPress();}
           else if (buttonDDuration < 3000) {buttonDMediumPress();}
           else {buttonDLongRelease();}     
        }
  }
neokey.pixels.show();
} 


void buttonAShortPress(){
     Serial.println("Button A: Short Press");
     if (lightIsOn == false){
        neoEffect = 1;
        }
     else if (lightIsOn == true){
        neoEffect = 2;
        }
}

 
void buttonAMediumPress(){
     Serial.println("Button A: Medium Press");
     if (lightIsWhite == false){
        red = 0;
        green = 0;
        blue = 0;
        white = 255;
        lightIsWhite = true;
        neoEffect = 1;
        }
     else if (lightIsWhite == true){
        float h = ((float)(countB % 24) * 360.0f) / 24.0f;
        HSVtoRGB(h, 100.0f, 100.0f, red, green, blue);
        white = 0;
        lightIsWhite = false;
        neoEffect = 1;
        }
neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
} 


void buttonALongHold(){
     Serial.println("Button A: Long Hold");
     piShutDownSequence();
} 


void buttonALongRelease(){
     Serial.println("Button A: Long Press");
}


void buttonBShortPress(){
     //Serial.println("Button B: Short Press");
     if (AIBool == false){
        Serial.println("openAI");
        AIBool = true;
        }
     else if (AIBool == true){
        Serial.println("closeAI");
        AIBool = false;
        }
}

 
void buttonBMediumPress(){
     Serial.println("Button B: Medium Press");
} 


void buttonBLongHold(){
     Serial.println("Button B: Long Hold");
} 


void buttonBLongRelease(){
     Serial.println("Button B: Long Release");
}

void buttonCShortPress(){
     //Serial.println("Button C: Short Press");
     Serial.println("closeAI");
}

 
void buttonCMediumPress(){
     Serial.println("Button C: Medium Press");
} 


void buttonCLongHold(){
     Serial.println("Button C: Long Hold");
} 

void buttonCLongRelease(){
     Serial.println("Button C: Long Release");
}

void buttonDShortPress(){
     Serial.println("Button D: Short Press");
}

void buttonDMediumPress(){
     Serial.println("Button D: Medium Press");
} 


void buttonDLongHold(){
     Serial.println("Button D: Long Hold");
} 

void buttonDLongRelease(){
     Serial.println("Button D: Long Release");
}
