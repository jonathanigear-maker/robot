


void encoder(){

#ifdef ENCA_OK


  if(encA.available()){countA = encA.read();
  //Serial.println(countA);
  }
  if(countA != lastCountA){
      Serial.print("countA = ");
      Serial.println(countA);
      pressed = false;
      int positionChange = countA - lastCountA;
      int direction = positionChange > 0 ? 1 : -1;
      brightnessTest += direction * (255 / 24);
      Serial.print("brightnessTest = ");
      Serial.println(brightnessTest);
      brightness = brightnessTest;
  
      if (lightIsWhite == true){
          red = 0;
          green = 0;
          blue = 0;
          white = 255;
          //neoEffect = 1;
          neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
      }
      else {red = 0;
          green = 0;
          blue = 0;
          white = 0;
          //neoEffect = 1;
          neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
      }
      lastCountA = countA;
   }

 #endif

 #ifdef ENCB_OK
     //encB is for colour and is on the left
  if(encB.available()){countB = encB.read();}
  if(countB != lastCountB){
      lastCountB = countB;
      int valueB = countB;
      Serial.print("countB = ");
      Serial.println(countB);
      pressed = false;
      while(countB < 0)
      valueB += 24;
      float h = ((float)(valueB % 24) * 360.0f) / 24.0f;
      byte r, g, b;
      HSVtoRGB(h, 100.0f, 100.0f, red, green, blue);
      encB.setRGB(red, green, blue);
      encA.setRGB(red, green, blue);
      if (lightIsWhite == true){
         red = 0;
         green = 0;
         blue = 0;
         white = 255;
         //neoEffect = 1;
      }
      else {white = 0;
         neoColor =  strip.Color(red*brightness/255,green*brightness/255,blue*brightness/255,white*brightness/255);
         //neoEffect = 1;
      }
      
  }

#endif

}

void queryButton() {
  // This function will be called when the interrupt occurs
  if (digitalRead(INTERRUPT_PIN)== LOW){
  pressed = true;
 }
}
